"""
Tests for Readability Heuristics, Claim Verification Logic, and Resume Improvement
"""

from services.readability_service import analyze_text_readability
from services.verification import (
    verify_claims_in_text, audit_and_save_document_claims,
    STATUS_SUPPORTED, STATUS_NEEDS_CONFIRM, STATUS_UNSUPPORTED, STATUS_CONTRADICTION
)
from services.database import get_candidate_by_id, get_verification_record_by_id


def test_readability_metrics():
    """Validates word count, sentence analysis, and keyword match percentages."""
    text = """
    # Education
    B.Tech in Computer Science from National Institute of Technology.
    
    # Technical Skills
    Python, Flask, JavaScript, SQLite, PostgreSQL, Git, Docker, REST APIs.
    
    # Projects
    Built a comprehensive Campus Placement Portal with automated testing.
    """
    jd = "Seeking a developer skilled in Python, Flask, Docker, and PostgreSQL."

    metrics = analyze_text_readability(text, jd)
    assert metrics["word_count"] > 20
    assert "Education" in metrics["detected_sections"]
    assert "Skills" in metrics["detected_sections"]
    assert "Projects" in metrics["detected_sections"]
    assert metrics["keyword_match_percentage"] > 50.0
    assert "python" in [k.lower() for k in metrics["matched_keywords"]]
    assert "flask" in [k.lower() for k in metrics["matched_keywords"]]


def test_claim_verification_supported_vs_contradiction():
    """Verifies that matching degrees are supported and conflicting degrees trigger contradictions."""
    candidate = {
        "id": 1,
        "name": "Aarav Sharma",
        "education": "B.Tech in Computer Science and Engineering",
        "graduation_year": "2026",
        "skills": "Python, Flask, SQLite, Git",
        "projects": "Built placement system with 500+ student profiles.",
        "experience": "Intern at CloudVibe; reduced latency by 25%."
    }

    # Document asserting true B.Tech degree and supported 25% metric
    doc_truth = "Aarav Sharma completed B.Tech in Computer Science. Reduced latency by 25%."
    claims_truth = verify_claims_in_text(candidate, doc_truth)

    degree_claim = next((c for c in claims_truth if "B.Tech" in c["claim_text"]), None)
    assert degree_claim is not None
    assert degree_claim["status"] == STATUS_SUPPORTED

    metric_claim = next((c for c in claims_truth if "25%" in c["claim_text"]), None)
    assert metric_claim is not None
    assert metric_claim["status"] == STATUS_SUPPORTED

    # Document claiming an exaggerated Ph.D. degree
    doc_fabrication = "Aarav Sharma holds a Ph.D. in Artificial Intelligence."
    claims_fabrication = verify_claims_in_text(candidate, doc_fabrication)

    phd_claim = next((c for c in claims_fabrication if "Ph.D." in c["claim_text"]), None)
    assert phd_claim is not None
    assert phd_claim["status"] == STATUS_CONTRADICTION
    assert "Candidate ground truth" in phd_claim["supporting_info"]


def test_claim_verification_unsupported_skills():
    """Verifies that unlisted technical skills are flagged as unsupported."""
    candidate = {
        "id": 1,
        "name": "Jane Developer",
        "education": "B.S. Software Engineering",
        "skills": "Python, Flask",
        "projects": "",
        "experience": ""
    }

    doc_text = "Proficient in Python, Flask, Kubernetes, and Rust."
    claims = verify_claims_in_text(candidate, doc_text)

    python_claim = next((c for c in claims if "Python" in c["claim_text"]), None)
    assert python_claim["status"] == STATUS_SUPPORTED

    rust_claim = next((c for c in claims if "Rust" in c["claim_text"]), None)
    assert rust_claim is not None
    assert rust_claim["status"] == STATUS_UNSUPPORTED


def test_resume_improve_route_with_consent(client):
    """Tests the full AI resume improvement route including privacy consent check."""
    # Create candidate
    client.post("/candidates/new", data={
        "name": "Kiran Kumar",
        "education": "B.Tech Electrical",
        "skills": "Python, Embedded C",
        "target_role": "Embedded Software Engineer"
    }, follow_redirects=True)

    # Ingest resume
    client.post("/resume/ingest", data={
        "candidate_id": 1,
        "input_method": "manual",
        "manual_resume_text": "Kiran Kumar\nB.Tech Electrical\nSkills: Python, Embedded C\nProjects: Smart Microcontroller",
        "target_job_title": "Embedded Software Engineer",
        "target_company": "IoT Solutions",
        "job_description": "Seeking Python and C programmer."
    }, follow_redirects=True)

    # Attempt improvement WITHOUT consent -> must be rejected
    res_no_consent = client.post("/resume/improve", data={
        "candidate_id": 1,
        "doc_id": 1,
        # user_consent omitted
    }, follow_redirects=True)
    assert b"privacy consent is required" in res_no_consent.data

    # Attempt improvement WITH consent -> succeeds
    res_with_consent = client.post("/resume/improve", data={
        "candidate_id": 1,
        "doc_id": 1,
        "user_consent": "1"
    }, follow_redirects=True)
    assert res_with_consent.status_code == 200
    assert b"Side-by-Side Comparison" in res_with_consent.data
    assert b"Key Improvements" in res_with_consent.data


def test_claim_resolution_workflow(client):
    """Tests resolving an audited claim via the verification interface."""
    # Create candidate and ingest doc
    client.post("/candidates/new", data={
        "name": "Audit Test Candidate",
        "education": "B.Tech CSE",
        "skills": "Python, SQL",
        "target_role": "Data Analyst"
    }, follow_redirects=True)

    client.post("/resume/ingest", data={
        "candidate_id": 1,
        "input_method": "manual",
        "manual_resume_text": "Candidate with B.Tech CSE. Skills: Python, SQL, Rust. Improved queries by 45%.",
        "target_job_title": "Data Analyst"
    }, follow_redirects=True)

    # Improve resume to generate claims
    client.post("/resume/improve", data={
        "candidate_id": 1,
        "doc_id": 1,
        "user_consent": "1"
    }, follow_redirects=True)

    # Verify that claims exist on verification route
    res_verif = client.get("/verification?candidate_id=1")
    assert res_verif.status_code == 200
    assert b"Claim Audit Checklist" in res_verif.data

    # Resolve claim #1 as confirmed
    res_resolve = client.post("/verification/1/resolve", data={
        "candidate_id": 1,
        "resolution": "confirmed"
    }, follow_redirects=True)
    assert res_resolve.status_code == 200
    assert b"resolution marked as" in res_resolve.data
    assert b"confirmed" in res_resolve.data


def test_update_improved_resume_edits(client):
    """Tests editing and accepting an AI-improved resume."""
    # Create candidate and ingest doc
    client.post("/candidates/new", data={
        "name": "Edit Test Candidate",
        "education": "B.S. CS",
        "skills": "Python",
        "target_role": "Junior Dev"
    }, follow_redirects=True)

    client.post("/resume/ingest", data={
        "candidate_id": 1,
        "input_method": "manual",
        "manual_resume_text": "Resume content for editing.",
        "target_job_title": "Junior Dev"
    }, follow_redirects=True)

    client.post("/resume/improve", data={
        "candidate_id": 1,
        "doc_id": 1,
        "user_consent": "1"
    }, follow_redirects=True)

    # Update manual text
    res_save = client.post("/resume/improve/update", data={
        "improved_id": 1,
        "candidate_id": 1,
        "doc_id": 1,
        "action_type": "save",
        "improved_text": "Candidate refined this section personally with extra verified details."
    }, follow_redirects=True)
    assert b"Resume edits saved successfully" in res_save.data
    assert b"Candidate refined this section personally" in res_save.data

    # Accept version
    res_accept = client.post("/resume/improve/update", data={
        "improved_id": 1,
        "candidate_id": 1,
        "doc_id": 1,
        "action_type": "accept"
    }, follow_redirects=True)
    assert b"Accepted" in res_accept.data
