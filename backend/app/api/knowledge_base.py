from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.knowledge_base import (
    KBPersonal, KBEducation, KBProject,
    KBExperience, KBSkill, KBCertification, KBAchievement
)
from pydantic import BaseModel
from typing import Optional, List
from jose import jwt

router = APIRouter()

SECRET_KEY = "resumex-secret-key"
ALGORITHM = "HS256"

def get_user_id(token: str) -> int:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return int(payload.get("sub"))

def exclude_embedding(obj) -> dict:
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns if c.name != "embedding"}

# --- Schemas ---

class PersonalIn(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    summary: Optional[str] = None

class EducationIn(BaseModel):
    school: str
    degree: str
    field: Optional[str] = None
    start_year: Optional[str] = None
    end_year: Optional[str] = None
    grade: Optional[str] = None

class ProjectIn(BaseModel):
    title: str
    description: str
    technologies: Optional[str] = None
    role: Optional[str] = None
    outcomes: Optional[str] = None
    domain: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class ExperienceIn(BaseModel):
    company: str
    role: str
    responsibilities: Optional[str] = None
    technologies: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class SkillIn(BaseModel):
    category: str
    name: str

class CertificationIn(BaseModel):
    name: str
    issuer: Optional[str] = None
    skills_covered: Optional[str] = None
    date: Optional[str] = None

class AchievementIn(BaseModel):
    title: str
    description: Optional[str] = None
    date: Optional[str] = None

# --- Personal ---

@router.get("/personal")
def get_personal(token: str, db: Session = Depends(get_db)):
    user_id = get_user_id(token)
    personal = db.query(KBPersonal).filter(KBPersonal.user_id == user_id).first()
    return personal

@router.post("/personal")
def save_personal(data: PersonalIn, token: str, db: Session = Depends(get_db)):
    user_id = get_user_id(token)
    existing = db.query(KBPersonal).filter(KBPersonal.user_id == user_id).first()
    if existing:
        for key, value in data.model_dump().items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    new = KBPersonal(user_id=user_id, **data.model_dump())
    db.add(new)
    db.commit()
    db.refresh(new)
    return new

# --- Education ---

@router.get("/education")
def get_education(token: str, db: Session = Depends(get_db)):
    user_id = get_user_id(token)
    return db.query(KBEducation).filter(KBEducation.user_id == user_id).all()

@router.post("/education")
def add_education(data: EducationIn, token: str, db: Session = Depends(get_db)):
    user_id = get_user_id(token)
    new = KBEducation(user_id=user_id, **data.model_dump())
    db.add(new)
    db.commit()
    db.refresh(new)
    return new

@router.delete("/education/{id}")
def delete_education(id: int, token: str, db: Session = Depends(get_db)):
    user_id = get_user_id(token)
    item = db.query(KBEducation).filter(KBEducation.id == id, KBEducation.user_id == user_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(item)
    db.commit()
    return {"message": "Deleted"}

# --- Projects ---

@router.get("/projects")
def get_projects(token: str, db: Session = Depends(get_db)):
    user_id = get_user_id(token)
    items = db.query(KBProject).filter(KBProject.user_id == user_id).all()
    return [exclude_embedding(i) for i in items]

@router.post("/projects")
def add_project(data: ProjectIn, token: str, db: Session = Depends(get_db)):
    user_id = get_user_id(token)

    from app.services.embeddings import generate_embedding, build_project_text
    text = build_project_text(
        title=data.title,
        description=data.description,
        technologies=data.technologies or "",
        role=data.role or "",
        outcomes=data.outcomes or "",
        domain=data.domain or ""
    )
    embedding = generate_embedding(text)

    new = KBProject(user_id=user_id, embedding=embedding, **data.model_dump())
    db.add(new)
    db.commit()
    db.refresh(new)
    return exclude_embedding(new)

@router.delete("/projects/{id}")
def delete_project(id: int, token: str, db: Session = Depends(get_db)):
    user_id = get_user_id(token)
    item = db.query(KBProject).filter(KBProject.id == id, KBProject.user_id == user_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(item)
    db.commit()
    return {"message": "Deleted"}

# --- Experience ---

@router.get("/experience")
def get_experience(token: str, db: Session = Depends(get_db)):
    user_id = get_user_id(token)
    items = db.query(KBExperience).filter(KBExperience.user_id == user_id).all()
    return [exclude_embedding(i) for i in items]

@router.post("/experience")
def add_experience(data: ExperienceIn, token: str, db: Session = Depends(get_db)):
    user_id = get_user_id(token)

    from app.services.embeddings import generate_embedding, build_experience_text
    text = build_experience_text(
        company=data.company,
        role=data.role,
        responsibilities=data.responsibilities or "",
        technologies=data.technologies or ""
    )
    embedding = generate_embedding(text)

    new = KBExperience(user_id=user_id, embedding=embedding, **data.model_dump())
    db.add(new)
    db.commit()
    db.refresh(new)
    return exclude_embedding(new)

@router.delete("/experience/{id}")
def delete_experience(id: int, token: str, db: Session = Depends(get_db)):
    user_id = get_user_id(token)
    item = db.query(KBExperience).filter(KBExperience.id == id, KBExperience.user_id == user_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(item)
    db.commit()
    return {"message": "Deleted"}

# --- Skills ---

@router.get("/skills")
def get_skills(token: str, db: Session = Depends(get_db)):
    user_id = get_user_id(token)
    return db.query(KBSkill).filter(KBSkill.user_id == user_id).all()

@router.post("/skills")
def add_skill(data: SkillIn, token: str, db: Session = Depends(get_db)):
    user_id = get_user_id(token)
    new = KBSkill(user_id=user_id, **data.model_dump())
    db.add(new)
    db.commit()
    db.refresh(new)
    return new

@router.delete("/skills/{id}")
def delete_skill(id: int, token: str, db: Session = Depends(get_db)):
    user_id = get_user_id(token)
    item = db.query(KBSkill).filter(KBSkill.id == id, KBSkill.user_id == user_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(item)
    db.commit()
    return {"message": "Deleted"}

# --- Certifications ---

@router.get("/certifications")
def get_certifications(token: str, db: Session = Depends(get_db)):
    user_id = get_user_id(token)
    items = db.query(KBCertification).filter(KBCertification.user_id == user_id).all()
    return [exclude_embedding(i) for i in items]

@router.post("/certifications")
def add_certification(data: CertificationIn, token: str, db: Session = Depends(get_db)):
    user_id = get_user_id(token)

    from app.services.embeddings import generate_embedding, build_certification_text
    text = build_certification_text(
        name=data.name,
        issuer=data.issuer or "",
        skills_covered=data.skills_covered or ""
    )
    embedding = generate_embedding(text)

    new = KBCertification(user_id=user_id, embedding=embedding, **data.model_dump())
    db.add(new)
    db.commit()
    db.refresh(new)
    return exclude_embedding(new)

@router.delete("/certifications/{id}")
def delete_certification(id: int, token: str, db: Session = Depends(get_db)):
    user_id = get_user_id(token)
    item = db.query(KBCertification).filter(KBCertification.id == id, KBCertification.user_id == user_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(item)
    db.commit()
    return {"message": "Deleted"}

# --- Achievements ---

@router.get("/achievements")
def get_achievements(token: str, db: Session = Depends(get_db)):
    user_id = get_user_id(token)
    items = db.query(KBAchievement).filter(KBAchievement.user_id == user_id).all()
    return [exclude_embedding(i) for i in items]

@router.post("/achievements")
def add_achievement(data: AchievementIn, token: str, db: Session = Depends(get_db)):
    user_id = get_user_id(token)

    from app.services.embeddings import generate_embedding, build_achievement_text
    text = build_achievement_text(
        title=data.title,
        description=data.description or ""
    )
    embedding = generate_embedding(text)

    new = KBAchievement(user_id=user_id, embedding=embedding, **data.model_dump())
    db.add(new)
    db.commit()
    db.refresh(new)
    return exclude_embedding(new)

@router.delete("/achievements/{id}")
def delete_achievement(id: int, token: str, db: Session = Depends(get_db)):
    user_id = get_user_id(token)
    item = db.query(KBAchievement).filter(KBAchievement.id == id, KBAchievement.user_id == user_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(item)
    db.commit()
    return {"message": "Deleted"}