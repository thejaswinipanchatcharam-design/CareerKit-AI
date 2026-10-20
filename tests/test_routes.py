"""
Tests for Core Routes & HTTP Responses in CareerKit AI
"""


def test_dashboard_route(client):
    """Verifies that the dashboard root route responds with 200 and loads core brand text."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"CareerKit AI" in response.data
    assert b"Application Dashboard" in response.data
    assert b"Total Candidates" in response.data


def test_navigation_routes(client):
    """Ensures all 7 primary sidebar links load without 404 or 500 errors."""
    routes = [
        "/",
        "/candidates",
        "/candidates/new",
        "/resume",
        "/cover-letter",
        "/portfolio",
        "/verification",
        "/report",
    ]
    for route in routes:
        response = client.get(route)
        assert response.status_code == 200, f"Route {route} failed with status {response.status_code}"


def test_404_error_page(client):
    """Ensures nonexistent routes return 404 and render the custom 404 template."""
    response = client.get("/this-route-definitely-does-not-exist")
    assert response.status_code == 404
    assert b"404 - Resource Not Found" in response.data
