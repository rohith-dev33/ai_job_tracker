from datetime import date
from pydantic import BaseModel


class JobApplicationCreate(BaseModel):
    company: str
    role: str
    job_url: str | None = None
    status: str
    applied_date: date

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str    
