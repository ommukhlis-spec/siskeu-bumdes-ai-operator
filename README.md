# Siskeu BUMDes AI Operator

Siskeu BUMDes AI Operator is a newly created AI-operated service layer built for the Build with Gemini XPRIZE. It runs on top of the pre-existing Siskeu BUMDes financial administration foundation and uses Gemini on Google Cloud to explain synthetic or redacted BUMDes monthly reports with a human-review safety boundary.

## Product framing

This repository separates three layers clearly:

* **Siskeu BUMDes** — pre-existing BUMDes financial administration foundation and real-world domain context.
* **LynkMesh** — pre-existing deterministic context infrastructure and technical moat.
* **Siskeu BUMDes AI Operator** — newly created XPRIZE service layer that injects LynkMesh context into Gemini, runs evidence-logged AI workflows, and requires human review before final financial use.

The first implemented workflow is:

```text
Synthetic or redacted BUMDes monthly report input
-> LynkMesh context pack
-> Vertex AI Gemini live briefing
-> ExecutionLog
-> Human review approval
-> Evidence dashboard
```

## What it does

The AI Operator helps BUMDes operators understand monthly financial reports by producing a plain-language briefing from structured report data.

The current workflow:

1. Loads synthetic or redacted monthly report data.
2. Loads a LynkMesh context pack.
3. Calls Gemini through Vertex AI on Google Cloud.
4. Generates a plain-language report explanation.
5. Saves a durable ExecutionLog.
6. Shows the run in an evidence dashboard.
7. Requires human review before final use.

## Safety boundary

The system is intentionally designed with a financial safety boundary:

* AI explains, checks, and proposes.
* Human operators approve final financial decisions.
* The system does not automatically post ledger entries.
* Public demo data is synthetic or redacted.
* No real BUMDes financial data is exposed in this repository.

This project does **not** claim fully autonomous accounting.

## Business and revenue framing

The original Siskeu BUMDes development was paid for by a real BUMDes/customer. That historical payment is treated as:

* validated demand,
* traction evidence,
* historical paid development/service revenue.

It is not automatically counted as XPRIZE-period AI Operator revenue.

New XPRIZE-period revenue should come from the AI Operator paid pilot/add-on:

```text
AI-Assisted Monthly Closing & Report Briefing
```

Evidence split:

```text
evidence/historical/
  Historical Siskeu BUMDes traction evidence
  counts_as_xprize_revenue: false

evidence/xprize_period/
  New AI Operator pilot/add-on evidence
  counts_as_xprize_revenue: true
```

## Current runtime status

Production/evidence mode uses:

```text
Cloud Run service: siskeu-bumdes-ai-operator
Cloud Run region: asia-southeast2
Gemini runtime: Vertex AI
Gemini location: asia-southeast1
Gemini model: gemini-2.5-flash
Report source: synthetic
```

The Cloud Run region and Gemini model location are intentionally different:

```text
Cloud Run: asia-southeast2
Vertex AI Gemini: asia-southeast1
```

`gemini-2.5-flash` was verified working in `asia-southeast1`.

## Evidence status

Product-running evidence is stored under:

```text
evidence/product_running/
```

Expected Cloud Run evidence files:

```text
01_cloud_run_dashboard_overview_live_gemini_approved.png
02_cloud_run_lynkmesh_grounding_layer.png
03_cloud_run_executionlog_history.png
cloud_run_live_gemini_approved_run.json
cloud_run_execution_logs.json
```

A valid live Gemini evidence run should show:

```text
model: gemini-2.5-flash
is_stub: false
prompt_tokens: > 0
candidates_tokens: > 0
total_tokens: > 0
latency_ms: > 0
response_id: live Gemini response id
human_review.status: approved
result_status: succeeded
data_classification: synthetic or redacted
```

Stub/offline runs are retained only for local development and CI. They are not final XPRIZE product-running evidence.

## Repository structure

```text
app/
  agents/
  dashboard/
  evidence/
  gemini/
  lynkmesh/
  siskeu/

data/
  context_packs/
  fixtures/
  runs/

evidence/
  historical/
  product_running/
  xprize_period/

scripts/
tests/
```

## API endpoints

```text
GET  /healthz
GET  /version
GET  /dashboard

POST /agents/report-explanation/run
POST /agents/report-explanation/run-custom
POST /runs/{run_id}/review

GET  /api/runs
GET  /api/runs/{run_id}
GET  /api/summary
```

Debug endpoints are useful during evidence capture but should be gated or disabled before long-term public production use:

```text
GET  /debug/gemini
POST /debug/gemini/minimal-run
```

## Local development

Install dependencies:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
```

Run local server:

```bash
uvicorn app.main:app --reload --port 8080
```

Open:

```text
http://localhost:8080/dashboard
```

Trigger a synthetic report explanation:

```bash
curl -s -X POST http://localhost:8080/agents/report-explanation/run \
  -H "content-type: application/json" \
  -d '{"tenant_ref":"synthetic-tenant-001","period":"2026-04"}'
```

Local development can run without live credentials. In that case the pipeline still exercises report loading, LynkMesh context loading, logging, and dashboard display, but Gemini output is a deterministic development fallback.

## Local live Gemini run with Vertex AI

PowerShell:

```powershell
$env:GEMINI_MODE="vertex"
$env:GOOGLE_GENAI_USE_VERTEXAI="true"
$env:GOOGLE_CLOUD_PROJECT="project-2501f30e-d2bc-4988-ada"
$env:GOOGLE_CLOUD_LOCATION="asia-southeast1"
$env:GEMINI_MODEL="gemini-2.5-flash"
$env:REPORT_SOURCE="synthetic"

python -m uvicorn app.main:app --host 127.0.0.1 --port 8080
```

Validate:

```powershell
curl.exe http://127.0.0.1:8080/version
curl.exe http://127.0.0.1:8080/debug/gemini
curl.exe -X POST -H "Content-Type: application/json" --data-raw "{}" http://127.0.0.1:8080/debug/gemini/minimal-run
```

Expected runtime indicators:

```text
stub_mode: false
gemini_mode: vertex
vertex_ai_enabled: true
google_cloud_location: asia-southeast1
gemini_client_stub: false
model: gemini-2.5-flash
is_stub: false
```

## Cloud Run deployment

Deploy:

```powershell
gcloud run deploy siskeu-bumdes-ai-operator `
  --source . `
  --project project-2501f30e-d2bc-4988-ada `
  --region asia-southeast2 `
  --allow-unauthenticated
```

Set environment variables one by one or as a comma-separated set:

```powershell
gcloud run services update siskeu-bumdes-ai-operator `
  --project project-2501f30e-d2bc-4988-ada `
  --region asia-southeast2 `
  --update-env-vars GEMINI_MODE=vertex

gcloud run services update siskeu-bumdes-ai-operator `
  --project project-2501f30e-d2bc-4988-ada `
  --region asia-southeast2 `
  --update-env-vars GOOGLE_GENAI_USE_VERTEXAI=true

gcloud run services update siskeu-bumdes-ai-operator `
  --project project-2501f30e-d2bc-4988-ada `
  --region asia-southeast2 `
  --update-env-vars GOOGLE_CLOUD_PROJECT=project-2501f30e-d2bc-4988-ada

gcloud run services update siskeu-bumdes-ai-operator `
  --project project-2501f30e-d2bc-4988-ada `
  --region asia-southeast2 `
  --update-env-vars GOOGLE_CLOUD_LOCATION=asia-southeast1

gcloud run services update siskeu-bumdes-ai-operator `
  --project project-2501f30e-d2bc-4988-ada `
  --region asia-southeast2 `
  --update-env-vars GEMINI_MODEL=gemini-2.5-flash

gcloud run services update siskeu-bumdes-ai-operator `
  --project project-2501f30e-d2bc-4988-ada `
  --region asia-southeast2 `
  --update-env-vars REPORT_SOURCE=synthetic
```

Validate deployed runtime:

```powershell
$base = "https://siskeu-bumdes-ai-operator-117234781795.asia-southeast2.run.app"

curl.exe "$base/version"
curl.exe "$base/debug/gemini"
curl.exe -X POST -H "Content-Type: application/json" --data-raw "{}" "$base/debug/gemini/minimal-run"
```

## Capture Cloud Run evidence

After running and approving a briefing from the deployed dashboard, save the latest run:

```powershell
$base = "https://siskeu-bumdes-ai-operator-117234781795.asia-southeast2.run.app"
$run = (Invoke-RestMethod "$base/api/runs")[0]
$run | ConvertTo-Json -Depth 20 | Out-File evidence\product_running\cloud_run_live_gemini_approved_run.json -Encoding utf8
```

Save Cloud Logging evidence:

```powershell
gcloud logging read `
  'resource.type="cloud_run_revision" AND resource.labels.service_name="siskeu-bumdes-ai-operator" AND (jsonPayload.event_type="execution_log_finalized" OR jsonPayload.event_type="human_review_updated")' `
  --project=project-2501f30e-d2bc-4988-ada `
  --limit=20 `
  --format=json > evidence\product_running\cloud_run_execution_logs.json
```

The evidence should show both:

```text
execution_log_finalized
human_review_updated
```

and at least one approved live Gemini run:

```text
gemini.is_stub: false
human_review.status: approved
result_status: succeeded
```

## Tests

```bash
pytest -q
```

Current test coverage includes:

* ExecutionLog schema
* run logger
* report explainer stub-mode isolation
* structured Cloud Logging sanitization

## Privacy and public repository rules

Do not commit:

* `.env`
* API keys
* service account JSON
* raw customer invoices
* payment proof with account numbers
* customer names
* raw financial records
* production database dumps
* private local paths
* real BUMDes financial data

Use:

* synthetic demo data
* redacted customer evidence
* hashed tenant references
* public-safe screenshots
* placeholder/example manifests

## Built with

```text
Python
FastAPI
Gemini API
Vertex AI
Google Cloud Run
Cloud Logging
LynkMesh
Docker
Jinja2
Pydantic
```
