
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing from .env")

client = genai.Client(api_key=api_key)


def analyze_job_description(description: str) -> str:
    prompt = f"""
    Analyze this job description for a job-tracking application.

    Return:
    1. Required skills
    2. Main responsibilities
    3. Experience level

    Keep the answer clear and structured.
    If information is not specified, say "Not specified".

    Job description:
    {description}
    """

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
    )

    return response.text or "No analysis returned."
