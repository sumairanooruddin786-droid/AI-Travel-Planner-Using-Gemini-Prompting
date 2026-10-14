"""Gemini API client with retries and model fallback for temporary overloads."""
import os
import time
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load this project's own .env before reading GEMINI_MODEL.
load_dotenv(Path(__file__).resolve().with_name(".env"))

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
# If the selected model is overloaded, try these alternatives in order.
FALLBACK_MODELS = [
    m.strip()
    for m in os.getenv(
        "GEMINI_FALLBACK_MODELS",
        "gemini-3.8-flash-lite,gemini-3.8-flash"
    ).split(",")
    if m.strip() and m.strip() != DEFAULT_MODEL
]


class GeminiNotConfiguredError(RuntimeError):
    """Raised when GEMINI_API_KEY is missing from the environment."""


@lru_cache(maxsize=1)
def _get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise GeminiNotConfiguredError(
            "GEMINI_API_KEY is missing. Put your key in backend/.env."
        )
    return genai.Client(api_key=api_key)


def _status_code(exc):
    for value in (
        getattr(exc, "status_code", None),
        getattr(exc, "code", None),
        getattr(getattr(exc, "response", None), "status_code", None),
    ):
        if isinstance(value, int):
            return value
        # Some SDK versions expose a status enum/string.
        if isinstance(value, str):
            digits = "".join(ch for ch in value if ch.isdigit())
            if digits:
                try:
                    return int(digits)
                except ValueError:
                    pass
    return None


def _generate_with_model(client, model, prompt, temperature):
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=4096,
        ),
    )
    text = getattr(response, "text", None)
    if not text:
        raise RuntimeError(
            f"Gemini model {model} returned no usable text. "
            "Check the prompt and safety response."
        )
    return text


def generate_text(prompt: str, temperature: float = 0.8) -> str:
    """Try the configured model, then fallback models for transient 5xx/429 errors."""
    client = _get_client()
    models = [DEFAULT_MODEL] + FALLBACK_MODELS
    retryable = {429, 500, 502, 503, 504}
    errors = []

    for model_index, model in enumerate(models):
        for attempt in range(2):
            try:
                return _generate_with_model(client, model, prompt, temperature)
            except Exception as exc:
                status = _status_code(exc)
                errors.append(f"{model}: {exc}")
                if status not in retryable:
                    # Don't mask invalid API keys, invalid requests, or unsupported models.
                    raise
                if attempt == 0:
                    time.sleep(1.5)
                    continue
                # After two failed attempts, move to the next model.
                break

    raise RuntimeError(
        "Gemini models are temporarily unavailable after retries. "
        "Please wait a minute and try again. Details: " + " | ".join(errors)
    )
