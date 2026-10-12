
import os
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app, get_db
from database import Base


# Connect to the test database
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if not TEST_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL is missing from .env")

test_engine = create_engine(TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


# Use the test database for API requests
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

Base.metadata.create_all(bind=test_engine)

client = TestClient(app)


# Clean up test users before each test
@pytest.fixture(autouse=True)
def clean_test_users():
    from models import User, JobApplication

    test_emails = [
        "duplicate_test@example.com",
        "owner_test@example.com",
        "other_test@example.com",
    ]

    db = TestingSessionLocal()

    try:
        user_ids = db.query(User.id).filter(
            User.email.in_(test_emails)
        )

        db.query(JobApplication).filter(
            JobApplication.user_id.in_(user_ids)
        ).delete(synchronize_session=False)

        db.query(User).filter(
            User.email.in_(test_emails)
        ).delete(synchronize_session=False)

        db.commit()
    finally:
        db.close()

    yield


# Test 1: Home endpoint
def test_home():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "AI JOB TRACKER"}


# Test 2: Access /me without a token
def test_me_without_token():
    response = client.get("/me")

    assert response.status_code == 401


# Test 3: Duplicate registration should fail
def test_duplicate_registration():
    email = "duplicate_test@example.com"

    user_data = {
        "name": "Test User",
        "email": email,
        "password": "TestPassword123!",
    }

    first_response = client.post(
        "/register",
        json=user_data,
    )

    assert first_response.status_code in (200, 201)

    second_response = client.post(
        "/register",
        json=user_data,
    )

    assert second_response.status_code == 409


# Test 4: A user cannot access another user's job
def test_user_cannot_access_another_users_job():
    from models import User, JobApplication
    from authentication import hash_password

    db = TestingSessionLocal()

    user_a_email = "owner_test@example.com"
    user_b_email = "other_test@example.com"

    try:
        # Create two users
        user_a = User(
            name="Owner Test",
            email=user_a_email,
            password=hash_password("TestPassword123!"),
        )

        user_b = User(
            name="Other Test",
            email=user_b_email,
            password=hash_password("TestPassword123!"),
        )

        db.add_all([user_a, user_b])
        db.commit()

        db.refresh(user_a)
        db.refresh(user_b)

        # Create a job belonging to User A
        job = JobApplication(
            user_id=user_a.id,
            company="Test Company",
            role="Developer",
            job_url="https://example.com/job",
            status="Applied",
            applied_date=date.today(),
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        job_id = job.id

    finally:
        db.close()

    # Log in as User B
    login_response = client.post(
        "/login",
        data={
            "username": user_b_email,
            "password": "TestPassword123!",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    # User B tries to access User A's job
    response = client.get(
        f"/jobs/{job_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 404
