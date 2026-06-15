from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import re
import io

router = APIRouter()

class AnalyzeRequest(BaseModel):
    resume_text: str
    job_description: str

# ─── Known multi-word skills ──────────────────────────────────────────────────
KNOWN_SKILLS = {
    "machine learning", "deep learning", "natural language processing",
    "computer vision", "neural networks", "large language models",
    "reinforcement learning", "transfer learning", "feature engineering",
    "data science", "data engineering", "data analysis", "data pipeline",
    "big data", "data visualization", "business intelligence",
    "software engineering", "software development", "full stack",
    "front end", "back end", "web development", "mobile development",
    "system design", "distributed systems", "microservices",
    "rest api", "graphql", "grpc", "api design",
    "react native", "node js", "next js", "vue js", "angular",
    "spring boot", "django rest framework", "fast api",
    "continuous integration", "continuous deployment", "ci cd",
    "test driven development", "agile development", "scrum",
    "cloud computing", "cloud platforms", "cloud infrastructure",
    "amazon web services", "google cloud platform", "microsoft azure",
    "mlops", "devops", "site reliability", "platform engineering",
    "version control", "code review", "pair programming",
    "sql databases", "nosql databases", "relational databases",
    "object oriented programming", "functional programming",
    "cross functional", "cross functional teams", "product management",
}

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "we", "you", "he", "she",
    "they", "it", "i", "my", "your", "our", "their", "this", "that",
    "these", "those", "what", "which", "who", "how", "when", "where",
    "why", "all", "any", "both", "each", "few", "more", "most", "other",
    "some", "such", "no", "not", "only", "same", "so", "than", "too",
    "very", "just", "as", "if", "about", "above", "after", "before",
    "between", "into", "through", "during", "also", "while", "although",
    "because", "since", "unless", "must", "able", "good", "also", "well",
    "used", "use", "using", "work", "working", "works", "ensure", "ensure",
    "including", "include", "includes", "required", "require", "requires",
    "ideal", "candidate", "position", "role", "team", "company", "join",
    "looking", "seeking", "responsible", "responsibilities",
}

REQUIRED_SECTIONS = [
    ("experience", ["experience", "work history", "employment", "professional experience"]),
    ("education", ["education", "academic", "degree", "university", "college"]),
    ("skills", ["skills", "technical skills", "technologies", "competencies"]),
    ("projects", ["projects", "project", "portfolio", "work samples"]),
    ("contact", ["email", "phone", "linkedin", "github", "@"]),
    ("summary", ["summary", "objective", "profile", "about me", "overview"]),
]

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

# ─── Helpers ──────────────────────────────────────────────────────────────────

def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())

def extract_keywords(text: str) -> set:
    text_lower = normalize(text)
    found = set()

    # Known multi-word skills
    for skill in KNOWN_SKILLS:
        if skill in text_lower:
            found.add(skill)

    # Clean text for unigrams/bigrams
    clean = re.sub(r"[^\w\s]", " ", text_lower)
    tokens = [w for w in clean.split() if w not in STOPWORDS and len(w) > 2]

    found.update(tokens)

    # Bigrams
    for i in range(len(tokens) - 1):
        bigram = f"{tokens[i]} {tokens[i+1]}"
        if len(bigram) > 6:
            found.add(bigram)

    return found


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


# ─── Sub-scorers ──────────────────────────────────────────────────────────────

def score_keywords(resume: str, jd: str) -> dict:
    resume_kw = extract_keywords(resume)
    jd_kw = extract_keywords(jd)

    matched = resume_kw & jd_kw
    missing = jd_kw - resume_kw

    # Filter missing to meaningful ones
    top_missing_phrases = sorted(
        [k for k in missing if " " in k],
        key=len, reverse=True
    )[:10]
    top_missing_words = sorted(
        [k for k in missing if " " not in k and len(k) > 3],
        key=len, reverse=True
    )[:10]
    top_missing = (top_missing_phrases + top_missing_words)[:15]

    top_matched = sorted(
        [k for k in matched if len(k) > 3],
        key=len, reverse=True
    )[:20]

    score = round((len(matched) / len(jd_kw)) * 100) if jd_kw else 0
    score = min(score, 100)

    return {
        "score": score,
        "matched_keywords": top_matched,
        "missing_keywords": top_missing,
        "skill_gaps": top_missing_phrases[:8],
        "total_jd_keywords": len(jd_kw),
        "total_matched": len(matched),
    }


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
    return {
        "score": score,
        "found_sections": found,
        "missing_sections": missing,
    }


def score_content(resume: str) -> dict:
    issues = []
    strengths = []

    # Word count
    words = resume.split()
    word_count = len(words)
    if word_count < 200:
        issues.append("Resume is too short (under 200 words) — add more detail")
    elif word_count > 800:
        issues.append("Resume may be too long (over 800 words) — consider trimming")
    else:
        strengths.append(f"Good length ({word_count} words)")

    # Numbers/quantification
    numbers = re.findall(r"\b\d+[%$]?\b|\b[%$]\d+", resume)
    meaningful_numbers = [n for n in numbers if n not in {"1", "2", "3", "0"}]
    if len(meaningful_numbers) >= 3:
        strengths.append(f"Good use of metrics ({len(meaningful_numbers)} numbers found)")
    elif len(meaningful_numbers) == 1 or len(meaningful_numbers) == 2:
        issues.append("Add more quantifiable achievements (use numbers, %, $ values)")
    else:
        issues.append("No quantifiable metrics found — add numbers to show impact (e.g. 'reduced load time by 40%')")

    # Action verbs
    resume_lower = resume.lower()
    found_verbs = [v for v in STRONG_ACTION_VERBS if v in resume_lower]
    if len(found_verbs) >= 5:
        strengths.append(f"Strong action verbs used ({len(found_verbs)} found)")
    elif len(found_verbs) >= 2:
        issues.append("Use more strong action verbs (built, optimized, led, scaled…)")
    else:
        issues.append("Weak language detected — start bullet points with strong verbs (achieved, built, deployed, led…)")

    # Weak phrases
    found_weak = [p for p in WEAK_PHRASES if p in resume_lower]
    if found_weak:
        issues.append(f"Weak phrases found: \"{found_weak[0]}\" — replace with action verbs")

    score_parts = []
    score_parts.append(50 if 200 <= word_count <= 800 else (20 if word_count > 0 else 0))
    score_parts.append(30 if len(meaningful_numbers) >= 3 else (15 if len(meaningful_numbers) >= 1 else 0))
    score_parts.append(20 if len(found_verbs) >= 5 else (10 if len(found_verbs) >= 2 else 0))
    score = sum(score_parts)

    return {
        "score": score,
        "word_count": word_count,
        "strengths": strengths,
        "issues": issues,
        "metrics_count": len(meaningful_numbers),
        "action_verbs_found": len(found_verbs),
    }


def score_ats_essentials(resume: str) -> dict:
    resume_lower = resume.lower()
    checks = []

    # Email
    has_email = bool(re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", resume))
    checks.append({"label": "Email address", "pass": has_email})

    # Phone
    has_phone = bool(re.search(r"[\+\(]?[\d\s\-\(\)]{7,15}", resume))
    checks.append({"label": "Phone number", "pass": has_phone})

    # LinkedIn
    has_linkedin = "linkedin" in resume_lower
    checks.append({"label": "LinkedIn profile", "pass": has_linkedin})

    # GitHub (for tech roles)
    has_github = "github" in resume_lower
    checks.append({"label": "GitHub profile", "pass": has_github})

    # No tables/columns warning (heuristic: if lots of | characters)
    pipe_count = resume.count("|")
    has_tables = pipe_count > 5
    checks.append({"label": "No complex tables (ATS-safe formatting)", "pass": not has_tables})

    # No special characters overuse
    special = len(re.findall(r"[★●■▶◆]", resume))
    checks.append({"label": "No special characters that confuse ATS", "pass": special == 0})

    passed = sum(1 for c in checks if c["pass"])
    score = round((passed / len(checks)) * 100)

    return {
        "score": score,
        "checks": checks,
    }


def overall_score(kw_score: int, section_score: int, content_score: int, ats_score: int) -> int:
    return round(
        kw_score * 0.40 +
        section_score * 0.20 +
        content_score * 0.25 +
        ats_score * 0.15
    )


def run_analysis(resume_text: str, jd_text: str) -> dict:
    kw = score_keywords(resume_text, jd_text)
    sections = score_sections(resume_text)
    content = score_content(resume_text)
    ats = score_ats_essentials(resume_text)

    total = overall_score(kw["score"], sections["score"], content["score"], ats["score"])

    return {
        "overall_score": total,
        "breakdown": {
            "keyword_match": kw["score"],
            "sections": sections["score"],
            "content_quality": content["score"],
            "ats_essentials": ats["score"],
        },
        "keywords": {
            "matched": kw["matched_keywords"],
            "missing": kw["missing_keywords"],
            "skill_gaps": kw["skill_gaps"],
            "total_jd": kw["total_jd_keywords"],
            "total_matched": kw["total_matched"],
        },
        "sections": sections,
        "content": content,
        "ats": ats,
    }


# ─── Routes ───────────────────────────────────────────────────────────────────

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
        raise HTTPException(status_code=400, detail="Could not extract text from the file")

    return run_analysis(resume_text, job_description)


# Keep old endpoint for backward compat
@router.post("/analyze")
def analyze_legacy(request: AnalyzeRequest):
    return run_analysis(request.resume_text, request.job_description)