from sqlalchemy.orm import Session
from app.models.knowledge_base import (
    KBProject, KBExperience, KBSkill,
    KBCertification, KBAchievement
)
from app.services.embeddings import generate_embedding
from rank_bm25 import BM25Okapi
import re

def tokenize(text: str) -> list:
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    return [w for w in text.split() if len(w) > 2]

def cosine_similarity(a: list, b: list) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x ** 2 for x in a) ** 0.5
    norm_b = sum(x ** 2 for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)

def extract_jd_keywords(jd_text: str) -> set:
    tokens = tokenize(jd_text)
    stopwords = {
        "and", "or", "the", "a", "an", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "are", "was", "were", "be",
        "have", "has", "had", "will", "would", "could", "should", "you",
        "we", "our", "your", "they", "this", "that", "these", "those",
        "must", "able", "work", "good", "also", "well", "can", "not"
    }
    return {t for t in tokens if t not in stopwords and len(t) > 2}

def rule_based_boost(item_text: str, jd_keywords: set, technologies: str = "") -> float:
    boost = 0.0
    item_tokens = set(tokenize(item_text))
    tech_tokens = set(tokenize(technologies)) if technologies else set()

    # Exact keyword match boost
    exact_matches = item_tokens & jd_keywords
    boost += min(len(exact_matches) * 0.03, 0.15)

    # Technology match boost
    tech_matches = tech_tokens & jd_keywords
    boost += min(len(tech_matches) * 0.04, 0.10)

    return boost

def retrieve_and_rank(user_id: int, jd_text: str, db: Session) -> dict:
    # Generate JD embedding
    jd_embedding = generate_embedding(jd_text)
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
        project_texts = []
        for p in projects:
            text = f"{p.title} {p.description or ''} {p.technologies or ''} {p.role or ''} {p.outcomes or ''} {p.domain or ''}"
            project_texts.append(tokenize(text))

        bm25 = BM25Okapi(project_texts)
        bm25_scores = bm25.get_scores(tokenize(jd_text))
        max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1

        scored_projects = []
        for i, p in enumerate(projects):
            if p.embedding is None:
                continue
            vector_score = cosine_similarity(jd_embedding, list(p.embedding))
            bm25_score = bm25_scores[i] / max_bm25
            item_text = f"{p.title} {p.description or ''} {p.outcomes or ''}"
            boost = rule_based_boost(item_text, jd_keywords, p.technologies or "")
            final_score = (0.5 * vector_score) + (0.3 * bm25_score) + (0.2 * boost)
            scored_projects.append((final_score, p))

        scored_projects.sort(key=lambda x: x[0], reverse=True)
        results["projects"] = [
            {**{c.name: getattr(p, c.name) for c in p.__table__.columns if c.name != "embedding"}, "score": round(score, 3)}
            for score, p in scored_projects[:3]
        ]

    # --- Experience ---
    experiences = db.query(KBExperience).filter(KBExperience.user_id == user_id).all()
    if experiences:
        exp_texts = []
        for e in experiences:
            text = f"{e.company} {e.role} {e.responsibilities or ''} {e.technologies or ''}"
            exp_texts.append(tokenize(text))

        bm25 = BM25Okapi(exp_texts)
        bm25_scores = bm25.get_scores(tokenize(jd_text))
        max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1

        scored_exp = []
        for i, e in enumerate(experiences):
            if e.embedding is None:
                continue
            vector_score = cosine_similarity(jd_embedding, list(e.embedding))
            bm25_score = bm25_scores[i] / max_bm25
            item_text = f"{e.role} {e.responsibilities or ''}"
            boost = rule_based_boost(item_text, jd_keywords, e.technologies or "")
            final_score = (0.5 * vector_score) + (0.3 * bm25_score) + (0.2 * boost)
            scored_exp.append((final_score, e))

        scored_exp.sort(key=lambda x: x[0], reverse=True)
        results["experience"] = [
            {**{c.name: getattr(e, c.name) for c in e.__table__.columns if c.name != "embedding"}, "score": round(score, 3)}
            for score, e in scored_exp[:2]
        ]

    # --- Certifications ---
    certifications = db.query(KBCertification).filter(KBCertification.user_id == user_id).all()
    if certifications:
        cert_texts = []
        for c in certifications:
            text = f"{c.name} {c.issuer or ''} {c.skills_covered or ''}"
            cert_texts.append(tokenize(text))

        bm25 = BM25Okapi(cert_texts)
        bm25_scores = bm25.get_scores(tokenize(jd_text))
        max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1

        scored_certs = []
        for i, c in enumerate(certifications):
            if c.embedding is None:
                continue
            vector_score = cosine_similarity(jd_embedding, list(c.embedding))
            bm25_score = bm25_scores[i] / max_bm25
            item_text = f"{c.name} {c.skills_covered or ''}"
            boost = rule_based_boost(item_text, jd_keywords)
            final_score = (0.5 * vector_score) + (0.3 * bm25_score) + (0.2 * boost)
            scored_certs.append((final_score, c))

        scored_certs.sort(key=lambda x: x[0], reverse=True)
        results["certifications"] = [
            {**{col.name: getattr(c, col.name) for col in c.__table__.columns if col.name != "embedding"}, "score": round(score, 3)}
            for score, c in scored_certs
            if score > 0.2
        ]

    # --- Achievements ---
    achievements = db.query(KBAchievement).filter(KBAchievement.user_id == user_id).all()
    if achievements:
        ach_texts = []
        for a in achievements:
            text = f"{a.title} {a.description or ''}"
            ach_texts.append(tokenize(text))

        bm25 = BM25Okapi(ach_texts)
        bm25_scores = bm25.get_scores(tokenize(jd_text))
        max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1

        scored_ach = []
        for i, a in enumerate(achievements):
            if a.embedding is None:
                continue
            vector_score = cosine_similarity(jd_embedding, list(a.embedding))
            bm25_score = bm25_scores[i] / max_bm25
            item_text = f"{a.title} {a.description or ''}"
            boost = rule_based_boost(item_text, jd_keywords)
            final_score = (0.5 * vector_score) + (0.3 * bm25_score) + (0.2 * boost)
            scored_ach.append((final_score, a))

        scored_ach.sort(key=lambda x: x[0], reverse=True)
        results["achievements"] = [
            {**{c.name: getattr(a, c.name) for c in a.__table__.columns if c.name != "embedding"}, "score": round(score, 3)}
            for score, a in scored_ach
            if score > 0.2
        ]

    # --- Skills (all skills, filtered by JD keywords) ---
    skills = db.query(KBSkill).filter(KBSkill.user_id == user_id).all()
    jd_text_lower = jd_text.lower()
    relevant_skills = [s for s in skills if s.name.lower() in jd_text_lower]
    all_skills = skills if not relevant_skills else relevant_skills
    results["skills"] = [{"id": s.id, "category": s.category, "name": s.name} for s in all_skills]

    return results