"""FastAPI entry point for the standalone OmniPulse x Qloo edition."""
from __future__ import annotations
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .agent import TasteExperienceAgent
from .qloo_client import QlooAPIError, QlooClient

ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT / "static"
app = FastAPI(title="OmniPulse x Qloo", version="0.1.0",
              description="A taste-aware agentic concierge grounded in Qloo cultural intelligence.")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

class InterestInput(BaseModel):
    query: str = Field(min_length=2, max_length=80)
    type: Literal["movie", "tv_show", "artist", "book", "brand", "videogame"]

class ResolveRequest(BaseModel):
    interests: list[InterestInput] = Field(min_length=1, max_length=3)

class SelectedSignal(BaseModel):
    entity_id: str = Field(min_length=8, max_length=100)
    name: str = Field(min_length=1, max_length=160)
    type: str | None = None

class PlanRequest(BaseModel):
    city: str = Field(min_length=2, max_length=80)
    occasion: Literal["movie_night", "dinner_party", "date_night", "weekend"]
    signals: list[SelectedSignal] = Field(min_length=1, max_length=3)

@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/api/health")
async def health():
    client = QlooClient()
    return {"status": "ok", "qloo_configured": client.configured, "service": "OmniPulse x Qloo"}

@app.post("/api/resolve")
async def resolve(request: ResolveRequest):
    client = QlooClient()
    try:
        return await TasteExperienceAgent(client).resolve([item.model_dump() for item in request.interests])
    except QlooAPIError as exc:
        code = 503 if not client.configured else (429 if exc.status_code == 429 else 502)
        raise HTTPException(status_code=code, detail=str(exc)) from exc

@app.post("/api/plan")
async def plan(request: PlanRequest):
    client = QlooClient()
    try:
        return await TasteExperienceAgent(client).plan(
            [signal.model_dump() for signal in request.signals], request.city, request.occasion
        )
    except QlooAPIError as exc:
        code = 503 if not client.configured else (429 if exc.status_code == 429 else 502)
        raise HTTPException(status_code=code, detail=str(exc)) from exc
