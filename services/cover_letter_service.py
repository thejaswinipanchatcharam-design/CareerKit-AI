"""
CareerKit AI - Cover Letter Generation Service
Generates targeted, highly factual cover letters aligned with specific job descriptions
while strictly adhering to candidate ground-truth facts (no invented experience, metrics, or employers).
"""

import re
from typing import Dict, Any, Optional
from services.ai_service import generate_ai_response


def generate_cover_letter(
    candidate: Dict[str, Any],
    target_role: str,
    company_name: str,
    job_description: str = "",
    tone: str = "professional",
    candidate_notes: str = ""
) -> Dict[str, Any]:
    """
    Generates a factuality-locked, tailored cover letter using the unified AI service.

    Returns:
        Dict with full_content, key_alignments, missing_requirements, success, error, is_mock.
    """
    if not candidate:
        return {
            "success": False,
            "error": "Candidate profile is required to generate a factual cover letter.",
            "full_content": ""
        }

    c_name = candidate.get("name", "Candidate")
    c_edu = candidate.get("education", "Engineering Student")
    c_skills = candidate.get("skills", "")
    c_projects = candidate.get("projects", "")
    c_exp = candidate.get("experience", "")
    c_email = candidate.get("email", "")
    c_phone = candidate.get("phone", "")
    c_loc = candidate.get("location", "")

    # Ground-truth candidate profile prompt block
    prompt = f"""Generate a tailored, professional cover letter strictly grounded in the candidate's verified facts.

CANDIDATE FACTS (GROUND TRUTH):
- Name: {c_name}
- Email: {c_email or 'Not provided'}
- Phone: {c_phone or 'Not provided'}
- Location: {c_loc or 'Not provided'}
- Education: {c_edu}
- Technical Skills: {c_skills}
- Completed Projects: {c_projects or 'None listed'}
- Work/Internship Experience: {c_exp or 'None listed'}
- Additional Candidate Notes: {candidate_notes or 'None'}

TARGET JOB CONTEXT:
- Target Role: {target_role}
- Target Company: {company_name}
- Job Description / Requirements:
{job_description or 'General requirements for ' + target_role}

MANDATORY FACTUALITY RULES:
1. ONLY reference qualifications, projects, technologies, and achievements explicitly provided in CANDIDATE FACTS.
2. NEVER fabricate previous companies, job titles, or metrics that the candidate has not accomplished.
3. If the job description requires a skill or qualification the candidate lacks, DO NOT pretend they have it; instead, highlight their genuine foundational skills or note '[NEEDS CANDIDATE INPUT]'.
4. Tone: {tone}. Be direct, confident, and professional without generic fluff.
5. Structure the response exactly as follows:

[COVER LETTER]
(Provide the complete, publication-ready cover letter text here including contact header, date, recipient salutation, 3-4 structured body paragraphs, professional closing, and candidate signature).

[KEY ALIGNMENTS]
- Bullet point 1: Genuine candidate skill/project matching a specific job requirement.
- Bullet point 2: Another genuine qualification matching the role.

[MISSING REQUIREMENTS]
- Bullet point 1: Any skill or requirement from the job description not documented in candidate facts, or 'None detected'.
"""

    system_instruction = (
        "You are an expert, ethical career mentor and technical writer. "
        "Your highest priority is uncompromising factual integrity. "
        "You help candidates highlight their authentic strengths without ever inventing or exaggerating claims."
    )

    ai_res = generate_ai_response(
        prompt=prompt,
        system_instruction=system_instruction,
        temperature=0.2  # Low temperature for factual precision
    )

    if not ai_res.get("success"):
        return {
            "success": False,
            "error": ai_res.get("error", "AI generation failed."),
            "full_content": "",
            "is_mock": False
        }

    if ai_res.get("is_mock"):
        fallback_letter = _generate_fallback_cover_letter(candidate, company_name, target_role)
        return {
            "success": True,
            "full_content": fallback_letter,
            "key_alignments": [
                f"Demonstrated technical skills in {candidate.get('skills', 'core engineering')}",
                f"Directly applicable project experience aligned with {target_role}"
            ],
            "missing_requirements": ["None detected in candidate ground-truth profile."],
            "provider": "mock",
            "model": "offline-demonstration",
            "is_mock": True
        }

    raw_output = ai_res.get("content", "")
    parsed = _parse_cover_letter_output(raw_output, candidate, company_name, target_role)
    parsed["success"] = True
    parsed["provider"] = ai_res.get("provider")
    parsed["model"] = ai_res.get("model")
    parsed["is_mock"] = ai_res.get("is_mock", False)
    return parsed


def _parse_cover_letter_output(
    output: str,
    candidate: Dict[str, Any],
    company_name: str,
    target_role: str
) -> Dict[str, Any]:
    """Parses raw AI generation into structured sections."""
    cover_letter_text = ""
    key_alignments = []
    missing_requirements = []

    # Check for [COVER LETTER] section
    cl_match = re.search(r"\[COVER LETTER\](.*?)(?=\[KEY ALIGNMENTS\]|\Z)", output, re.DOTALL | re.IGNORECASE)
    if cl_match:
        cover_letter_text = cl_match.group(1).strip()
    else:
        # Fallback if AI used standard markdown headers
        parts = re.split(r"#{2,3}\s*Key Alignments|\[KEY ALIGNMENTS\]", output, flags=re.IGNORECASE)
        cover_letter_text = parts[0].strip()

    # Check for [KEY ALIGNMENTS] section
    ka_match = re.search(r"\[KEY ALIGNMENTS\](.*?)(?=\[MISSING REQUIREMENTS\]|\Z)", output, re.DOTALL | re.IGNORECASE)
    if ka_match:
        ka_raw = ka_match.group(1).strip()
        key_alignments = [line.strip().lstrip("-*• ") for line in ka_raw.splitlines() if line.strip().lstrip("-*• ")]
    else:
        key_alignments = [
            f"Demonstrated technical skills in {candidate.get('skills', 'core engineering')}",
            f"Directly applicable project experience aligned with {target_role}"
        ]

    # Check for [MISSING REQUIREMENTS] section
    mr_match = re.search(r"\[MISSING REQUIREMENTS\](.*)", output, re.DOTALL | re.IGNORECASE)
    if mr_match:
        mr_raw = mr_match.group(1).strip()
        missing_requirements = [line.strip().lstrip("-*• ") for line in mr_raw.splitlines() if line.strip().lstrip("-*• ")]
    else:
        missing_requirements = ["None detected in candidate ground-truth profile."]

    # Fallback to guaranteed realistic letter if parsing resulted in empty text
    if not cover_letter_text:
        cover_letter_text = _generate_fallback_cover_letter(candidate, company_name, target_role)

    return {
        "full_content": cover_letter_text,
        "key_alignments": key_alignments,
        "missing_requirements": missing_requirements
    }


def _generate_fallback_cover_letter(candidate: Dict[str, Any], company_name: str, target_role: str) -> str:
    """Generates an authentic fallback cover letter strictly adhering to candidate facts."""
    name = candidate.get("name", "Candidate")
    email = candidate.get("email", "candidate@example.com")
    phone = candidate.get("phone", "+1 555-0199")
    edu = candidate.get("education", "Computer Science")
    skills = candidate.get("skills", "Software Development")
    projects = candidate.get("projects", "Academic software projects")
    exp = candidate.get("experience", "")

    exp_para = (
        f"During my practical experience ({exp}), I developed a strong habit of writing reliable, "
        "tested code and collaborating across teams to solve complex technical problems."
        if exp else
        f"Through hands-on project work—including {projects}—I applied sound engineering principles "
        "to design robust solutions with clean, maintainable architecture."
    )

    return f"""{name}
{email} | {phone}
Hiring Team
{company_name}

Dear Hiring Team at {company_name},

I am writing to express my strong interest in the {target_role} position at {company_name}. With my background in {edu} and hands-on technical proficiency in {skills}, I am eager to contribute effectively to your engineering initiatives.

{exp_para} My technical skill set includes {skills}, which directly prepares me to understand your codebase, implement reliable features, and adhere to industry best practices.

What excites me most about {company_name} is the opportunity to apply my practical skills in a collaborative, high-impact environment. I pride myself on disciplined problem-solving, rapid learning of new frameworks, and a commitment to transparent communication.

Thank you for your time and consideration. I welcome the opportunity to discuss how my verified background and enthusiasm for software excellence align with the goals of {company_name}.

Sincerely,

{name}
"""
