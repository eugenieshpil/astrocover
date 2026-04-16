from pathlib import Path
from io import BytesIO
import tempfile
import os

import requests
import markdown
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML, CSS
from pypdf import PdfReader, PdfWriter

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


def download_file(url: str) -> bytes:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.content


def markdown_to_html(md_text: str) -> str:
    return markdown.markdown(
        md_text,
        extensions=["extra", "nl2br", "sane_lists"]
    )


def render_body_pdf(html_content: str) -> bytes:
    template = jinja_env.get_template("reading.html")
    full_html = template.render(content=html_content)

    css_path = STATIC_DIR / "styles.css"
    pdf_bytes = HTML(
        string=full_html,
        base_url=str(BASE_DIR)
    ).write_pdf(
        stylesheets=[CSS(filename=str(css_path))]
    )
    return pdf_bytes


def image_to_single_page_pdf(image_bytes: bytes) -> bytes:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as img_file:
        img_file.write(image_bytes)
        img_path = img_file.name

    try:
        pdf_bytes = HTML(
            string=f"""
            <html>
              <body style="margin:0; padding:0;">
                <img src="file://{img_path}" style="width:100%; height:100vh; object-fit:cover;" />
              </body>
            </html>
            """
        ).write_pdf()
        return pdf_bytes
    finally:
        if os.path.exists(img_path):
            os.remove(img_path)


def merge_pdfs(pdf_parts: list[bytes]) -> bytes:
    writer = PdfWriter()

    for part in pdf_parts:
        reader = PdfReader(BytesIO(part))
        for page in reader.pages:
            writer.add_page(page)

    output = BytesIO()
    writer.write(output)
    return output.getvalue()


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
        cover_bytes = download_file(str(payload.cover_url))
        html_content = markdown_to_html(payload.reading_text)

        cover_pdf = image_to_single_page_pdf(cover_bytes)
        body_pdf = render_body_pdf(html_content)

        final_pdf = merge_pdfs([cover_pdf, body_pdf])

        return Response(
            content=final_pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": "inline; filename=reading.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
