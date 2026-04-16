from pathlib import Path

import markdown
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML, CSS

from generate_personalized_cover import build_cover

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"])
)


class CoverRequest(BaseModel):
    name: str
    birth_date: str
    birth_time: str
    birth_place: str
    prepared_date: str


class PDFRequest(BaseModel):
    cover_url: HttpUrl
    reading_text: str


def markdown_to_html(md_text: str) -> str:
    return markdown.markdown(
        md_text,
        extensions=["extra", "nl2br", "sane_lists"]
    )


def build_final_pdf_file(cover_url: str, html_content: str, output_path: Path) -> None:
    template = jinja_env.get_template("reading.html")
    full_html = template.render(
        cover_url=cover_url,
        content=html_content
    )

    css_path = STATIC_DIR / "styles.css"

    HTML(
        string=full_html,
        base_url=str(BASE_DIR)
    ).write_pdf(
        target=str(output_path),
        stylesheets=[CSS(filename=str(css_path))]
    )


@app.post("/generate-cover")
def generate_cover(req: CoverRequest):
    cover_path = BASE_DIR / "cover.png"
    output_path = Path("/tmp/cover.png")

    build_cover(
        cover_path=cover_path,
        output_path=output_path,
        name=req.name,
        birth_date=req.birth_date,
        birth_time=req.birth_time,
        birth_place=req.birth_place,
        prepared_date=req.prepared_date,
    )

    return FileResponse(
        output_path,
        media_type="image/png",
        filename="cover.png"
    )


@app.post("/generate-pdf")
def generate_pdf(payload: PDFRequest):
    try:
        html_content = markdown_to_html(payload.reading_text)
        output_path = Path("/tmp/final-reading.pdf")

        build_final_pdf_file(
            cover_url=str(payload.cover_url),
            html_content=html_content,
            output_path=output_path
        )

        return FileResponse(
            path=output_path,
            media_type="application/pdf",
            filename="final-reading.pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
