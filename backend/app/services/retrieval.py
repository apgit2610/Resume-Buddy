from sqlalchemy.orm import Session
from app.models.knowledge_base import (
    KBProject, KBExperience, KBSkill,
    KBCertification, KBAchievement
)
from app.services.embeddings import generate_embedding
from rank_bm25 import BM25Okapi
import re
import math

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

def normalize_bm25(raw_score: float) -> float:
    """
    Convert a raw BM25 score to a 0-1 range using a fixed saturation curve,
    instead of dividing by the max score in the current corpus.
    Dividing by corpus-max makes scores relative to whatever else happens
    to be in the knowledge base (unstable with small corpora) rather than
    reflecting absolute match quality. This uses 1 - e^(-score/k), which
    saturates smoothly: a raw BM25 of ~6-8 (a strong real match) lands
    around 0.7-0.85, while a raw score of ~1-2 (a couple incidental word
    overlaps) stays low, around 0.15-0.3.
    """
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

    # Exact keyword match boost (general text overlap)
    exact_matches = item_tokens & jd_keywords
    boost += min(len(exact_matches) * 0.025, 0.10)

    # Technology match boost — this is the strongest real signal.
    # If the JD explicitly names a tool/tech and the item's tech stack
    # contains it, that's near-certain relevance (e.g. "TensorFlow" in
    # both), so weight it more heavily than generic word overlap.
    tech_matches = tech_tokens & jd_keywords
    boost += min(len(tech_matches) * 0.10, 0.40)

    return min(boost, 1.0)

def score_items(items, build_text_fn, embed_text_fn, jd_text, jd_embedding, jd_keywords):
    """
    Shared scoring routine for projects/experience/certifications/achievements.
    Returns list of (final_score, item) sorted descending.
    """
    if not items:
        return []

    item_texts = [tokenize(build_text_fn(i)) for i in items]
    bm25 = BM25Okapi(item_texts)
    bm25_raw_scores = bm25.get_scores(tokenize(jd_text))

    scored = []
    for i, item in enumerate(items):
        if item.embedding is None:
            continue
        vector_score = cosine_similarity(jd_embedding, list(item.embedding))
        bm25_score = normalize_bm25(bm25_raw_scores[i])
        boost = rule_based_boost(
            embed_text_fn(item)[0],
            jd_keywords,
            embed_text_fn(item)[1]
        )
        # Weights: vector similarity is the most reliable signal (captures
        # semantic/domain match even with no exact word overlap), BM25
        # catches exact phrasing, and the rule boost rewards explicit
        # tech-stack matches which are the strongest deterministic signal.
        final_score = (0.55 * vector_score) + (0.20 * bm25_score) + (0.25 * boost)
        scored.append((final_score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored

def retrieve_and_rank(user_id: int, jd_text: str, db: Session) -> dict:
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
        def build_text(p):
            return f"{p.title} {p.description or ''} {p.technologies or ''} {p.role or ''} {p.outcomes or ''} {p.domain or ''}"

        def embed_text(p):
            item_text = f"{p.title} {p.description or ''} {p.outcomes or ''}"
            return (item_text, p.technologies or "")

        scored = score_items(projects, build_text, embed_text, jd_text, jd_embedding, jd_keywords)
        results["projects"] = [
            {**{c.name: getattr(p, c.name) for c in p.__table__.columns if c.name != "embedding"}, "score": round(score, 3)}
            for score, p in scored
        ]

    # --- Experience ---
    experiences = db.query(KBExperience).filter(KBExperience.user_id == user_id).all()
    if experiences:
        def build_text(e):
            return f"{e.company} {e.role} {e.responsibilities or ''} {e.technologies or ''}"

        def embed_text(e):
            return (f"{e.role} {e.responsibilities or ''}", e.technologies or "")

        scored = score_items(experiences, build_text, embed_text, jd_text, jd_embedding, jd_keywords)
        results["experience"] = [
            {**{c.name: getattr(e, c.name) for c in e.__table__.columns if c.name != "embedding"}, "score": round(score, 3)}
            for score, e in scored[:2]
        ]

    # --- Certifications ---
    certifications = db.query(KBCertification).filter(KBCertification.user_id == user_id).all()
    if certifications:
        def build_text(c):
            return f"{c.name} {c.issuer or ''} {c.skills_covered or ''}"

        def embed_text(c):
            return (f"{c.name} {c.skills_covered or ''}", "")

        scored = score_items(certifications, build_text, embed_text, jd_text, jd_embedding, jd_keywords)
        results["certifications"] = [
            {**{col.name: getattr(c, col.name) for col in c.__table__.columns if col.name != "embedding"}, "score": round(score, 3)}
            for score, c in scored
            if score > 0.2
        ]

    # --- Achievements ---
    achievements = db.query(KBAchievement).filter(KBAchievement.user_id == user_id).all()
    if achievements:
        def build_text(a):
            return f"{a.title} {a.description or ''}"

        def embed_text(a):
            return (f"{a.title} {a.description or ''}", "")

        scored = score_items(achievements, build_text, embed_text, jd_text, jd_embedding, jd_keywords)
        results["achievements"] = [
            {**{c.name: getattr(a, c.name) for c in a.__table__.columns if c.name != "embedding"}, "score": round(score, 3)}
            for score, a in scored
            if score > 0.2
        ]

    # --- Skills (all included, JD-relevant ones first) ---
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