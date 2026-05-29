# Product-Running Evidence — Siskeu BUMDes AI Operator

## 1. Evidence Purpose

This folder contains product-running evidence for **Siskeu BUMDes AI Operator**, a deployed AI-operated financial assistant for BUMDes monthly report explanation workflows.

The purpose of this evidence is to show that the product is not only a local prototype. It is deployed on Google Cloud Run, uses live Vertex AI Gemini inference, records LynkMesh grounding metadata, creates ExecutionLog records, and supports human review before any financial use.

---

## 2. Public-Safe Scope

This evidence uses synthetic or redacted data only.

No real BUMDes financial records, customer names, private invoices, bank account numbers, service account files, API keys, or production database exports are included in this repository.

The AI workflow is intentionally bounded:

```text
AI explains, checks, and proposes.
Human operators approve final financial decisions.
The system does not post ledger entries automatically.
The demo uses synthetic/redacted data.
```

---

## 3. Deployed Service

| Field                | Value                                                                              |
| -------------------- | ---------------------------------------------------------------------------------- |
| Product              | Siskeu BUMDes AI Operator                                                          |
| Cloud Run service    | `siskeu-bumdes-ai-operator`                                                        |
| Google Cloud project | `project-2501f30e-d2bc-4988-ada`                                                   |
| Project number       | `117234781795`                                                                     |
| Cloud Run region     | `asia-southeast2`                                                                  |
| Service URL          | `https://siskeu-bumdes-ai-operator-117234781795.asia-southeast2.run.app`           |
| Dashboard URL        | `https://siskeu-bumdes-ai-operator-117234781795.asia-southeast2.run.app/dashboard` |
| Runtime store        | `local_jsonl`                                                                      |
| Report source        | `synthetic`                                                                        |

---

## 4. Live Gemini Runtime

The deployed service was verified using live Vertex AI Gemini mode.

| Field                            | Value              |
| -------------------------------- | ------------------ |
| Gemini mode                      | `vertex`           |
| Vertex AI enabled                | `true`             |
| Google Cloud location for Gemini | `asia-southeast1`  |
| Gemini model                     | `gemini-2.5-flash` |
| Stub mode                        | `false`            |
| Gemini client stub               | `false`            |
| Gemini client Vertex enabled     | `true`             |

The Cloud Run service is deployed in `asia-southeast2`, while Vertex AI Gemini is called through `asia-southeast1` because this Gemini runtime was verified working there.

---

## 5. Latest Approved Evidence Run

| Field               | Value                                  |
| ------------------- | -------------------------------------- |
| Run ID              | `b1dd9e4f-eef5-4e1f-b448-f634681eaca0` |
| Agent               | `report_explainer`                     |
| Agent version       | `1.1.1`                                |
| Period              | `2026-04`                              |
| Data classification | `synthetic`                            |
| Result status       | `succeeded`                            |
| Human review status | `approved`                             |
| Reviewer ref        | `xprize-demo-operator`                 |
| Created at          | `2026-05-29T08:45:04.329025Z`          |
| Completed at        | `2026-05-29T08:45:11.673709Z`          |
| Reviewed at         | `2026-05-29T08:45:15.338743+00:00`     |

Review note:

```text
Approved from dashboard. Cloud Run live Gemini evidence. Synthetic/redacted data only.
```

---

## 6. Gemini Evidence

| Field            | Value                     |
| ---------------- | ------------------------- |
| Model            | `gemini-2.5-flash`        |
| Response ID      | `EFIZauC2HIGo4vEP2c3IyAo` |
| Finish reason    | `STOP`                    |
| Prompt tokens    | `1278`                    |
| Candidate tokens | `289`                     |
| Total tokens     | `3327`                    |
| Latency          | `7342 ms`                 |
| Temperature      | `0.2`                     |
| Is stub          | `false`                   |

This confirms the run used live Gemini inference, not local stub output.

---

## 7. LynkMesh Grounding Evidence

Each AI run records LynkMesh context metadata so the explanation can be traced back to a deterministic application context pack.

| Field             | Value                                                              |
| ----------------- | ------------------------------------------------------------------ |
| Context pack ID   | `f9f1a6f2b0d3240b4cd88759251d1dc33f1e9cda4e761fe9405ca1fbc8b75357` |
| Graph ID          | `ad5a0df4-11bf-5578-bbc7-54b84e4e3110`                             |
| Build ID          | `3f94d80e-d0ea-403c-b419-3696c85de235`                             |
| Profile           | `balanced`                                                         |
| Generator version | `4.4.1`                                                            |
| Schema version    | `mesh_context_ai_pack.v0.1`                                        |
| Token estimate    | `609`                                                              |

LynkMesh is used as a context infrastructure layer. It provides compact, deterministic system context from the Siskeu BUMDes application so Gemini can generate explanations grounded in the actual workflow structure.

The claim is intentionally bounded:

```text
LynkMesh provides deterministic, compact context from the Siskeu BUMDes application to ground Gemini workflows.
```

This evidence does not claim that LynkMesh automatically understands all financial risks.

---

## 8. Prompt and Artifact References

| Field                    | Value                                                                     |
| ------------------------ | ------------------------------------------------------------------------- |
| Prompt ID                | `report_explanation`                                                      |
| Prompt version           | `v1`                                                                      |
| Prompt SHA-256           | `sha256:d8b747214095957b5a4f0d3ce0969ba6d952bf7d70fd5d06f9b42add1a5c641c` |
| Prompt artifact          | `data/runs/b1dd9e4f-eef5-4e1f-b448-f634681eaca0/prompt.txt`               |
| Redacted report artifact | `data/runs/b1dd9e4f-eef5-4e1f-b448-f634681eaca0/report_redacted.json`     |
| Gemini response artifact | `data/runs/b1dd9e4f-eef5-4e1f-b448-f634681eaca0/response.txt`             |

The artifact paths refer to runtime-generated files inside the deployed service runtime. Public repository evidence uses redacted/synthetic exported JSON and screenshots instead of private runtime data.

---

## 9. Evidence Files in This Folder

Expected evidence files:

```text
evidence/product_running/
├── PRODUCT_RUNNING_EVIDENCE.md
├── cloud_run_live_gemini_approved_run.json
├── cloud_run_execution_logs.json
├── 01_cloud_run_dashboard_overview_live_gemini_approved.png
├── 02_cloud_run_lynkmesh_grounding_layer.png
└── 03_cloud_run_executionlog_history.png
```

### File descriptions

| File                                                       | Purpose                                                                        |
| ---------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `cloud_run_live_gemini_approved_run.json`                  | Exported approved ExecutionLog for the latest live Gemini run                  |
| `cloud_run_execution_logs.json`                            | Cloud Logging export for execution finalization and human review update events |
| `01_cloud_run_dashboard_overview_live_gemini_approved.png` | Dashboard overview showing Cloud Run evidence KPIs and live Gemini status      |
| `02_cloud_run_lynkmesh_grounding_layer.png`                | Dashboard section showing LynkMesh context pack and grounding metadata         |
| `03_cloud_run_executionlog_history.png`                    | Dashboard section showing succeeded and approved ExecutionLog history          |

---

## 10. Product-Running Checklist

| Requirement                         | Status | Evidence                                      |
| ----------------------------------- | -----: | --------------------------------------------- |
| Deployed Cloud Run URL exists       | ✅ Done | Cloud Run service URL                         |
| Dashboard is accessible             | ✅ Done | `/dashboard`                                  |
| Vertex AI Gemini runtime configured | ✅ Done | `/debug/gemini`                               |
| Gemini model recorded               | ✅ Done | `gemini-2.5-flash`                            |
| Stub mode disabled                  | ✅ Done | `is_stub=false`                               |
| Synthetic/redacted data only        | ✅ Done | `data_classification=synthetic`               |
| LynkMesh context pack recorded      | ✅ Done | `context_pack_id`                             |
| ExecutionLog generated              | ✅ Done | `run_id=b1dd9e4f-eef5-4e1f-b448-f634681eaca0` |
| Human review supported              | ✅ Done | `human_review.status=approved`                |
| Cloud Logging export captured       | ✅ Done | `cloud_run_execution_logs.json`               |
| Dashboard screenshots captured      | ✅ Done | `01`, `02`, `03` PNG files                    |
| GitHub repository updated           | ✅ Done | Commit history in `main`                      |

---

## 11. Validation Commands

### Runtime validation

```powershell
$base = "https://siskeu-bumdes-ai-operator-117234781795.asia-southeast2.run.app"

curl.exe "$base/version"
curl.exe "$base/debug/gemini"
curl.exe "$base/dashboard"
```

Expected runtime indicators:

```text
stub_mode=false
gemini_mode=vertex
vertex_ai_enabled=true
google_cloud_project=project-2501f30e-d2bc-4988-ada
google_cloud_location=asia-southeast1
gemini_client_stub=false
gemini_client_vertex_enabled=true
gemini_model=gemini-2.5-flash
report_source=synthetic
```

### Read latest approved run

```powershell
$base = "https://siskeu-bumdes-ai-operator-117234781795.asia-southeast2.run.app"
$runId = "b1dd9e4f-eef5-4e1f-b448-f634681eaca0"

$approvedRun = Invoke-RestMethod "$base/api/runs/$runId"
$approvedRun | ConvertTo-Json -Depth 30
```

### Export approved run evidence

```powershell
$approvedRun | ConvertTo-Json -Depth 30 |
  Out-File evidence\product_running\cloud_run_live_gemini_approved_run.json -Encoding utf8
```

### Export Cloud Logging evidence

```powershell
gcloud logging read `
  'resource.type="cloud_run_revision" AND resource.labels.service_name="siskeu-bumdes-ai-operator" AND (jsonPayload.event_type="execution_log_finalized" OR jsonPayload.event_type="human_review_updated")' `
  --project=project-2501f30e-d2bc-4988-ada `
  --limit=20 `
  --format=json > evidence\product_running\cloud_run_execution_logs.json
```

---

## 12. Known Technical Limitation

The current deployed service uses `local_jsonl` for run storage. To keep demo evidence consistent, Cloud Run was constrained to a single instance during evidence capture.

For production hardening, the ExecutionLog store should be moved to Firestore or Cloud Storage so run records remain durable across instances and revisions.

This limitation does not affect the validity of the product-running evidence shown here. It is a deployment hardening item for the next phase.

---

## 13. Safety and Claim Boundaries

This evidence supports the following claim:

```text
Siskeu BUMDes AI Operator is a deployed AI-operated financial assistant that uses Gemini on Google Cloud and LynkMesh context to explain synthetic or redacted BUMDes monthly reports, with human approval before final financial use.
```

This evidence does not claim:

```text
Fully autonomous accounting.
Automatic ledger posting.
Certified audit output.
Unsupervised financial decisions.
LynkMesh automatically understands all financial risks.
Use of real unredacted BUMDes financial data in the public demo.
```

---

## 14. Current Evidence Status

Technical product-running evidence is complete for the deployed MVP.

Completed:

```text
✅ FastAPI service works.
✅ Cloud Run deployment works.
✅ Vertex AI Gemini live runtime works.
✅ Gemini model gemini-2.5-flash verified.
✅ LynkMesh context pack recorded.
✅ ExecutionLog generated.
✅ Human review workflow works.
✅ Dashboard evidence view works.
✅ Synthetic/redacted data only.
✅ Approved live Gemini run exported.
✅ Cloud Logging evidence exported.
✅ Dashboard screenshots captured.
```

Next workstream:

```text
Business and revenue evidence pack:
- historical Siskeu BUMDes payment summary, redacted
- AI Operator paid pilot offer
- pilot agreement
- invoice
- redacted payment proof
- P&L summary
- customer/user evidence
- demo video
- Devpost final copy and QA
```
