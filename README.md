# Siskeu BUMDes AI Operator

A **newly created** AI-operated service layer on top of the (pre-existing) Siskeu
BUMDes accounting platform. Built for the *Build with Gemini XPRIZE*.

Three clearly separated layers:

- **Siskeu BUMDes** (pre-existing) — the double-entry accounting platform and the
  real-world domain (books, journals, reports, approval workflow).
- **LynkMesh** (pre-existing) — context infrastructure. It builds a deterministic
  semantic graph of the platform and projects it into a compact (~600-token)
  context pack that grounds the model.
- **AI Operator** (this repo, new) — the service we built during the window: it
  injects LynkMesh context into Gemini, runs operational agents, enforces a
  human-approval boundary on anything that touches the ledger, deploys on Google
  Cloud, and **logs every agent run as evidence**.

The first working flow (implemented here):

> Synthetic monthly report -> load LynkMesh context pack -> call Gemini through the
> configured client -> produce a plain-language report explanation -> save an
> ExecutionLog -> show the run in a simple dashboard.

## Business / revenue framing (read this)

- The **original Siskeu BUMDes development was paid for by a real BUMDes/customer.**
  That is **historical paid development/service revenue** and **proof of validated
  demand.** It lives under `evidence/historical/`.
- That historical payment is **NOT** automatically counted as XPRIZE-period AI
  Operator revenue. It predates the window and is not tied to the new AI layer.
- The **new XPRIZE revenue** must come from the AI Operator paid pilot/add-on:
  **"AI-Assisted Monthly Closing & Report Briefing."** Its evidence lives under
  `evidence/xprize_period/` and, where possible, links to real agent `run_id`s.

## How to run locally

```bash
# 1) (optional) create a venv and install deps
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2) configure env (works WITHOUT a key -> stub mode)
cp .env.example .env
# set GEMINI_API_KEY for real calls; leave empty to run the offline stub.
# export the vars (or use a dotenv loader of your choice):
set -a; . ./.env; set +a                                # bash

# 3) run the service
uvicorn app.main:app --reload --port 8080

# 4) trigger the first agent run
curl -s -X POST localhost:8080/agents/report-explanation/run \
  -H "content-type: application/json" \
  -d '{"tenant_ref":"synthetic-tenant-001","period":"2026-04"}' | python -m json.tool

# 5) open the dashboard
#    http://localhost:8080/dashboard
```

No API key? The Gemini client runs in **stub mode** (deterministic offline
response) so the entire pipeline — logging, redaction, dashboard — works end to end.

## Docker

```bash
docker build -t siskeu-ai-operator .
docker run --rm -p 8080:8080 --env-file .env siskeu-ai-operator
```

## Deploy to Cloud Run (template)

```bash
gcloud run deploy siskeu-ai-operator \
  --source . \
  --region asia-southeast2 \
  --allow-unauthenticated \
  --set-secrets GEMINI_API_KEY=gemini-api-key:latest \
  --set-env-vars GEMINI_MODEL=gemini-2.5-flash,GCP_PROJECT=YOUR_PROJECT,GCS_BUCKET=YOUR_BUCKET
```
> Confirm the current Gemini model id in Google's docs. The model is always read
> from `GEMINI_MODEL`; it is never hardcoded.

## Tests

```bash
pytest -q
```

## Layout

See `ARCHITECTURE.md`.

## Gemini Runtime Mode

The Siskeu BUMDes AI Operator supports two Gemini runtime modes.

### 1. Production / Evidence Mode � Vertex AI Gemini Live

For XPRIZE product-running evidence, the application runs Gemini through Vertex AI using Application Default Credentials or the Cloud Run service account.

Required environment variables:

```env
GEMINI_MODE=vertex
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=project-2501f30e-d2bc-4988-ada
GOOGLE_CLOUD_LOCATION=asia-southeast1
GEMINI_MODEL=gemini-2.5-flash
REPORT_SOURCE=synthetic
```

A successful live evidence run records:

```json
{
  "model": "gemini-2.5-flash",
  "is_stub": false,
  "prompt_tokens": "> 0",
  "candidates_tokens": "> 0",
  "total_tokens": "> 0",
  "latency_ms": "> 0",
  "response_id": "live Gemini response id"
}
```

The dashboard distinguishes live Gemini runs from local/development stub runs.

### 2. Local / CI Stub Mode

Stub mode is retained for local development, offline testing, and CI when no live Gemini credentials are configured.

Stub mode is active when neither Vertex AI mode nor an API key is configured. Stub runs are clearly marked with:

```json
{
  "is_stub": true,
  "response_id": "stub"
}
```

Stub runs are not used as final XPRIZE product-running evidence.

## Evidence Workflow

The submitted evidence workflow is:

```text
Synthetic or redacted BUMDes report input
? LynkMesh context pack
? Vertex AI Gemini live briefing
? ExecutionLog
? Human review approval
? Evidence dashboard
```

The AI explains, checks, and proposes. Human operators approve final financial decisions. The system does not automatically post ledger entries and does not claim fully autonomous accounting.

## Local Live Gemini Run

Use this local command sequence to run with Vertex AI Gemini:

```powershell
$env:GEMINI_MODE="vertex"
$env:GOOGLE_GENAI_USE_VERTEXAI="true"
$env:GOOGLE_CLOUD_PROJECT="project-2501f30e-d2bc-4988-ada"
$env:GOOGLE_CLOUD_LOCATION="asia-southeast1"
$env:GEMINI_MODEL="gemini-2.5-flash"
$env:GEMINI_FORCE_MINIMAL=""
$env:GEMINI_DEBUG=""
$env:REPORT_EXPLAINER_DEBUG=""

python -m uvicorn app.main:app --host 127.0.0.1 --port 8080
```

Then validate:

```powershell
curl.exe http://127.0.0.1:8080/version
curl.exe http://127.0.0.1:8080/debug/gemini
```

Expected runtime evidence:

```text
stub_mode=false
gemini_model=gemini-2.5-flash
google_cloud_location=asia-southeast1
```
