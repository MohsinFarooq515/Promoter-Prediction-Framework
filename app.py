from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.groups import MODEL_GROUPS
from webapp.predictor import ModelRegistry, parse_fasta as parse_fasta_text, parse_sequence

PROJECT_ROOT = Path(__file__).resolve().parent
STATIC_ROOT = PROJECT_ROOT / "webapp" / "static"
registry = ModelRegistry(PROJECT_ROOT)
app = FastAPI(title="Promoter Sequence Predictor", version="1.0.0")
app.mount("/static", StaticFiles(directory=STATIC_ROOT), name="static")


class SequenceRequest(BaseModel):
    model_group: str
    sequence: str = Field(min_length=1)
    sequence_id: str = "sequence_1"


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_ROOT / "index.html")


@app.get("/api/health")
def health():
    models = registry.describe()
    return {"status": "ok" if all(item["available"] for item in models) else "degraded", "models": models}


@app.get("/api/models")
def models():
    return {"models": registry.describe()}


@app.post("/api/predict/sequence")
def predict_sequence(request: SequenceRequest):
    _check_group(request.model_group)
    try:
        return registry.predict(request.model_group, parse_sequence(request.sequence, request.sequence_id.strip() or "sequence_1"))
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/predict/fasta")
async def predict_fasta_upload(model_group: str = Form(...), file: UploadFile = File(...)):
    _check_group(model_group)
    try:
        raw = await file.read(10 * 1024 * 1024 + 1)
        if len(raw) > 10 * 1024 * 1024:
            raise ValueError("FASTA uploads are limited to 10 MB.")
        text = raw.decode("utf-8-sig")
        record_count = sum(line.lstrip().startswith(">") for line in text.splitlines())
        result = registry.predict(model_group, parse_fasta_text(text))
        result["truncated"] = record_count > result["total"]
        if result["truncated"]:
            result["uploaded_record_count"] = record_count
            result["message"] = (
                f"This FASTA file contains {record_count:,} records. "
                f"The first {result['total']:,} sequences have been processed."
            )
        return result
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=422, detail="The FASTA file must be UTF-8 text.") from exc
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _check_group(model_group: str) -> None:
    if model_group not in MODEL_GROUPS:
        raise HTTPException(status_code=422, detail=f"Model group must be one of: {', '.join(MODEL_GROUPS)}.")
