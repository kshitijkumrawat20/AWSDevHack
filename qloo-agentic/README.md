# OmniPulse × Qloo — Taste-Aware Experience Agent

> Cultural intelligence is the missing context between a technically correct recommendation and an experience that feels right.

A standalone Qloo Agentic Hackathon edition of OmniPulse. It takes cultural references explicitly chosen by a user, resolves them to Qloo entities, asks Qloo's Taste Graph for affinity-ranked recommendations, and orchestrates a coherent local experience across places, movies, music and an optional ambient scene preview.

## Why Qloo is essential

A generic LLM can suggest popular restaurants, films or artists. This application instead uses Qloo for the core recommendation step:

1. Resolve the user's named references with Qloo's `/search` endpoint.
2. Confirm the exact Qloo entity IDs with the user before using them as taste signals.
3. Recommend places in the chosen city, plus movies and artists, through Qloo's `/v2/insights` endpoint using the confirmed entity IDs.
4. Orchestrate the returned candidates and an occasion-specific ambient scene preview into one experience.

The Qloo results are not decorative. Remove Qloo and the app loses entity resolution, taste-graph affinity recommendations, geographic place filtering and recommendation provenance.

## Run locally

Requires Python 3.11+.

```bash
cd qloo-agentic
uv venv --python 3.12
.venv\\Scripts\\Activate.ps1  # PowerShell
uv pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

Set your event key in a local untracked `.env` file (the application loads it on startup) or export it in your shell:

```bash
# Edit .env and set your actual event-issued value:
# QLOO_API_KEY=your-secret-key
# QLOO_BASE_URL=https://hackathon.api.qloo.com

python scripts/smoke_qloo.py Indore
uv run uvicorn app.main:app --reload --port 8000
```

Open http://127.0.0.1:8000.

## Deploy

The included Dockerfile serves the UI and API from one process. For Render, create a new Web Service from this repository, select branch `qloo-agentic`, set the Root Directory to `qloo-agentic`, choose Docker as the runtime, and set the `QLOO_API_KEY` environment variable as a secret. The same directory can be deployed to any host that runs Docker.

Set these backend environment variables in the host dashboard: `QLOO_API_KEY` (secret), `QLOO_BASE_URL=https://hackathon.api.qloo.com`, and optional `QLOO_TIMEOUT_SECONDS=20`.

Never put the Qloo key in frontend variables, browser storage, source code or screenshots.

## Verify the live event key

The smoke test makes two small live requests (one entity search and one place recommendation). Run it only when you are ready to spend two Qloo API requests:

```bash
python scripts/smoke_qloo.py Indore
```

It prints the selected seed and returned place names, never the API key. A configured key alone is not proof of successful authentication; use this check before recording the demo.

## Tests

```bash
pip install -r requirements.txt
pytest -q
```

Unit tests use synthetic fixtures and do not spend Qloo API quota. Live API verification requires the event key and must be run before submission.

## API

- `GET /api/health`: reports whether the server has a key configured (not whether the key is valid).
- `POST /api/resolve`: accepts 1–3 explicit cultural references and returns Qloo search candidates for user confirmation.
- `POST /api/plan`: accepts confirmed Qloo entity IDs, a city and an occasion; returns Qloo recommendations and an auditable tool trace.

## Responsible use and limitations

- Qloo describes aggregate cultural affinity; it does not prove an individual's identity, preferences, or future behavior.
- Only explicit cultural references typed by the user are sent to Qloo. Names, emails, household memory, health notes and device identifiers are not sent.
- Entity matches are shown for user confirmation; the system does not silently accept an ambiguous first match.
- The ambient scene is a suggested preset only. No real smart-home hardware is controlled by this demo.
- Recommendations are limited by the event API key's available categories and quota. Missing categories are surfaced instead of being replaced with fabricated results.
- The first version does not save profile data or raw Qloo responses.

## Built with

FastAPI, Python, httpx, Qloo Insights API, Qloo Taste Graph, HTML, CSS, JavaScript, Docker.

## License

MIT — see the repository root `LICENSE` file.
