# app/services/pdf_generator.py
import html
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright

TEMPLATE_DIR = Path(__file__).parent.parent / "templates"

_jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html"]),  # escapes user input by default — do not disable
)


class PdfGenerationError(Exception):
    """Raised when HTML rendering or PDF conversion fails."""
    pass


def _clean_link(raw: str) -> str:
    """Strips protocol/www for display text, mirroring the frontend's cleanDisplay()."""
    if not raw:
        return ""
    stripped = raw.strip()
    for prefix in ("https://", "http://", "www."):
        if stripped.lower().startswith(prefix):
            stripped = stripped[len(prefix):]
    return stripped


def _as_href(raw: str) -> str:
    """Ensures a value has a scheme before being used as a href."""
    stripped = raw.strip()
    return stripped if stripped.startswith("http") else f"https://{stripped}"


def _bullets(raw: str) -> list[str]:
    """Splits a textarea-style newline string into individual bullet lines."""
    if not raw:
        return []
    return [line.strip() for line in raw.split("\n") if line.strip()]


def render_resume_html(resume_data: dict) -> str:
    """
    Builds the final resume HTML server-side from validated resume_data
    (the same JSONB snapshot stored on the Order at checkout time).
    This mirrors the client's renderPreview() logic in script.js, but
    runs entirely on the server so the output PDF is never dependent on
    anything the browser sent after payment.
    """
    contact = resume_data.get("contact", {})

    context = {
        "full_name": contact.get("fullName", ""),
        "email": contact.get("email", ""),
        "phone": contact.get("phone", ""),
        "location": contact.get("location", ""),
        "linkedin": contact.get("linkedin", ""),
        "github": contact.get("github", ""),
        "portfolio": contact.get("portfolio", ""),
        "summary": resume_data.get("summary", ""),
        "education": resume_data.get("education", []),
        "experience": resume_data.get("experience", []),
        "projects": [
            {**p, "bullets": _bullets(p.get("bullets", ""))}
            for p in resume_data.get("projects", [])
        ],
        "skills": resume_data.get("skills", []),
        "leadership": [
            {**l, "bullets": _bullets(l.get("bullets", ""))}
            for l in resume_data.get("leadership", [])
        ],
        "coding_profiles": resume_data.get("coding_profiles", []),
        "interests": resume_data.get("interests", ""),
        "certifications": _bullets(resume_data.get("certifications", "")),
        "achievements": _bullets(resume_data.get("achievements", "")),
        "custom_sections": [
            {**c, "content": _bullets(c.get("content", ""))}
            for c in resume_data.get("custom_sections", [])
        ],
        "clean_link": _clean_link,
        "as_href": _as_href,
    }

    # Also fix up experience/education bullets, which are raw textarea strings too
    context["experience"] = [
        {**e, "bullets": _bullets(e.get("bullets", ""))}
        for e in context["experience"]
    ]

    template = _jinja_env.get_template("resume_template.html")
    try:
        return template.render(**context)
    except Exception as exc:
        raise PdfGenerationError(f"Failed to render resume HTML: {exc}") from exc


def generate_pdf_bytes(html_content: str) -> bytes:
    """
    Converts rendered HTML into PDF bytes using headless Chromium via
    Playwright. Runs synchronously and is meant to be called from a
    background task/worker, not directly inside a request handler.
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
            try:
                page = browser.new_page()
                page.set_content(html_content, wait_until="networkidle")
                pdf_bytes = page.pdf(
                    format="Letter",
                    margin={"top": "0.5in", "bottom": "0.5in", "left": "0.5in", "right": "0.5in"},
                    print_background=True,
                )
                return pdf_bytes
            finally:
                browser.close()
    except Exception as exc:
        raise PdfGenerationError(f"Failed to generate PDF: {exc}") from exc


def generate_resume_pdf(resume_data: dict) -> bytes:
    """Convenience wrapper: resume_data dict -> final PDF bytes, in one call."""
    resume_html = render_resume_html(resume_data)
    return generate_pdf_bytes(resume_html)