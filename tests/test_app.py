"""Tests for the FastAPI activities application."""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to a known state before each test."""
    # Store original state
    original_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    }
    
    # Reset activities
    activities.clear()
    for name, details in original_activities.items():
        activities[name] = details.copy()
        activities[name]["participants"] = details["participants"].copy()
    
    yield
    
    # Cleanup - reset again after test
    activities.clear()
    for name, details in original_activities.items():
        activities[name] = details.copy()
        activities[name]["participants"] = details["participants"].copy()


class TestGetActivities:
    """Tests for the GET /activities endpoint."""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_get_activities_includes_participants(self, client, reset_activities):
        """Test that activities include participant information."""
        response = client.get("/activities")
        data = response.json()
        assert "participants" in data["Chess Club"]
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
    
    def test_get_activities_includes_capacity(self, client, reset_activities):
        """Test that activities include capacity information."""
        response = client.get("/activities")
        data = response.json()
        assert "max_participants" in data["Chess Club"]
        assert data["Chess Club"]["max_participants"] == 12


class TestSignup:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_adds_participant(self, client, reset_activities):
        """Test that signing up adds a participant to an activity."""
        email = "newstudent@mergington.edu"
        response = client.post(
            f"/activities/Chess Club/signup?email={email}",
            follow_redirects=True
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert email in activities["Chess Club"]["participants"]
    
    def test_signup_duplicate_fails(self, client, reset_activities):
        """Test that signing up a duplicate participant fails."""
        email = "michael@mergington.edu"
        response = client.post(
            f"/activities/Chess Club/signup?email={email}",
            follow_redirects=True
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_nonexistent_activity_fails(self, client, reset_activities):
        """Test that signing up for nonexistent activity fails."""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=test@example.com",
            follow_redirects=True
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]
    
    def test_signup_returns_success_message(self, client, reset_activities):
        """Test that successful signup returns appropriate message."""
        email = "newstudent@mergington.edu"
        response = client.post(
            f"/activities/Programming Class/signup?email={email}",
            follow_redirects=True
        )
        assert response.status_code == 200
        data = response.json()
        assert email in data["message"]
        assert "Programming Class" in data["message"]


class TestUnregister:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint."""
    
    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregistering removes a participant."""
        email = "michael@mergington.edu"
        assert email in activities["Chess Club"]["participants"]
        
        response = client.delete(
            f"/activities/Chess Club/unregister?email={email}",
            follow_redirects=True
        )
        assert response.status_code == 200
        assert email not in activities["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_participant_fails(self, client, reset_activities):
        """Test that unregistering a non-participant fails."""
        email = "nobody@mergington.edu"
        response = client.delete(
            f"/activities/Chess Club/unregister?email={email}",
            follow_redirects=True
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]
    
    def test_unregister_nonexistent_activity_fails(self, client, reset_activities):
        """Test that unregistering from nonexistent activity fails."""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister?email=test@example.com",
            follow_redirects=True
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]
    
    def test_unregister_returns_success_message(self, client, reset_activities):
        """Test that successful unregister returns appropriate message."""
        email = "emma@mergington.edu"
        response = client.delete(
            f"/activities/Programming Class/unregister?email={email}",
            follow_redirects=True
        )
        assert response.status_code == 200
        data = response.json()
        assert email in data["message"]
        assert "Programming Class" in data["message"]


class TestActivityParticipantCounts:
    """Tests for participant counts across operations."""
    
    def test_participant_count_increases_on_signup(self, client, reset_activities):
        """Test that participant count increases when signing up."""
        initial_count = len(activities["Gym Class"]["participants"])
        response = client.post(
            "/activities/Gym Class/signup?email=newparticipant@mergington.edu",
            follow_redirects=True
        )
        assert response.status_code == 200
        assert len(activities["Gym Class"]["participants"]) == initial_count + 1
    
    def test_participant_count_decreases_on_unregister(self, client, reset_activities):
        """Test that participant count decreases when unregistering."""
        initial_count = len(activities["Chess Club"]["participants"])
        response = client.delete(
            f"/activities/Chess Club/unregister?email=michael@mergington.edu",
            follow_redirects=True
        )
        assert response.status_code == 200
        assert len(activities["Chess Club"]["participants"]) == initial_count - 1
