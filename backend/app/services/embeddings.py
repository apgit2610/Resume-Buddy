from typing import List

_model = None

def get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            print(f"Warning: Could not load embedding model: {e}")
            return None
    return _model

def generate_embedding(text: str) -> List[float]:
    model = get_model()
    if model is None:
        return []
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()

def build_project_text(title: str, description: str, technologies: str = "", role: str = "", outcomes: str = "", domain: str = "") -> str:
    parts = [f"Project: {title}"]
    if description:
        parts.append(f"Description: {description}")
    if technologies:
        parts.append(f"Technologies: {technologies}")
    if role:
        parts.append(f"Role: {role}")
    if outcomes:
        parts.append(f"Outcomes: {outcomes}")
    if domain:
        parts.append(f"Domain: {domain}")
    return " | ".join(parts)

def build_experience_text(company: str, role: str, responsibilities: str = "", technologies: str = "") -> str:
    parts = [f"Company: {company}", f"Role: {role}"]
    if responsibilities:
        parts.append(f"Responsibilities: {responsibilities}")
    if technologies:
        parts.append(f"Technologies: {technologies}")
    return " | ".join(parts)

def build_certification_text(name: str, issuer: str = "", skills_covered: str = "") -> str:
    parts = [f"Certification: {name}"]
    if issuer:
        parts.append(f"Issuer: {issuer}")
    if skills_covered:
        parts.append(f"Skills: {skills_covered}")
    return " | ".join(parts)

def build_achievement_text(title: str, description: str = "") -> str:
    parts = [f"Achievement: {title}"]
    if description:
        parts.append(f"Description: {description}")
    return " | ".join(parts)