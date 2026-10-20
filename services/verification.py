"""
CareerKit AI - Claim Verification & Factuality Audit Service
Extracts factual assertions (degrees, skills, dates, metrics, projects)
from generated documents and cross-references them against candidate ground-truth.
Categorizes claims into 4 strict factuality states and recommends actions.
"""

import re
from typing import List, Dict, Any, Optional
from services.database import save_verification_record, get_db


STATUS_SUPPORTED = "Supported by supplied info"
STATUS_NEEDS_CONFIRM = "Needs candidate confirmation"
STATUS_UNSUPPORTED = "Unsupported"
STATUS_CONTRADICTION = "Contradiction detected"


def verify_claims_in_text(candidate: Dict[str, Any], document_text: str, document_type: str = "resume") -> List[Dict[str, Any]]:
    """
    Identifies factual claims in document text and evaluates them against candidate ground-truth.
    
    Returns:
        List of claim audit dictionaries.
    """
    if not document_text or not candidate:
        return []

    claims = []
    lower_doc = document_text.lower()

    # Pre-parse candidate ground-truth facts
    gt_education = (candidate.get("education") or "").lower()
    gt_grad_year = str(candidate.get("graduation_year") or "").strip()
    gt_skills = set(
        s.strip().lower()
        for s in (candidate.get("skills") or "").split(",")
        if s.strip()
    )
    gt_projects = (candidate.get("projects") or "").lower()
    gt_experience = (candidate.get("experience") or "").lower()

    # --------------------------------------------------------------------------
    # 1. Degree & Qualification Audit
    # --------------------------------------------------------------------------
    degree_patterns = [
        (r"\b(?:b\.?tech|bachelor of technology|b\.?e\.?|bachelor of engineering)\b", "B.Tech / B.E."),
        (r"\b(?:b\.?s\.?|b\.?sc\.?|bachelor of science)\b", "B.S. / B.Sc."),
        (r"\b(?:m\.?tech|master of technology|m\.?s\.?|m\.?sc\.?|master of science)\b", "M.Tech / M.S."),
        (r"\b(?:ph\.?d\.?|doctor of philosophy|doctorate)\b", "Ph.D. / Doctorate"),
        (r"\b(?:m\.?b\.?a\.?|master of business administration)\b", "M.B.A.")
    ]

    for pat, label in degree_patterns:
        match = re.search(pat, lower_doc)
        if match:
            matched_claim = match.group(0).strip()
            # Check if candidate ground truth has this degree level
            if re.search(pat, gt_education):
                claims.append({
                    "claim_text": f"Educational Degree: {label}",
                    "document_type": document_type,
                    "status": STATUS_SUPPORTED,
                    "reason": f"Matches candidate ground-truth education '{candidate.get('education')}'.",
                    "supporting_info": candidate.get("education"),
                    "suggested_action": "No action needed (Verified from candidate profile)."
                })
            else:
                # Degree mentioned in document that differs from ground-truth degree
                claims.append({
                    "claim_text": f"Educational Degree: {label} ('{matched_claim}')",
                    "document_type": document_type,
                    "status": STATUS_CONTRADICTION,
                    "reason": f"Document claims {label}, but candidate ground-truth record lists '{candidate.get('education')}'.",
                    "supporting_info": f"Candidate ground truth: {candidate.get('education')}",
                    "suggested_action": f"Edit to match verified degree '{candidate.get('education')}' or update candidate profile."
                })

    # --------------------------------------------------------------------------
    # 2. Graduation Year & Dates Audit
    # --------------------------------------------------------------------------
    if gt_grad_year:
        year_matches = set(re.findall(r"\b(20[1-3][0-9])\b", document_text))
        for y in year_matches:
            if y == gt_grad_year:
                claims.append({
                    "claim_text": f"Graduation Year: {y}",
                    "document_type": document_type,
                    "status": STATUS_SUPPORTED,
                    "reason": "Graduation year aligns with candidate profile.",
                    "supporting_info": f"Expected graduation: {gt_grad_year}",
                    "suggested_action": "No action needed."
                })
            elif abs(int(y) - int(gt_grad_year)) > 3:
                # Unrelated historical year or potential date mismatch
                pass

    # --------------------------------------------------------------------------
    # 3. Numerical Metrics & Quantified Achievements Audit
    # --------------------------------------------------------------------------
    # Look for patterns like "25%", "40% reduction", "$10,000", "500+ users"
    metric_matches = re.finditer(
        r"(\b\d{1,3}%[^\.\n]*|\$\d+[\d,]*[^\.\n]*|\b\d+\+?\s*(?:users|clients|students|requests|queries|tests|endpoints|records)[^\.\n]*)",
        document_text,
        re.IGNORECASE
    )

    found_metrics = set()
    for m in metric_matches:
        raw_metric = m.group(1).strip()
        if raw_metric in found_metrics:
            continue
        found_metrics.add(raw_metric)

        # Check if this metric or number appears in candidate projects or experience
        number_in_metric = re.search(r"\d+", raw_metric)
        num_str = number_in_metric.group(0) if number_in_metric else ""

        if num_str and (num_str in gt_projects or num_str in gt_experience):
            claims.append({
                "claim_text": f"Quantitative Metric: '{raw_metric}'",
                "document_type": document_type,
                "status": STATUS_SUPPORTED,
                "reason": f"Metric value ({num_str}) found in candidate ground-truth projects or experience.",
                "supporting_info": "Present in candidate profile description.",
                "suggested_action": "Verified from profile."
            })
        else:
            claims.append({
                "claim_text": f"Quantitative Metric: '{raw_metric}'",
                "document_type": document_type,
                "status": STATUS_NEEDS_CONFIRM,
                "reason": "This specific performance metric was not found in the candidate's ground-truth facts.",
                "supporting_info": "Candidate profile contains no corresponding numerical measurement.",
                "suggested_action": "Confirm this measurement is factually accurate and documented before submitting."
            })

    # --------------------------------------------------------------------------
    # 4. Technical Skills & Tools Audit
    # --------------------------------------------------------------------------
    # Sample list of standard technical tools commonly scanned in resumes
    common_tech_tools = [
        "python", "flask", "django", "fastapi", "javascript", "typescript", "react",
        "angular", "vue", "node.js", "express", "sql", "sqlite", "postgresql", "mysql",
        "mongodb", "redis", "docker", "kubernetes", "git", "github", "linux", "bash",
        "aws", "gcp", "azure", "pytest", "c++", "java", "c#", "rust", "go", "html5", "css3"
    ]

    for tool in common_tech_tools:
        # Match tool as standalone word
        if re.search(rf"\b{re.escape(tool)}\b", lower_doc):
            # Check if candidate explicitly lists this skill
            matched_gt = any(tool in s or s in tool for s in gt_skills)
            if matched_gt:
                claims.append({
                    "claim_text": f"Technical Skill: {tool.capitalize()}",
                    "document_type": document_type,
                    "status": STATUS_SUPPORTED,
                    "reason": f"Skill '{tool}' is explicitly declared in candidate ground-truth profile.",
                    "supporting_info": candidate.get("skills"),
                    "suggested_action": "Verified."
                })
            else:
                # Skill present in document, but missing from candidate skills
                # Check if it was mentioned in projects or experience
                in_exp = tool in gt_experience or tool in gt_projects
                if in_exp:
                    claims.append({
                        "claim_text": f"Technical Skill: {tool.capitalize()}",
                        "document_type": document_type,
                        "status": STATUS_NEEDS_CONFIRM,
                        "reason": f"Skill '{tool}' was referenced in project/experience notes, but is missing from core skills list.",
                        "supporting_info": "Mentioned in project/experience text.",
                        "suggested_action": "Add to verified profile skills or confirm competence."
                    })
                else:
                    claims.append({
                        "claim_text": f"Technical Skill: {tool.capitalize()}",
                        "document_type": document_type,
                        "status": STATUS_UNSUPPORTED,
                        "reason": f"Document claims '{tool.capitalize()}', but candidate has not listed this skill anywhere in their profile.",
                        "supporting_info": f"Candidate skills: {candidate.get('skills')}",
                        "suggested_action": f"Remove '{tool.capitalize()}' or confirm candidate has genuine knowledge before asserting."
                    })

    # Deduplicate claims by claim_text
    unique_claims = []
    seen_texts = set()
    for c in claims:
        if c["claim_text"] not in seen_texts:
            seen_texts.add(c["claim_text"])
            unique_claims.append(c)

    return unique_claims


def audit_and_save_document_claims(
    candidate: Dict[str, Any],
    document_text: str,
    document_type: str = "resume",
    db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Audits document text, categorizes all claims, and persists them into SQLite.
    """
    candidate_id = candidate.get("id")
    claims = verify_claims_in_text(candidate, document_text, document_type)

    saved_claims = []
    for c in claims:
        c_data = {
            "candidate_id": candidate_id,
            "document_type": document_type,
            "claim_text": c["claim_text"],
            "status": c["status"],
            "reason": c["reason"],
            "supporting_info": c.get("supporting_info"),
            "suggested_action": c.get("suggested_action", "Confirm statement"),
            "candidate_resolution": "pending"
        }
        claim_id = save_verification_record(c_data, db_path)
        c_data["id"] = claim_id
        saved_claims.append(c_data)

    return saved_claims
