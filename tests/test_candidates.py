"""
Tests for Candidate Profile Management (CRUD) and Validation
"""


def test_create_candidate_success(client):
    """Tests creating a new candidate with valid required fields."""
    response = client.post("/candidates/new", data={
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "+1 555-0123",
        "location": "Seattle, WA",
        "education": "B.S. in Computer Science",
        "graduation_year": "2025",
        "skills": "Python, Flask, SQLite, Pytest",
        "projects": "Built an automated testing suite.",
        "experience": "Intern at Tech Startup",
        "target_role": "Backend Engineer",
        "summary": "Motivated backend developer seeking junior roles."
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Jane Doe" in response.data
    assert b"Backend Engineer" in response.data
    assert b"Profile created successfully" in response.data


def test_create_candidate_missing_required_fields(client):
    """Ensures backend rejects submission when required fields (like education) are omitted."""
    response = client.post("/candidates/new", data={
        "name": "Incomplete Profile",
        "education": "",  # Missing required field
        "skills": "Python",
        "target_role": "Developer"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Please fill in all required fields" in response.data


def test_view_candidate_detail(client):
    """Tests viewing a candidate detail page by valid ID."""
    # First create
    client.post("/candidates/new", data={
        "name": "Mark Spencer",
        "education": "B.E. Information Technology",
        "skills": "JavaScript, Node.js",
        "target_role": "Frontend Developer"
    })

    # Read candidate 1
    response = client.get("/candidates/1")
    assert response.status_code == 200
    assert b"Mark Spencer" in response.data
    assert b"Frontend Developer" in response.data


def test_view_nonexistent_candidate_returns_404(client):
    """Querying an invalid candidate ID must trigger a 404 response."""
    response = client.get("/candidates/9999")
    assert response.status_code == 404
    assert b"404 - Resource Not Found" in response.data


def test_edit_candidate(client):
    """Tests updating an existing candidate profile."""
    # Create candidate
    client.post("/candidates/new", data={
        "name": "Alice Taylor",
        "education": "B.S. Software Engineering",
        "skills": "Python, Docker",
        "target_role": "DevOps Engineer"
    })

    # Update candidate 1
    response = client.post("/candidates/1/edit", data={
        "name": "Alice Taylor, Lead",
        "education": "B.S. Software Engineering",
        "skills": "Python, Docker, Kubernetes, CI/CD",
        "target_role": "Senior Cloud Engineer"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Alice Taylor, Lead" in response.data
    assert b"Senior Cloud Engineer" in response.data
    assert b"updated successfully" in response.data


def test_delete_candidate(client):
    """Tests deleting candidate and verifying removal from candidate directory."""
    # Create candidate
    client.post("/candidates/new", data={
        "name": "Temporary Candidate",
        "education": "B.A. General Studies",
        "skills": "Word, Excel",
        "target_role": "Office Assistant"
    })

    # Confirm candidate exists
    res_before = client.get("/candidates/1")
    assert res_before.status_code == 200

    # Delete candidate
    res_delete = client.post("/candidates/1/delete", follow_redirects=True)
    assert res_delete.status_code == 200
    assert b"deleted" in res_delete.data

    # Confirm candidate is gone (404)
    res_after = client.get("/candidates/1")
    assert res_after.status_code == 404


def test_search_candidates(client):
    """Tests candidate search by keyword across name, role, and skills."""
    # Create two different candidates
    client.post("/candidates/new", data={
        "name": "Sarah Connor",
        "education": "B.S. Cybernetics",
        "skills": "Robotics, Assembly, C++",
        "target_role": "Robotics Engineer"
    }, follow_redirects=True)

    client.post("/candidates/new", data={
        "name": "David Miller",
        "education": "B.A. Graphic Design",
        "skills": "Figma, CSS, UI Design",
        "target_role": "UI/UX Designer"
    }, follow_redirects=True)

    # Search for "Robotics"
    response_robotics = client.get("/candidates?q=Robotics")
    assert response_robotics.status_code == 200
    assert b"Sarah Connor" in response_robotics.data
    assert b"David Miller" not in response_robotics.data

    # Search for "Designer"
    response_designer = client.get("/candidates?q=Designer")
    assert response_designer.status_code == 200
    assert b"David Miller" in response_designer.data
    assert b"Sarah Connor" not in response_designer.data


def test_seed_sample_candidate_route(client):
    """Tests the one-click demo candidate loader for viva presentations."""
    response = client.post("/candidates/seed-sample", follow_redirects=True)
    assert response.status_code == 200
    assert b"Aarav Sharma" in response.data
    assert b"Junior Full-Stack Engineer" in response.data
    assert b"National Institute of Technology" in response.data
    assert b"Campus Placement Management System" in response.data


def test_candidate_documents_summary_service(app):
    """Tests document summary statistics generation for a candidate."""
    from services.database import create_candidate, get_candidate_documents_summary
    with app.app_context():
        db_path = app.config.get("DATABASE_PATH")
        candidate_id = create_candidate({
            "name": "Test Summary Candidate",
            "education": "B.Tech",
            "skills": "Python",
            "target_role": "Developer"
        }, db_path)

        summary = get_candidate_documents_summary(candidate_id, db_path)
        assert summary["original_documents"] == []
        assert summary["improved_documents"] == []
        assert summary["cover_letters"] == []
        assert summary["portfolios"] == []
        assert summary["claim_counts"]["supported"] == 0
        assert summary["claim_counts"]["needs_confirmation"] == 0

