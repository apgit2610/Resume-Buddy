from sentence_transformers import SentenceTransformer
from typing import List

# Load model once when the module is imported
model = SentenceTransformer('all-MiniLM-L6-v2')

def generate_embedding(text: str) -> List[float]:
    """Generate embedding for a single text string."""
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()

def build_project_text(title: str, description: str, technologies: str = "", role: str = "", outcomes: str = "", domain: str = "") -> str:
    """Combine project fields into a single text for embedding."""
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
    """Combine experience fields into a single text for embedding."""
    parts = [f"Company: {company}", f"Role: {role}"]
    if responsibilities:
        parts.append(f"Responsibilities: {responsibilities}")
    if technologies:
        parts.append(f"Technologies: {technologies}")
    return " | ".join(parts)

def build_certification_text(name: str, issuer: str = "", skills_covered: str = "") -> str:
    """Combine certification fields into a single text for embedding."""
    parts = [f"Certification: {name}"]
    if issuer:
        parts.append(f"Issuer: {issuer}")
    if skills_covered:
        parts.append(f"Skills: {skills_covered}")
    return " | ".join(parts)

def build_achievement_text(title: str, description: str = "") -> str:
    """Combine achievement fields into a single text for embedding."""
    parts = [f"Achievement: {title}"]
    if description:
        parts.append(f"Description: {description}")
    return " | ".join(parts)