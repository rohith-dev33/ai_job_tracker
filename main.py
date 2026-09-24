from fastapi import FastAPI

from database import Base, engine
import models

app = FastAPI(title="AI JOB TRACKER")

Base.metadata.create_all(bind=engine)


@app.get("/")
def home():
    return {"message": "AI JOB TRACKER"}