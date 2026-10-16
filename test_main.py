
import os
from datetime import date
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app, get_db
from database import Base
from models import User, JobApplication
from authentication import hash_password


# -------------------------
# Test database configuration
# -------------------------

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if not TEST_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL is missing from .env")

test_engine = create_engine(TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)

Base.metadata.create_all(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


# -------------------------
# Test helpers
# -------------------------

TEST_EMAILS = [
    "register_test@example.com",
    "duplicate_test@example.com",
    "login_test@example.com",
    "me_test@example.com",
    "create_job_test@example.com",
    "list_job_test@example.com",
    "owner_test@example.com",
    "other_test@example.com",
    "update_job_test@example.com",
    "delete_job_test@example.com",
]

TEST_PASSWORD = "TestPassword123!"


@pytest.fixture(autouse=True)
def clean_test_data():
    """Remove test data before and after each test."""
    def cleanup():
        db = TestingSessionLocal()
        try:
            user_ids = db.query(User.id).filter(
                User.email.in_(TEST_EMAILS)
            )

            db.query(JobApplication).filter(
                JobApplication.user_id.in_(user_ids)
            ).delete(synchronize_session=False)

            db.query(User).filter(
                User.email.in_(TEST_EMAILS)
            ).delete(synchronize_session=False)

            db.commit()
        finally:
            db.close()

    cleanup()
    yield
    cleanup()


def create_test_user(email, password=TEST_PASSWORD):
    db = TestingSessionLocal()
    try:
        user = User(
            name="Test User",
            email=email,
            password=hash_password(password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.id
    finally:
        db.close()


def get_token(email, password=TEST_PASSWORD):
    response = client.post(
        "/login",
        data={
            "username": email,
            "password": password,
        },
    )

    assert response.status_code == 200
    assert "access_token" in response.json()

    return response.json()["access_token"]


def job_payload(company="Test Company", role="Backend Developer"):
    return {
        "company": company,
        "role": role,
        "job_url": "https://example.com/job",
        "status": "Applied",
        "applied_date": date.today().isoformat(),
    }


def create_job_with_token(token, payload=None):
    return client.post(
        "/jobs",
        json=payload or job_payload(),
        headers={"Authorization": f"Bearer {token}"},
    )


# -------------------------
# 1. Basic API tests
# -------------------------

def test_home():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "AI JOB TRACKER"}


def test_unknown_route():
    response = client.get("/route-that-does-not-exist")

    assert response.status_code == 404


# -------------------------
# 2. Registration tests
# -------------------------

def test_register_user():
    response = client.post(
        "/register",
        json={
            "name": "Register Test",
            "email": "register_test@example.com",
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code in (200, 201)
    assert response.json()["email"] == "register_test@example.com"


def test_duplicate_registration():
    data = {
        "name": "Duplicate Test",
        "email": "duplicate_test@example.com",
        "password": TEST_PASSWORD,
    }

    first = client.post("/register", json=data)
    second = client.post("/register", json=data)

    assert first.status_code in (200, 201)
    assert second.status_code == 409


def test_register_missing_required_field():
    response = client.post(
        "/register",
        json={
            "name": "Incomplete User",
            "email": "register_test@example.com",
        },
    )

    assert response.status_code == 422


# -------------------------
# 3. Login tests
# -------------------------

def test_login_success():
    email = "login_test@example.com"
    create_test_user(email)

    response = client.post(
        "/login",
        data={
            "username": email,
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_unknown_email():
    response = client.post(
        "/login",
        data={
            "username": "unknown_test@example.com",
            "password": TEST_PASSWORD,
        },
    )

    # Current API returns a message with status 200.
    assert response.status_code == 200
    assert response.json()["message"] == "Invalid email or password"


def test_login_wrong_password():
    email = "login_test@example.com"
    create_test_user(email)

    response = client.post(
        "/login",
        data={
            "username": email,
            "password": "WrongPassword123!",
        },
    )

    # Current API returns a message with status 200.
    assert response.status_code == 200
    assert response.json()["message"] == "Invalid email or password"


# -------------------------
# 4. Authentication tests
# -------------------------

def test_me_without_token():
    response = client.get("/me")

    assert response.status_code == 401


def test_me_with_invalid_token():
    response = client.get(
        "/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401


def test_me_with_valid_token():
    email = "me_test@example.com"
    create_test_user(email)
    token = get_token(email)

    response = client.get(
        "/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == email


# -------------------------
# 5. Create and list jobs
# -------------------------

def test_create_job_with_token():
    email = "create_job_test@example.com"
    create_test_user(email)
    token = get_token(email)

    response = create_job_with_token(token)

    assert response.status_code in (200, 201)
    assert response.json()["company"] == "Test Company"
    assert response.json()["role"] == "Backend Developer"


def test_create_job_without_token():
    response = client.post(
        "/jobs",
        json=job_payload(),
    )

    assert response.status_code == 401


def test_create_job_with_invalid_data():
    email = "create_job_test@example.com"
    create_test_user(email)
    token = get_token(email)

    response = create_job_with_token(
        token,
        {"company": "Missing required fields"},
    )

    assert response.status_code == 422


def test_list_own_jobs():
    email = "list_job_test@example.com"
    create_test_user(email)
    token = get_token(email)

    created = create_job_with_token(token)
    assert created.status_code in (200, 201)

    response = client.get(
        "/jobs",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert any(
        job["id"] == created.json()["id"]
        for job in response.json()
    )


# -------------------------
# 6. View jobs and user isolation
# -------------------------

def test_get_own_job():
    email = "owner_test@example.com"
    create_test_user(email)
    token = get_token(email)

    created = create_job_with_token(token)
    job_id = created.json()["id"]

    response = client.get(
        f"/jobs/{job_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == job_id


def test_user_cannot_access_another_users_job():
    owner_email = "owner_test@example.com"
    other_email = "other_test@example.com"

    create_test_user(owner_email)
    create_test_user(other_email)

    owner_token = get_token(owner_email)
    other_token = get_token(other_email)

    created = create_job_with_token(owner_token)
    assert created.status_code in (200, 201)

    job_id = created.json()["id"]

    response = client.get(
        f"/jobs/{job_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 404


def test_get_nonexistent_job():
    email = "owner_test@example.com"
    create_test_user(email)
    token = get_token(email)

    response = client.get(
        "/jobs/999999999",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


# -------------------------
# 7. Update jobs
# -------------------------

def test_update_own_job():
    email = "update_job_test@example.com"
    create_test_user(email)
    token = get_token(email)

    created = create_job_with_token(token)
    assert created.status_code in (200, 201)

    job_id = created.json()["id"]

    updated = client.patch(
        f"/jobs/{job_id}",
        json=job_payload(
            company="Updated Company",
            role="Senior Developer",
        ),
        headers={"Authorization": f"Bearer {token}"},
    )

    assert updated.status_code == 200
    assert updated.json()["company"] == "Updated Company"
    assert updated.json()["role"] == "Senior Developer"


def test_user_cannot_update_another_users_job():
    create_test_user("owner_test@example.com")
    create_test_user("other_test@example.com")

    owner_token = get_token("owner_test@example.com")
    other_token = get_token("other_test@example.com")

    created = create_job_with_token(owner_token)
    assert created.status_code in (200, 201)

    response = client.patch(
        f"/jobs/{created.json()['id']}",
        json=job_payload(company="Unauthorized Change"),
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 404


# -------------------------
# 8. Delete jobs
# -------------------------

def test_delete_own_job():
    email = "delete_job_test@example.com"
    create_test_user(email)
    token = get_token(email)

    created = create_job_with_token(token)
    assert created.status_code in (200, 201)

    job_id = created.json()["id"]

    deleted = client.delete(
        f"/jobs/{job_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert deleted.status_code == 200
    assert deleted.json()["message"] == "Job deleted successfully"

    fetched = client.get(
        f"/jobs/{job_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert fetched.status_code == 404


def test_user_cannot_delete_another_users_job():
    create_test_user("owner_test@example.com")
    create_test_user("other_test@example.com")

    owner_token = get_token("owner_test@example.com")
    other_token = get_token("other_test@example.com")

    created = create_job_with_token(owner_token)
    assert created.status_code in (200, 201)

    response = client.delete(
        f"/jobs/{created.json()['id']}",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 404


def test_delete_nonexistent_job():
    email = "delete_job_test@example.com"
    create_test_user(email)
    token = get_token(email)

    response = client.delete(
        "/jobs/999999999",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404



# -------------------------
# 9. AI job analysis tests
# -------------------------




@patch("main.analyze_job_description")
def test_ai_analyze_job_success(mock_analyze):
    mock_analyze.return_value = (
        "Required skills: Python, FastAPI, PostgreSQL\n"
        "Main responsibilities: Build backend APIs\n"
        "Experience level: Not specified"
    )

    response = client.post(
        "/ai/analyze-job",
        json={
            "description": (
                "Python backend developer with FastAPI "
                "and PostgreSQL experience."
            )
        },
    )

    assert response.status_code == 200
    assert "analysis" in response.json()
    assert "Python" in response.json()["analysis"]
    mock_analyze.assert_called_once()


@patch("main.analyze_job_description")
def test_ai_analyze_job_description_too_short(mock_analyze):
    response = client.post(
        "/ai/analyze-job",
        json={"description": "Python developer"},
    )

    assert response.status_code == 422
    mock_analyze.assert_not_called()


@patch("main.analyze_job_description")
def test_ai_analyze_job_service_failure(mock_analyze):
    mock_analyze.side_effect = Exception("AI service unavailable")

    response = client.post(
        "/ai/analyze-job",
        json={
            "description": (
                "Python backend developer with FastAPI "
                "and PostgreSQL experience."
            )
        },
    )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "AI analysis is temporarily unavailable. Please try again."
    )
