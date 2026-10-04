from sqlalchemy import Column, Integer, String,Date,ForeignKey
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable =False)

class JobApplication(Base):
    __tablename__ = "Job Application"

    id =Column(Integer,primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company = Column(String, nullable=False)
    role = Column(String, nullable=False)
    job_url = Column(String)
    status = Column(String, nullable=False)
    applied_date = Column(Date, nullable=False)    