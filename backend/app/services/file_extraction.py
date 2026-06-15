import io
from fastapi import UploadFile, HTTPException


def extract_text_from_file(file: UploadFile) -> str:
    filename = file.filename or ""
    content = file.file.read()

    if filename.lower().endswith(".pdf"):
        return extract_text_from_pdf(content)
    elif filename.lower().endswith(".docx"):
        return extract_text_from_docx(content)
    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload a PDF or DOCX file."
        )


def extract_text_from_pdf(content: bytes) -> str:
    import fitz  # PyMuPDF

    text = ""
    doc = fitz.open(stream=content, filetype="pdf")
    for page in doc:
        text += page.get_text()
    doc.close()
    return text.strip()


def extract_text_from_docx(content: bytes) -> str:
    from docx import Document

    doc = Document(io.BytesIO(content))
    text = "\n".join(p.text for p in doc.paragraphs)
    return text.strip()