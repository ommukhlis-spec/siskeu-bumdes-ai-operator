# Product Running Evidence — Siskeu BUMDes AI Operator

Date: 2026-05-27

## Product

Siskeu BUMDes AI Operator is a deployed AI-operated financial assistant for BUMDes workflows.

It uses:
- Google Cloud Run for deployment
- Gemini via Vertex AI for report explanation
- LynkMesh context pack for deterministic grounding context
- ExecutionLog dashboard for evidence
- Human review before final approval
- Structured Cloud Logging for sanitized backend evidence events

## Live Service Evidence

Cloud Run service:
- siskeu-bumdes-ai-operator

Google Cloud region:
- asia-southeast2

Verified runtime:
- stub_mode=false
- gemini_mode=vertex
- model=gemini-2.5-flash
- app_env=cloud-run-vertex-gemini

## Verified Workflow

1. Loads synthetic BUMDes monthly report data.
2. Loads LynkMesh context pack.
3. Calls Gemini via Vertex AI.
4. Generates plain-language monthly report briefing.
5. Saves ExecutionLog.
6. Shows the run in the dashboard.
7. Requires human review before final approval.
8. Emits sanitized structured Cloud Logging events.

## Latest Evidence Run

Run ID:
- 47f6ad25-764b-4f36-92a0-6f264b0768a3

Result:
- succeeded

Gemini model:
- gemini-2.5-flash

Total tokens:
- 2625

LynkMesh context_pack_id:
- f9f1a6f2b0d3240b4cd88759251d1dc33f1e9cda4e761fe9405ca1fbc8b75357

Human review:
- approved

## Cloud Logging Evidence

Structured Cloud Logging events captured:
- execution_log_finalized
- human_review_updated

These events include:
- run_id
- Gemini model
- token usage
- LynkMesh context_pack_id
- human_review.status
- result_status

## Demo Video

YouTube demo:
https://www.youtube.com/watch?v=IwoLyCP9D0M

## Privacy and Safety

This evidence uses synthetic BUMDes report data only.

No public evidence includes:
- real BUMDes financial records
- API keys
- service account JSON
- customer payment proof
- customer private information

## Safe Claim

AI explains, checks, and proposes.
Humans approve final financial decisions.

