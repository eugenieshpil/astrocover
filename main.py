from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from generate_personalized_cover import build_cover

app = FastAPI()


class Request(BaseModel):
    name: str
    birth_date: str
    birth_time: str
    birth_place: str
    prepared_date: str


@app.post("/generate-cover")
def generate(req: Request):
    base_dir = Path(__file__).resolve().parent
    cover_path = base_dir / "cover.png"
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

    return FileResponse(output_path, media_type="image/png", filename="cover.png")
