# Architecture

## Boundary

The AI Operator never imports Siskeu PHP code directly. It reads report data
through `app/siskeu/report_adapter.py` (synthetic fixture now; read-only HTTP or
DB view later) and grounds the model with a LynkMesh context pack. This keeps the
"new project" boundary clean and auditable.

```
synthetic report fixture ─┐
                          ▼
        report_adapter ─► redact ─►┐
                                   │
   LynkMesh context pack ─► context_loader ─►┐
                                             ▼
                                   prompt registry (versioned + hashed)
                                             ▼
                                   GeminiClient (real OR stub)
                                             ▼
                                   structured JSON briefing
                                             ▼
                          run_logger ─► ExecutionLog (ALWAYS, even on failure)
                                             ▼
                       store: Firestore  OR  local JSONL fallback
                                             ▼
                                   dashboard (ugly, read-only)
```

## Evidence pipeline (the point of this repo)

Every agent run writes one `ExecutionLog` tying together:
- `lynkmesh.context_pack_id` (+ graph_id / build_id) — proves grounding,
- `prompt.{prompt_id, prompt_version, prompt_sha256}` — proves which instructions,
- `gemini.{model, tokens, latency, response_id}` — proves the deployed LLM call,
- `data_classification` (synthetic | redacted | real),
- `human_review.{status, reviewer_ref, reviewed_at, notes}`,
- `result_status` (succeeded | failed) — failures are logged too.

## Storage

- **Firestore** (`agent_runs`) is the system of record when `GCP_PROJECT` is set.
- **Local JSONL** (`data/runs/runs.jsonl` + per-run `<run_id>.json`) is the dev
  fallback used automatically when Firestore is unset/unavailable.
- Larger artifacts (rendered prompt, raw response, redacted report) are written
  per-run under `data/runs/<run_id>/`.

## Google Cloud products used

Cloud Run (host), Firestore (logs), Secret Manager (API key), Cloud Logging
(stdout). Any one satisfies the XPRIZE "≥1 Google Cloud product" rule.
