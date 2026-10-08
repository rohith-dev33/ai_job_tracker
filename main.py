from fastapi import FastAPI,Depends,Form,HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

from database import Base, engine,SessionLocal
import models
from schemas import UserCreate, UserLogin, JobApplicationCreate, UserResponse

from authentication import hash_password, verify_password,create_access_token,decode_access_token
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
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    print("TOKEN PARTS:", len(token.split(".")))
    print("TOKEN START:", token[:10])
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    user = db.query(models.User).filter(
        models.User.id == int(user_id)
    ).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return user

@app.post("/jobs")
def create_job(
    job: JobApplicationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
     new_job = models.JobApplication(
    user_id=current_user.id,
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
def login_user(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    db_user = db.query(models.User).filter(
        models.User.email == username
    ).first()

    if not db_user:
        return {"message": "Invalid email or password"}

    if not verify_password(password, db_user.password):
        return {"message": "Invalid email or password"}

    access_token = create_access_token(
        {"sub": str(db_user.id)}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
    return {"message": "Login successful"}

@app.get("/me", response_model=UserResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@app.get("/jobs")
def get_jobs(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.JobApplication).filter(
        models.JobApplication.user_id == current_user.id
    ).all()


