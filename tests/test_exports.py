"""
Tests for Document Exports (ReportLab PDF & python-docx DOCX),
Cover Letter Service, Portfolio Builder, and Export Download Routes.
"""

import os
import io
import tempfile
from docx import Document
from services.export_service import (
    export_resume_to_pdf, export_resume_to_docx,
    export_cover_letter_to_pdf, export_cover_letter_to_docx
)
from services.cover_letter_service import generate_cover_letter
from services.portfolio_service import generate_portfolio_and_script


def test_pdf_export_generation():
    """Verifies that ReportLab creates valid PDF files with binary header %PDF."""
    candidate = {
        "name": "Aarav Sharma",
        "email": "aarav.sharma@example.edu",
        "phone": "+91 98765 43210",
        "location": "Bengaluru, India"
    }
    resume_text = """
# Aarav Sharma
## Professional Summary
Dedicated 3rd-year engineering student with proven skills in Python, Flask, and SQLite.

## Technical Skills
- Programming Languages: Python, JavaScript, C++
- Frameworks: Flask, HTML5, CSS3
- Tools & Databases: SQLite, Git, Docker, Pytest

## Featured Projects
- Campus Placement Portal: Built with Flask and SQLite, managing 500+ student profiles.
"""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
        pdf_path = tf.name

    try:
        exported_path = export_resume_to_pdf(candidate, resume_text, pdf_path)
        assert os.path.exists(exported_path)
        assert os.path.getsize(exported_path) > 1000

        with open(exported_path, "rb") as f:
            header = f.read(4)
            assert header == b"%PDF"
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)


def test_docx_export_generation():
    """Verifies that python-docx generates openable .docx documents containing candidate content."""
    candidate = {
        "name": "Priya Patel",
        "email": "priya.patel@example.edu",
        "phone": "+91 91234 56789",
        "location": "Pune, India"
    }
    resume_text = """
# Priya Patel
## Education
B.Tech in Computer Engineering, Class of 2026

## Skills
Python, Django, PostgreSQL, REST APIs

## Experience
Software Development Intern at FinTech Systems
"""
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
        docx_path = tf.name

    try:
        exported_path = export_resume_to_docx(candidate, resume_text, docx_path)
        assert os.path.exists(exported_path)
        assert os.path.getsize(exported_path) > 1000

        # Verify document readability with python-docx
        doc = Document(exported_path)
        doc_text = " ".join([p.text for p in doc.paragraphs])
        assert "Priya Patel" in doc_text
        assert "EDUCATION" in doc_text or "Education" in doc_text
        assert "Django" in doc_text
    finally:
        if os.path.exists(docx_path):
            os.remove(docx_path)


def test_cover_letter_service_generation():
    """Validates tailored cover letter generation and structured alignment extraction."""
    candidate = {
        "id": 1,
        "name": "Kiran Kumar",
        "education": "B.Tech Electrical & Electronics",
        "skills": "Python, Embedded C, MQTT",
        "projects": "IoT Weather Monitoring Station",
        "experience": "Academic Project Lead"
    }

    res = generate_cover_letter(
        candidate=candidate,
        target_role="Junior IoT Firmware Engineer",
        company_name="SmartSensors Inc.",
        job_description="Seeking developer with Python and Embedded C skills for sensor telemetry."
    )

    assert res["success"] is True
    assert "full_content" in res
    assert "SmartSensors Inc." in res["full_content"]
    assert "Kiran Kumar" in res["full_content"]
    assert len(res["key_alignments"]) > 0


def test_portfolio_and_script_service():
    """Validates portfolio data structure and 30-60s video script timing metrics."""
    candidate = {
        "id": 1,
        "name": "Aarav Sharma",
        "target_role": "Full-Stack Engineer",
        "education": "B.Tech Computer Science and Engineering",
        "skills": "Python, Flask, SQLite, Git, Pytest",
        "projects": "Built campus placement system with automated unit tests."
    }

    res = generate_portfolio_and_script(candidate)

    assert res["success"] is True
    assert res["headline"]
    assert res["introduction"]
    assert res["video_script"]
    assert "[0:00 - 0:10" in res["video_script"]
    assert "[0:50 - 1:00" in res["video_script"]

    # Verify script duration is tuned for 30-60s
    metrics = res["script_metrics"]
    assert 20 <= metrics["estimated_seconds"] <= 70
    assert metrics["word_count"] > 30


def test_cover_letter_routes_and_consent(client):
    """Tests the cover letter web workflow: consent gating, generation, and manual editing."""
    # 1. Create candidate
    client.post("/candidates/new", data={
        "name": "Cover Letter Candidate",
        "education": "B.S. Computer Science",
        "skills": "Python, Flask, SQL",
        "target_role": "Backend Engineer"
    }, follow_redirects=True)

    # 2. Attempt generation WITHOUT consent -> rejected
    res_no_consent = client.post("/cover-letter/generate", data={
        "candidate_id": 1,
        "company_name": "CloudNine Solutions",
        "target_role": "Backend Engineer",
        "job_description": "Python developer wanted."
        # user_consent omitted
    }, follow_redirects=True)
    assert b"privacy consent is required" in res_no_consent.data

    # 3. Generation WITH consent -> succeeds
    res_with_consent = client.post("/cover-letter/generate", data={
        "candidate_id": 1,
        "company_name": "CloudNine Solutions",
        "target_role": "Backend Engineer",
        "job_description": "Python developer wanted.",
        "user_consent": "1"
    }, follow_redirects=True)
    assert res_with_consent.status_code == 200
    assert b"CloudNine Solutions" in res_with_consent.data
    assert b"Save Letter Edits" in res_with_consent.data

    # 4. Save manual edits to cover letter
    res_edit = client.post("/cover-letter/1/edit", data={
        "candidate_id": 1,
        "full_content": "Dear Hiring Team at CloudNine Solutions,\n\nI am thrilled to apply for the Backend Engineer position with genuine verified skills."
    }, follow_redirects=True)
    assert res_edit.status_code == 200
    assert b"Cover letter edits saved successfully" in res_edit.data
    assert b"I am thrilled to apply" in res_edit.data


def test_portfolio_routes_and_consent(client):
    """Tests portfolio generation with consent and manual section editing."""
    # 1. Create candidate
    client.post("/candidates/new", data={
        "name": "Portfolio Candidate",
        "education": "B.Tech IT",
        "skills": "JavaScript, React, Node.js",
        "target_role": "Frontend Developer"
    }, follow_redirects=True)

    # 2. Attempt generation WITHOUT consent -> rejected
    res_no_consent = client.post("/portfolio/generate", data={
        "candidate_id": 1,
        "theme": "clean-purple"
        # user_consent omitted
    }, follow_redirects=True)
    assert b"privacy consent is required" in res_no_consent.data

    # 3. Generation WITH consent -> succeeds
    res_with_consent = client.post("/portfolio/generate", data={
        "candidate_id": 1,
        "theme": "clean-purple",
        "user_consent": "1"
    }, follow_redirects=True)
    assert res_with_consent.status_code == 200
    assert b"One-Page Web Portfolio" in res_with_consent.data
    assert b"30\xe2\x80\x9360s Video Script" in res_with_consent.data or b"Video Script" in res_with_consent.data

    # 4. Save manual edits to portfolio
    res_edit = client.post("/portfolio/1/edit", data={
        "candidate_id": 1,
        "headline": "Lead Frontend Specialist",
        "introduction": "Refined personal narrative.",
        "skills_section": "JavaScript, React, CSS3",
        "projects_section": "Interactive Web Applications",
        "experience_section": "Independent Project Work",
        "contact_section": "Email: test@example.com",
        "video_script": "[0:00 - 0:10] Hello, I am a frontend developer."
    }, follow_redirects=True)
    assert res_edit.status_code == 200
    assert b"Portfolio details and video script updated successfully" in res_edit.data
    assert b"Lead Frontend Specialist" in res_edit.data


def test_export_download_routes(client):
    """Tests downloading improved resumes and cover letters as PDF and DOCX attachments."""
    # 1. Create candidate, ingest resume, improve resume
    client.post("/candidates/new", data={
        "name": "Export Candidate",
        "education": "B.Tech CSE",
        "skills": "Python, Flask",
        "target_role": "Software Engineer"
    }, follow_redirects=True)

    client.post("/resume/ingest", data={
        "candidate_id": 1,
        "input_method": "manual",
        "manual_resume_text": "Export Candidate Resume Text"
    }, follow_redirects=True)

    client.post("/resume/improve", data={
        "candidate_id": 1,
        "doc_id": 1,
        "user_consent": "1"
    }, follow_redirects=True)

    # 2. Download Resume as PDF
    res_pdf = client.get("/export/resume/1/pdf")
    assert res_pdf.status_code == 200
    assert res_pdf.mimetype == "application/pdf"
    assert "attachment" in res_pdf.headers["Content-Disposition"]
    assert res_pdf.data.startswith(b"%PDF")

    # 3. Download Resume as DOCX
    res_docx = client.get("/export/resume/1/docx")
    assert res_docx.status_code == 200
    assert "openxmlformats" in res_docx.mimetype or "word" in res_docx.mimetype
    assert "attachment" in res_docx.headers["Content-Disposition"]

    # 4. Generate and download Cover Letter as PDF and DOCX
    client.post("/cover-letter/generate", data={
        "candidate_id": 1,
        "company_name": "DownloadCorp",
        "target_role": "Software Engineer",
        "user_consent": "1"
    }, follow_redirects=True)

    cl_pdf = client.get("/export/cover-letter/1/pdf")
    assert cl_pdf.status_code == 200
    assert cl_pdf.mimetype == "application/pdf"
    assert cl_pdf.data.startswith(b"%PDF")

    cl_docx = client.get("/export/cover-letter/1/docx")
    assert cl_docx.status_code == 200
    assert "openxmlformats" in cl_docx.mimetype or "word" in cl_docx.mimetype


def test_export_security_format_validation(client):
    """Tests that unsupported export formats are rejected with HTTP 400."""
    res_bad_format = client.get("/export/resume/1/exe")
    assert res_bad_format.status_code == 400
    assert b"Unsupported export format" in res_bad_format.data
