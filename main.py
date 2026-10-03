from fastapi import FastAPI,Depends
from sqlalchemy.orm import Session

from database import Base, engine,SessionLocal
import models
from schemas import UserCreate, UserLogin, JobApplicationCreate

from authentication import hash_password, verify_password
app = FastAPI(title="AI JOB TRACKER")

Base.metadata.create_all(bind=engine)


@app.get("/")
def home():
    return {"message": "AI JOB TRACKER"}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/jobs")
def create_job(
    job: JobApplicationCreate,
    db: Session = Depends(get_db)
):
    new_job = models.JobApplication(
        company=job.company,
        role=job.role,
        job_url=job.job_url,
        status=job.status,
        applied_date=job.applied_date
    )

    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    return new_job

@app.post("/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = hash_password(user.password)

    new_user = models.User(
        name=user.name,
        email=user.email,
        password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user 

@app.post("/login")
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(
        models.User.email == user.email
    ).first()

    if not db_user:
        return {"message": "Invalid email or password"}

    if not verify_password(user.password, db_user.password):
        return {"message": "Invalid email or password"}

    return {"message": "Login successful"}