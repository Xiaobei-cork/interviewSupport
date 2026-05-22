from pathlib import Path


def extract_text(file_path: Path, file_type: str) -> str:
    if file_type == "pdf":
        return _extract_pdf(file_path)
    return _extract_docx(file_path)


def _extract_pdf(path: Path) -> str:
    import pdfplumber

    text_parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
    return "\n".join(text_parts) or "（未能解析PDF文本，使用Mock分析）"


def _extract_docx(path: Path) -> str:
    from docx import Document

    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip()) or "（未能解析Word文本）"
