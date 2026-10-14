"""
main.py
-------
FastAPI backend for the AI Travel Planner assignment.

Exposes:
  GET  /api/health                -> simple liveness check
  GET  /api/techniques            -> metadata about the 3 prompting techniques
  POST /api/itinerary             -> generate ONE itinerary with a chosen technique
  POST /api/itinerary/compare     -> generate all 3 itineraries at once (bonus feature)

Also serves the static frontend (../frontend) at "/", so the whole app can be
run with a single command: `uvicorn main:app --reload`.
"""

import os
import time
from pathlib import Path
from typing import List, Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from gemini_client import GeminiNotConfiguredError, generate_text
from prompts import TECHNIQUE_BUILDERS, TECHNIQUE_LABELS

load_dotenv()

app = FastAPI(
    title="AI Travel Planner API",
    description="Generates personalized travel itineraries via Gemini, comparing "
    "Zero-Shot, Few-Shot, and Structured Reasoning prompting techniques.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

Technique = Literal["zero-shot", "few-shot", "structured"]


class TripRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=60)
    destination: str = Field(..., min_length=1, max_length=80)
    days: int = Field(..., ge=1, le=30)
    budget: float = Field(..., gt=0, le=1_000_000)
    interests: List[str] = Field(default_factory=list)
    travel_style: str = Field(..., min_length=1, max_length=30)
    technique: Technique = "zero-shot"

    @field_validator("interests")
    @classmethod
    def clean_interests(cls, value: List[str]) -> List[str]:
        return [v.strip() for v in value if v and v.strip()]


class ItineraryResponse(BaseModel):
    technique: str
    technique_label: str
    prompt_used: str
    itinerary_markdown: str
    generation_time_seconds: float


class CompareResponse(BaseModel):
    results: List[ItineraryResponse]


def _run_technique(data: dict, technique: Technique) -> ItineraryResponse:
    builder = TECHNIQUE_BUILDERS[technique]
    prompt = builder(data)

    start = time.time()
    try:
        text = generate_text(prompt)
    except GeminiNotConfiguredError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Gemini request failed: {exc}") from exc
    elapsed = time.time() - start

    return ItineraryResponse(
        technique=technique,
        technique_label=TECHNIQUE_LABELS[technique],
        prompt_used=prompt,
        itinerary_markdown=text,
        generation_time_seconds=round(elapsed, 2),
    )


@app.get("/api/health")
def health():
    return {"status": "ok", "gemini_configured": bool(os.getenv("GEMINI_API_KEY"))}


@app.get("/api/techniques")
def techniques():
    return {
        "techniques": [
            {
                "id": "zero-shot",
                "label": "Zero-Shot Prompting",
                "description": "Gemini gets only the traveler's details and a direct "
                "instruction - no examples to learn a pattern from.",
            },
            {
                "id": "few-shot",
                "label": "Few-Shot Prompting",
                "description": "Gemini first studies 3 example travelers and their "
                "sample itineraries, then follows that pattern for the real traveler.",
            },
            {
                "id": "structured",
                "label": "Structured Reasoning Prompting",
                "description": "Gemini is guided through 6 explicit analysis steps "
                "internally, then returns only the final plan with short justifications.",
            },
        ]
    }


@app.post("/api/itinerary", response_model=ItineraryResponse)
def create_itinerary(trip: TripRequest):
    return _run_technique(trip.model_dump(), trip.technique)


@app.post("/api/itinerary/compare", response_model=CompareResponse)
def compare_itineraries(trip: TripRequest):
    data = trip.model_dump()
    results = [_run_technique(data, technique) for technique in TECHNIQUE_BUILDERS]
    return CompareResponse(results=results)


# --- Serve the frontend -----------------------------------------------------
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
