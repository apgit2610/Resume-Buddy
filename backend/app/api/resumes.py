from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.resume import Resume
from app.schemas.resume import ResumeCreate, ResumeResponse, ResumeUpdate
from typing import List
from jose import jwt

router = APIRouter()

SECRET_KEY = "resumex-secret-key"
ALGORITHM = "HS256"

def get_current_user_id(token: str) -> int:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return int(payload.get("sub"))

@router.post("/", response_model=ResumeResponse)
def create_resume(resume: ResumeCreate, token: str, db: Session = Depends(get_db)):
    user_id = get_current_user_id(token)
    new_resume = Resume(
        user_id=user_id,
        title=resume.title,
        template=resume.template,
        content=resume.content
    )
    db.add(new_resume)
    db.commit()
    db.refresh(new_resume)
    return new_resume

@router.get("/", response_model=List[ResumeResponse])
def get_resumes(token: str, db: Session = Depends(get_db)):
    user_id = get_current_user_id(token)
    resumes = db.query(Resume).filter(Resume.user_id == user_id).all()
    return resumes

@router.get("/{resume_id}", response_model=ResumeResponse)
def get_resume(resume_id: int, token: str, db: Session = Depends(get_db)):
    user_id = get_current_user_id(token)
    resume = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == user_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume

@router.put("/{resume_id}", response_model=ResumeResponse)
def update_resume(resume_id: int, resume: ResumeUpdate, token: str, db: Session = Depends(get_db)):
    user_id = get_current_user_id(token)
    db_resume = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == user_id).first()
    if not db_resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    db_resume.title = resume.title
    db_resume.content = resume.content
    db.commit()
    db.refresh(db_resume)
    return db_resume

@router.delete("/{resume_id}")
def delete_resume(resume_id: int, token: str, db: Session = Depends(get_db)):
    user_id = get_current_user_id(token)
    resume = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == user_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    db.delete(resume)
    db.commit()
    return {"message": "Resume deleted"}