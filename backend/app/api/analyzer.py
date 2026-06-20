from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import re
import io

router = APIRouter()

# ─── Tech skill extraction ────────────────────────────────────────────────────

# Common tech skills, languages, frameworks, tools
TECH_SKILLS = {
    # Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "kotlin", "swift", "scala", "r", "matlab", "bash", "shell", "php", "ruby",
    "dart", "elixir", "haskell", "lua", "perl",

    # ML / AI
    "tensorflow", "pytorch", "keras", "scikit-learn", "sklearn", "xgboost",
    "lightgbm", "catboost", "hugging face", "transformers", "langchain",
    "openai", "llm", "nlp", "cv", "bert", "gpt", "stable diffusion",
    "pandas", "numpy", "scipy", "matplotlib", "seaborn", "plotly",
    "jupyter", "colab", "wandb", "mlflow", "ray", "dask",

    # Web frameworks
    "react", "nextjs", "next.js", "vuejs", "vue.js", "angular", "svelte",
    "fastapi", "django", "flask", "express", "nestjs", "nest.js", "spring",
    "laravel", "rails", "asp.net", "fastify",

    # Databases
    "postgresql", "mysql", "sqlite", "mongodb", "redis", "elasticsearch",
    "cassandra", "dynamodb", "neo4j", "firebase", "supabase", "pinecone",
    "qdrant", "weaviate", "chroma", "pgvector",

    # Cloud / DevOps
    "aws", "gcp", "azure", "docker", "kubernetes", "terraform", "ansible",
    "jenkins", "github actions", "circleci", "gitlab ci", "helm", "airflow",
    "kafka", "rabbitmq", "celery", "nginx", "linux",

    # Tools
    "git", "github", "gitlab", "bitbucket", "jira", "confluence", "figma",
    "postman", "graphql", "rest", "grpc", "websocket",

    # Concepts
    "machine learning", "deep learning", "natural language processing",
    "computer vision", "reinforcement learning", "transfer learning",
    "data engineering", "data science", "mlops", "devops", "ci/cd",
    "microservices", "system design", "distributed systems",
    "agile", "scrum", "tdd", "api design", "rag", "vector search",
}

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "we", "you", "he", "she", "they", "it", "i",
    "my", "your", "our", "their", "this", "that", "these", "those",
    "all", "any", "both", "each", "more", "most", "other", "some", "no",
    "not", "only", "same", "so", "than", "too", "very", "just", "as", "if",
    "also", "well", "can", "must", "able", "good", "used", "use", "using",
    "work", "working", "ensure", "including", "required", "ideal",
    "candidate", "position", "role", "team", "company", "join", "looking",
    "seeking", "responsible", "responsibilities", "experience", "knowledge",
    "strong", "excellent", "proficient", "familiarity", "understanding",
    "ability", "skills", "skill", "plus", "preferred", "bonus",
}

# Generic JD/corporate-speak that isn't meaningful to match against a resume.
FILLER_WORDS = {
    "innovative", "passionate", "dynamic", "growing", "growth",
    "environment", "opportunity", "opportunities", "collaborative",
    "collaboration", "culture", "mission", "vision", "values",
    "diverse", "diversity", "inclusive", "inclusion", "equity",
    "benefits", "compensation", "salary", "competitive", "package",
    "remote", "hybrid", "onsite", "office", "flexible", "flexibility",
    "global", "world", "industry", "leading", "leader", "client",
    "clients", "customer", "customers", "stakeholders", "thrive",
    "thriving", "exciting", "impactful", "impact", "drive", "driven",
    "motivated", "communication", "interpersonal", "organization",
    "organizational", "mindset", "attitude", "year", "years", "month",
    "months", "level", "levels", "type", "types", "kind", "kinds",
    "various", "multiple", "wide", "range", "variety", "different",
    "current", "future", "term", "full", "part", "based", "across",
    "within", "into", "onto", "upon", "through", "throughout", "during",
    "while", "such", "regarding", "related", "relevant", "appropriate",
    "applicable", "potential", "possible", "additional", "overall",
    "general", "specific", "particular", "certain", "highly", "extremely",
    "deeply", "truly", "really", "currently", "previously", "recently",
    "please", "apply", "submit", "send", "contact", "email", "address",
    "great", "amazing", "fun", "love", "loves", "enjoy", "enjoys",
}

STRONG_ACTION_VERBS = {
    "achieved", "built", "created", "delivered", "designed", "developed",
    "engineered", "established", "implemented", "improved", "increased",
    "launched", "led", "managed", "optimized", "reduced", "scaled",
    "shipped", "solved", "spearheaded", "streamlined", "transformed",
    "automated", "architected", "deployed", "migrated", "integrated",
    "accelerated", "collaborated", "contributed", "generated", "published",
    "researched", "trained", "fine-tuned", "monitored", "maintained",
}

WEAK_PHRASES = [
    "responsible for", "helped with", "assisted in", "worked on",
    "involved in", "participated in", "was part of", "duties included",
    "tasked with",
]

REQUIRED_SECTIONS = [
    ("experience", ["experience", "work history", "employment"]),
    ("education", ["education", "academic", "degree", "university"]),
    ("skills", ["skills", "technical skills", "technologies"]),
    ("projects", ["projects", "project", "portfolio"]),
    ("contact", ["email", "phone", "linkedin", "@"]),
    ("summary", ["summary", "objective", "profile", "about"]),
]

# ─── Helpers ──────────────────────────────────────────────────────────────────

def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())

def stem(word: str) -> str:
    """Lightweight suffix-stripping stemmer to normalize word forms
    (e.g. 'developing'/'developed'/'develops' -> 'develop',
    'systems' -> 'system', 'technologies' -> 'technology')."""
    if len(word) <= 4:
        return word
    if word.endswith("ies"):
        return word[:-3] + "y"
    if word.endswith("ied"):
        return word[:-3] + "y"
    if word.endswith("ing"):
        s = word[:-3]
        if len(s) > 2 and s[-1] == s[-2] and s[-1] not in "aeiou":
            s = s[:-1]
        return s
    if word.endswith("ed") and not word.endswith("eed"):
        s = word[:-2]
        if len(s) > 2 and s[-1] == s[-2] and s[-1] not in "aeiou":
            s = s[:-1]
        return s
    if word.endswith("es") and not word.endswith("ses"):
        return word[:-2]
    if word.endswith("s") and not word.endswith("ss") and not word.endswith("us"):
        return word[:-1]
    return word

def _build_tech_skill_stems() -> set:
    """Stemmed tokens from every word in TECH_SKILLS, so phrases like
    'machine learning' exclude 'machine' and 'learning' from role keywords."""
    stems = set()
    for skill in TECH_SKILLS:
        for word in re.split(r"[^a-z0-9]+", skill):
            if word:
                stems.add(stem(word))
    return stems

TECH_SKILL_STEMS = _build_tech_skill_stems()

def extract_tech_skills(text: str) -> set:
    """Extract only recognized tech skills from text."""
    text_lower = normalize(text)
    found = set()

    # Match known multi-word and single-word tech skills
    for skill in TECH_SKILLS:
        # Use word boundary matching
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found.add(skill)

    return found

def extract_role_keywords(text: str) -> dict:
    """Extract meaningful role/domain keywords — not stopwords, not filler,
    not part of a tech-skill phrase, not single chars. Words are stemmed so
    different tenses/plurals (e.g. 'developing' vs 'developed') count as the
    same keyword. Returns {stem: representative_original_word}."""
    text_lower = normalize(text)
    clean = re.sub(r"[^\w\s]", " ", text_lower)
    tokens = clean.split()

    keywords: dict = {}
    for token in tokens:
        if (
            token in STOPWORDS
            or token in FILLER_WORDS
            or len(token) <= 3
            or token.isdigit()
        ):
            continue
        s = stem(token)
        if s in TECH_SKILL_STEMS:
            continue
        if s not in keywords:
            keywords[s] = token

    return keywords

def extract_text_from_pdf(file_bytes: bytes) -> str:
    import fitz
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_text_from_docx(file_bytes: bytes) -> str:
    from docx import Document
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join([para.text for para in doc.paragraphs])

# ─── Scorers ─────────────────────────────────────────────────────────────────

def score_tech_skills(resume: str, jd: str) -> dict:
    """Match actual tech skills between resume and JD."""
    resume_skills = extract_tech_skills(resume)
    jd_skills = extract_tech_skills(jd)

    if not jd_skills:
        return {
            "score": 50,
            "matched": [],
            "missing": [],
            "jd_total": 0,
            "matched_total": 0,
        }

    matched = resume_skills & jd_skills
    missing = jd_skills - resume_skills

    score = round((len(matched) / len(jd_skills)) * 100)
    score = min(score, 100)

    return {
        "score": score,
        "matched": sorted(matched),
        "missing": sorted(missing),
        "jd_total": len(jd_skills),
        "matched_total": len(matched),
    }

def score_role_keywords(resume: str, jd: str) -> dict:
    """Match domain/role keywords (non-tech but meaningful), using stemming
    to normalize word forms so e.g. 'developing' in the JD matches
    'developed' in the resume."""
    resume_kw = extract_role_keywords(resume)
    jd_kw = extract_role_keywords(jd)

    if not jd_kw:
        return {"score": 50, "matched": [], "missing": []}

    resume_stems = set(resume_kw.keys())
    jd_stems = set(jd_kw.keys())

    matched_stems = resume_stems & jd_stems
    missing_stems = jd_stems - resume_stems

    score = round((len(matched_stems) / len(jd_stems)) * 100)
    score = min(score, 100)

    # Display using the JD's own wording
    top_matched = sorted(
        (jd_kw[s] for s in matched_stems if len(jd_kw[s]) > 4),
        key=len, reverse=True
    )[:10]
    top_missing = sorted(
        (jd_kw[s] for s in missing_stems if len(jd_kw[s]) > 4),
        key=len, reverse=True
    )[:10]

    return {
        "score": score,
        "matched": top_matched,
        "missing": top_missing,
    }

def score_resume_quality(resume: str) -> dict:
    """Score resume content quality."""
    issues = []
    strengths = []

    words = resume.split()
    word_count = len(words)

    if word_count < 200:
        issues.append("Resume is too short — add more detail to experience and projects")
    elif word_count > 900:
        issues.append("Resume may be too long — aim for 1 page (under 800 words)")
    else:
        strengths.append(f"Good length ({word_count} words)")

    numbers = re.findall(r"\b\d+[%$x]?\b", resume)
    meaningful = [n for n in numbers if n not in {"0", "1", "2", "3"} and len(n) > 1]
    if len(meaningful) >= 4:
        strengths.append(f"Strong use of metrics ({len(meaningful)} data points)")
    elif len(meaningful) >= 1:
        issues.append("Add more quantifiable results (%, $, x improvement)")
    else:
        issues.append("No metrics found — add numbers to show impact (e.g. 'reduced latency by 40%')")

    resume_lower = resume.lower()
    found_verbs = [v for v in STRONG_ACTION_VERBS if v in resume_lower]
    if len(found_verbs) >= 6:
        strengths.append(f"Strong action verbs ({len(found_verbs)} found)")
    elif len(found_verbs) >= 3:
        issues.append("Use more strong action verbs (built, optimized, led, scaled…)")
    else:
        issues.append("Weak language — start bullets with action verbs (built, deployed, engineered…)")

    found_weak = [p for p in WEAK_PHRASES if p in resume_lower]
    if found_weak:
        issues.append(f"Weak phrase found: \"{found_weak[0]}\" — replace with action verb")

    score_parts = []
    score_parts.append(40 if 200 <= word_count <= 900 else 10)
    score_parts.append(35 if len(meaningful) >= 4 else (20 if len(meaningful) >= 1 else 0))
    score_parts.append(25 if len(found_verbs) >= 6 else (15 if len(found_verbs) >= 3 else 0))
    score = sum(score_parts)

    return {
        "score": score,
        "word_count": word_count,
        "strengths": strengths,
        "issues": issues,
        "metrics_count": len(meaningful),
        "action_verbs_count": len(found_verbs),
    }

def score_ats_essentials(resume: str) -> dict:
    resume_lower = resume.lower()
    checks = []

    has_email = bool(re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", resume))
    checks.append({"label": "Email address", "pass": has_email})

    has_phone = bool(re.search(r"[\+\(]?[\d\s\-\(\)]{7,15}", resume))
    checks.append({"label": "Phone number", "pass": has_phone})

    has_linkedin = "linkedin" in resume_lower
    checks.append({"label": "LinkedIn profile", "pass": has_linkedin})

    has_github = "github" in resume_lower
    checks.append({"label": "GitHub profile", "pass": has_github})

    pipe_count = resume.count("|")
    checks.append({"label": "ATS-safe formatting (no complex tables)", "pass": pipe_count <= 5})

    special = len(re.findall(r"[★●■▶◆]", resume))
    checks.append({"label": "No special characters that confuse ATS", "pass": special == 0})

    passed = sum(1 for c in checks if c["pass"])
    score = round((passed / len(checks)) * 100)

    return {"score": score, "checks": checks}

def score_sections(resume: str) -> dict:
    resume_lower = resume.lower()
    found = []
    missing = []

    for section_name, patterns in REQUIRED_SECTIONS:
        if any(p in resume_lower for p in patterns):
            found.append(section_name)
        else:
            missing.append(section_name)

    score = round((len(found) / len(REQUIRED_SECTIONS)) * 100)
    return {"score": score, "found": found, "missing": missing}

def overall_score(tech: int, role: int, quality: int, ats: int) -> int:
    return round(tech * 0.45 + role * 0.25 + quality * 0.20 + ats * 0.10)

def run_analysis(resume_text: str, jd_text: str) -> dict:
    tech = score_tech_skills(resume_text, jd_text)
    role = score_role_keywords(resume_text, jd_text)
    quality = score_resume_quality(resume_text)
    ats = score_ats_essentials(resume_text)
    sections = score_sections(resume_text)

    total = overall_score(tech["score"], role["score"], quality["score"], ats["score"])

    return {
        "overall_score": total,
        "breakdown": {
            "tech_skills_match": tech["score"],
            "role_keywords": role["score"],
            "resume_quality": quality["score"],
            "ats_essentials": ats["score"],
        },
        "tech_skills": {
            "matched": tech["matched"],
            "missing": tech["missing"],
            "jd_total": tech["jd_total"],
            "matched_total": tech["matched_total"],
        },
        "role_keywords": {
            "matched": role["matched"],
            "missing": role["missing"],
        },
        "quality": quality,
        "ats": ats,
        "sections": sections,
    }

# ─── Routes ──────────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    resume_text: str
    job_description: str

@router.post("/analyze-text")
def analyze_text(request: AnalyzeRequest):
    if not request.resume_text.strip() or not request.job_description.strip():
        raise HTTPException(status_code=400, detail="Both resume and job description are required")
    return run_analysis(request.resume_text, request.job_description)

@router.post("/analyze-file")
async def analyze_file(
    file: UploadFile = File(...),
    job_description: str = Form(...)
):
    file_bytes = await file.read()
    filename = file.filename or ""

    if filename.endswith(".pdf"):
        resume_text = extract_text_from_pdf(file_bytes)
    elif filename.endswith(".docx"):
        resume_text = extract_text_from_docx(file_bytes)
    else:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")

    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from file")

    return run_analysis(resume_text, job_description)

@router.post("/extract-text")
async def extract_text_endpoint(file: UploadFile = File(...)):
    file_bytes = await file.read()
    filename = file.filename or ""

    if filename.endswith(".pdf"):
        text = extract_text_from_pdf(file_bytes)
    elif filename.endswith(".docx"):
        text = extract_text_from_docx(file_bytes)
    else:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")

    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from file")

    return {"text": text}

# Backward compat
@router.post("/analyze")
def analyze_legacy(request: AnalyzeRequest):
    return run_analysis(request.resume_text, request.job_description)