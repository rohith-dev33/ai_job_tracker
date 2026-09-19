from fastapi import FastAPI

app = FastAPI(title="AI JOB TRACKER")


@app.get("/")
def home():
    return{"message": "AI JOB TRACKER"}
