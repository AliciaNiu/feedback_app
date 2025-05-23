import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from unittest.mock import patch, MagicMock
import os
import base64

USERNAME = os.getenv("BASIC_AUTH_USERNAME")
PASSWORD = os.getenv("BASIC_AUTH_PASSWORD")
BASE_URL = os.getenv("FEEDBACK_BASE_URL")

# Test auth helper
def basic_auth_header(username: str, password: str) -> dict:
    credentials = f"{username}:{password}"
    token = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {token}"}

@pytest.mark.asyncio
@patch("app.main.connect_db")
async def test_feedback_success(mock_connect_db):
    # Mock the DB connection and cursor
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect_db.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    payload = {
        "session_id": "abc123",
        "page_context": {"page": "home"},
        "action": "thumbs_up"
    }
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as client:
        response = await client.post(
            "/api/feedback",
            json=payload,
            headers=basic_auth_header(USERNAME, PASSWORD)
        )
    
    assert response.status_code == 200
    assert "Feedback successfully saved" == response.json()["message"]
    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()


@pytest.mark.asyncio
async def test_feedback_missing_fields():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as client:
        response = await client.post(
            "/api/feedback",
            json={"action": "thumbs_up"},  # missing page_context
            headers=basic_auth_header(USERNAME, PASSWORD)
        )
    
    assert response.status_code == 400
    assert "Missing fields" in response.json()["error"]

@pytest.mark.asyncio
async def test_feedback_invalid_action():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as client:
        response = await client.post(
            "/api/feedback",
            json={
                "page_context": {"page": "about"},
                "action": "like"
            },
            headers=basic_auth_header(USERNAME, PASSWORD)
        )
    
    assert response.status_code == 400
    assert "Invalid action data" in response.json()["error"]

@pytest.mark.asyncio
async def test_feedback_invalid_page_context():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as client:
        response = await client.post(
            "/api/feedback",
            json={
                "page_context": "home",  # not a dict
                "action": "thumbs_down"
            },
            headers=basic_auth_header(USERNAME, PASSWORD)
        )
    
    assert response.status_code == 400
    assert "page content must be a JSON object" in response.json()["error"]
