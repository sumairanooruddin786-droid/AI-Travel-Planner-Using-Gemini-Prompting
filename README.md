# Wayfarer — AI Travel Planner (Gemini Prompting Techniques)

A full-stack app built for the SMIT Prompt Engineering assignment. It generates a
personalized travel itinerary with the Google Gemini API, and lets you compare how
**Zero-Shot**, **Few-Shot**, and **Structured Reasoning** prompting change the result
for the exact same trip.

## Stack

- **Backend:** Python, FastAPI, `google-genai` (official Gemini SDK)
- **Frontend:** Vanilla HTML/CSS/JS (no build step) — a "boarding pass" themed UI
- **Output:** each generated plan renders as a boarding-pass card; results can be
  printed/exported, and you can run all 3 techniques at once to compare them

## Project structure

```
ai-travel-planner/
├── backend/
│   ├── main.py            FastAPI app + routes
│   ├── prompts.py         The 3 prompting-technique builders (the assignment core)
│   ├── gemini_client.py   Thin wrapper around the Gemini API
│   ├── requirements.txt
│   └── .env.example       Copy to .env and add your key
└── frontend/
    ├── index.html
    ├── style.css
    └── script.js
```

## Setup

1. **Get a Gemini API key** — https://aistudio.google.com/app/apikey (free tier available).

2. **Install backend dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Add your API key:**
   ```bash
   cp .env.example .env
   # then edit .env and paste your key into GEMINI_API_KEY=
   ```

4. **Run the server:**
   ```bash
   uvicorn main:app --reload
   ```

5. **Open the app:** http://127.0.0.1:8000 — the FastAPI server also serves the
   frontend, so there's nothing else to start.

## How the three techniques are implemented

All three live in `backend/prompts.py` so they're easy to compare:

| Technique | What it does |
|---|---|
| **Zero-Shot** | Sends only a direct instruction + the traveler's raw details. No examples. |
| **Few-Shot** | Prepends 3 fully worked example travelers (different destinations, budgets, styles) before asking for the real traveler's plan, so Gemini has a concrete pattern to copy. |
| **Structured Reasoning** | Gives Gemini an explicit 6-step checklist (analyze preferences → consider budget → consider days → select attractions → build itinerary → justify picks) but instructs it to hide the scratch work and return only the final plan with a short one-line "why" per day. |

Every technique shares the same output-format instructions, so the *only* variable
being tested between them is the prompting strategy — which is the point of the
assignment.

## API reference

| Method | Route | Purpose |
|---|---|---|
| GET | `/api/health` | Liveness + whether the API key is configured |
| GET | `/api/techniques` | Metadata describing the 3 techniques (used to render descriptions) |
| POST | `/api/itinerary` | Body: `{name, destination, days, budget, interests[], travel_style, technique}` → one itinerary |
| POST | `/api/itinerary/compare` | Same body, `technique` is ignored → runs all 3 techniques and returns all results |

## Bonus features added beyond the spec

- **Compare-all mode**: run the same trip through all 3 techniques side by side in one click.
- **"View prompt used"**: every result card can show the exact prompt sent to Gemini, for transparency/grading.
- **Print/export**: each boarding pass has a print-friendly stylesheet.
- **Recent trips history** shown at the bottom of the results panel for the session.

## Fix for Gemini 503 UNAVAILABLE

The backend now retries temporary Gemini errors and tries a fallback model if the
selected model is overloaded. This cannot guarantee availability if every model
is overloaded or unavailable to your API key.

1. Create `backend/.env` from `backend/.env.example`.
2. Replace `your_api_key_here` with your own Gemini API key.
3. From the project root, run:
   ```bash
   pip install -r backend/requirements.txt
   uvicorn main:app --reload
   ```
4. Open `http://127.0.0.1:8000`.

If the error persists, check that the browser is using this updated project folder
and check your model access/quota in Google AI Studio.

