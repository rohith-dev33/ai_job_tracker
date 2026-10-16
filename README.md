
# AI Job Tracker

## Overview

AI Job Tracker is a backend application built with FastAPI and PostgreSQL
to help users manage their job applications.

Users can register, log in, and manage their own job application records.
The application also integrates Google Gemini AI to analyze job descriptions
and identify required skills, main responsibilities, and experience level.

## Key Features

- User registration and login
- JWT-based authentication
- Create, view, update, and delete job applications
- User-specific access to job records
- AI-powered job description analysis
- Input validation and error handling
- Automated API tests using pytest


## Technology Stack

- **Python** — Main programming language
- **FastAPI** — Framework for building REST APIs
- **PostgreSQL** — Relational database for storing application data
- **SQLAlchemy** — ORM for interacting with the database using Python
- **JWT** — Token-based authentication
- **Google Gemini API** — AI-powered job description analysis
- **Pytest** — Automated testing framework
- **Pydantic** — Request data validation
- **Git and GitHub** — Version control and source code hosting


## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/rohith-dev33/ai_job_tracker.git
cd ai_job_tracker
```

### 2. Create and Activate a Virtual Environment

On Windows:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root and configure the following variables:

```env
DATABASE_URL=your_postgresql_database_url
JWT_SECRET_KEY=your_secret_key
TEST_DATABASE_URL=your_test_database_url
GEMINI_API_KEY=your_gemini_api_key
```

Replace the placeholder values with your own configuration.
Never commit your `.env` file or expose your API keys and database passwords.

### 5. Run the Application

```bash
uvicorn main:app --reload
```

The API will be available at:

http://127.0.0.1:8000

### 6. Explore the API

Open the interactive Swagger documentation:

http://127.0.0.1:8000/docs


## Running Tests

The project uses pytest to test API endpoints, authentication,
job application management, user access controls, and AI analysis.

Run the complete test suite:

```powershell
python -m pytest -v
```

The test suite currently contains 26 tests covering the main
API functionality and AI endpoint behavior.

AI endpoint tests use mocked responses, so they do not need
to call the Gemini API for each test.
