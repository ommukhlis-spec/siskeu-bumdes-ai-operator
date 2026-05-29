# Business & Revenue Evidence — Siskeu BUMDes AI Operator

## 1. Purpose

This document summarizes the business and revenue evidence plan for **Siskeu BUMDes AI Operator**.

The goal is to separate:

1. **Historical Siskeu BUMDes traction** — proof that the original Siskeu BUMDes work had real demand.
2. **XPRIZE-period AI Operator revenue** — new revenue from the AI-operated service layer built for this submission.

This distinction is important because the original Siskeu BUMDes development payment validates demand, but it should not be counted as XPRIZE-period AI Operator revenue.

---

## 2. Revenue Framing

### Historical revenue / traction

Historical revenue refers to the original paid development or service work related to the pre-existing Siskeu BUMDes application.

Use it as:

- validated demand,
- traction evidence,
- proof that the domain is real,
- proof that Siskeu BUMDes is not merely a toy demo.

Do not use it as:

- XPRIZE-period AI Operator revenue,
- new AI Operator sales,
- proof that the AI Operator itself has already generated revenue.

Expected location:

```text
evidence/historical/
```

### XPRIZE-period revenue

XPRIZE-period revenue should come from a new paid pilot, add-on, or service related to **Siskeu BUMDes AI Operator**.

Recommended offer:

```text
AI-Assisted Monthly Closing & Report Briefing
```

Use it as:

- clean AI Operator revenue,
- evidence of a new business layer,
- evidence that customers are willing to pay for AI-assisted financial workflow support.

Expected location:

```text
evidence/xprize_period/
```

---

## 3. Public Evidence vs Private Evidence

### Public repository evidence

Public-safe evidence may include:

- redacted summaries,
- placeholder manifests,
- invoice templates,
- public-safe agreement templates,
- screenshots with synthetic/redacted data,
- linked AI run IDs,
- revenue summaries with sensitive customer information removed.

### Private evidence

The following should not be committed to the public repository:

- unredacted invoices,
- bank transfer proof with account numbers,
- real customer names without permission,
- signed agreements containing private identity details,
- real financial records,
- raw payment screenshots,
- production database exports,
- API keys or service account files.

Private evidence should be stored offline or in a private folder and only shared through the official submission process if required and safe.

---

## 4. Current Evidence Checklist

| Evidence item | Status | Public repo file | Private/raw file |
|---|---:|---|---|
| Product-running evidence | Done / update if needed | `evidence/product_running/` | N/A |
| Historical Siskeu BUMDes payment summary | Pending | `evidence/historical/README.md` | private/offline |
| Historical manifest | Pending | `evidence/historical/manifest.example.json` | private/offline |
| AI Operator paid pilot offer | Drafted | `evidence/xprize_period/AI_ASSISTED_MONTHLY_CLOSING_OFFER.md` | N/A |
| Pilot agreement template | Drafted | `evidence/xprize_period/PILOT_AGREEMENT_TEMPLATE.md` | signed agreement private/offline |
| Invoice template | Drafted | `evidence/xprize_period/INVOICE_TEMPLATE.md` | issued invoice private/offline |
| Payment proof checklist | Drafted | `evidence/xprize_period/REDACTION_CHECKLIST.md` | payment proof private/offline |
| XPRIZE-period manifest | Pending | `evidence/xprize_period/manifest.example.json` | private/offline |
| P&L summary | Drafted | `evidence/xprize_period/P_AND_L_SUMMARY.md` | bookkeeping private/offline |
| Customer feedback/testimonial | Pending | `evidence/xprize_period/CUSTOMER_TESTIMONIAL_TEMPLATE.md` | signed/public permission private/offline |

---

## 5. Safe Business Claim

Safe public claim:

```text
Siskeu BUMDes AI Operator is a new AI-operated service layer built on top of the Siskeu BUMDes domain foundation. Historical Siskeu BUMDes work validates demand, while XPRIZE-period revenue should come from a new AI-assisted monthly closing and report briefing pilot.
```

Avoid claiming:

```text
The original Siskeu BUMDes development payment is new AI Operator revenue.
The system performs fully autonomous accounting.
The AI automatically posts ledger entries.
LynkMesh fully understands all financial risks.
```

---

## 6. Next Actions

1. Fill the historical evidence summary with redacted facts.
2. Send the AI-Assisted Monthly Closing & Report Briefing offer to the warmest BUMDes/customer lead.
3. If accepted, create a pilot agreement and invoice.
4. Collect payment proof and redact it.
5. Link the paid pilot to one or more approved AI run IDs.
6. Update the XPRIZE-period manifest.
7. Update the P&L summary.
8. Commit only public-safe summaries and templates.
