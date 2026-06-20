from sqlalchemy.orm import Session
from app.models.knowledge_base import (
    KBProject, KBExperience, KBSkill,
    KBCertification, KBAchievement
)
from rank_bm25 import BM25Okapi
import re
import math

def tokenize(text: str) -> list:
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    return [w for w in text.split() if len(w) > 2]

def normalize_bm25(raw_score: float) -> float:
    k = 6.0
    return 1 - math.exp(-raw_score / k)

def extract_jd_keywords(jd_text: str) -> set:
    tokens = tokenize(jd_text)
    stopwords = {
        "and", "or", "the", "a", "an", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "are", "was", "were", "be",
        "have", "has", "had", "will", "would", "could", "should", "you",
        "we", "our", "your", "they", "this", "that", "these", "those",
        "must", "able", "work", "good", "also", "well", "can", "not",
        "using", "real", "world", "into", "them", "design", "build",
        "develop", "solve", "solutions", "applications", "environments",
        "capabilities", "problems", "platforms"
    }
    return {t for t in tokens if t not in stopwords and len(t) > 2}

def rule_based_boost(item_text: str, jd_keywords: set, technologies: str = "") -> float:
    boost = 0.0
    item_tokens = set(tokenize(item_text))
    tech_tokens = set(tokenize(technologies)) if technologies else set()
    exact_matches = item_tokens & jd_keywords
    boost += min(len(exact_matches) * 0.025, 0.10)
    tech_matches = tech_tokens & jd_keywords
    boost += min(len(tech_matches) * 0.10, 0.40)
    return min(boost, 1.0)

def score_items_bm25(items, build_text_fn, get_tech_fn, jd_text, jd_keywords):
    if not items:
        return []

    item_texts = [tokenize(build_text_fn(i)) for i in items]
    bm25 = BM25Okapi(item_texts)
    bm25_raw_scores = bm25.get_scores(tokenize(jd_text))

    scored = []
    for i, item in enumerate(items):
        bm25_score = normalize_bm25(bm25_raw_scores[i])
        boost = rule_based_boost(
            build_text_fn(item),
            jd_keywords,
            get_tech_fn(item)
        )
        # BM25 only — no vector similarity
        final_score = (0.60 * bm25_score) + (0.40 * boost)
        scored.append((final_score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored

def retrieve_and_rank(user_id: int, jd_text: str, db: Session) -> dict:
    jd_keywords = extract_jd_keywords(jd_text)

    results = {
        "projects": [],
        "experience": [],
        "certifications": [],
        "achievements": [],
        "skills": []
    }

    # --- Projects ---
    projects = db.query(KBProject).filter(KBProject.user_id == user_id).all()
    if projects:
        scored = score_items_bm25(
            projects,
            lambda p: f"{p.title} {p.description or ''} {p.technologies or ''} {p.role or ''} {p.outcomes or ''} {p.domain or ''}",
            lambda p: p.technologies or "",
            jd_text,
            jd_keywords
        )
        results["projects"] = [
            {**{c.name: getattr(p, c.name) for c in p.__table__.columns if c.name != "embedding"}, "score": round(score, 3)}
            for score, p in scored
        ]

    # --- Experience ---
    experiences = db.query(KBExperience).filter(KBExperience.user_id == user_id).all()
    if experiences:
        scored = score_items_bm25(
            experiences,
            lambda e: f"{e.company} {e.role} {e.responsibilities or ''} {e.technologies or ''}",
            lambda e: e.technologies or "",
            jd_text,
            jd_keywords
        )
        results["experience"] = [
            {**{c.name: getattr(e, c.name) for c in e.__table__.columns if c.name != "embedding"}, "score": round(score, 3)}
            for score, e in scored[:2]
        ]

    # --- Certifications ---
    certifications = db.query(KBCertification).filter(KBCertification.user_id == user_id).all()
    if certifications:
        scored = score_items_bm25(
            certifications,
            lambda c: f"{c.name} {c.issuer or ''} {c.skills_covered or ''}",
            lambda c: "",
            jd_text,
            jd_keywords
        )
        results["certifications"] = [
            {**{col.name: getattr(c, col.name) for col in c.__table__.columns if col.name != "embedding"}, "score": round(score, 3)}
            for score, c in scored
            if score > 0.1
        ]

    # --- Achievements ---
    achievements = db.query(KBAchievement).filter(KBAchievement.user_id == user_id).all()
    if achievements:
        scored = score_items_bm25(
            achievements,
            lambda a: f"{a.title} {a.description or ''}",
            lambda a: "",
            jd_text,
            jd_keywords
        )
        results["achievements"] = [
            {**{c.name: getattr(a, c.name) for c in a.__table__.columns if c.name != "embedding"}, "score": round(score, 3)}
            for score, a in scored
            if score > 0.1
        ]

    # --- Skills ---
    skills = db.query(KBSkill).filter(KBSkill.user_id == user_id).all()
    jd_text_lower = jd_text.lower()
    jd_tokens = set(tokenize(jd_text))

    def skill_relevance(skill):
        name_lower = skill.name.lower()
        name_tokens = set(tokenize(skill.name))
        if name_lower in jd_text_lower:
            return 0
        if name_tokens & jd_tokens:
            return 1
        return 2

    skills_sorted = sorted(skills, key=skill_relevance)
    results["skills"] = [{"id": s.id, "category": s.category, "name": s.name} for s in skills_sorted]

    return results