# Redaction Checklist — Business & Revenue Evidence

Before committing any business or revenue evidence to GitHub, check the following.

## Never Commit

```text
.env
API keys
service account JSON
raw invoices
raw bank transfer proof
bank account numbers
real customer names without permission
customer addresses
phone numbers
email addresses
signatures
raw financial records
production database exports
private local paths
```

## Safe to Commit

```text
redacted summary
placeholder manifest
invoice template
agreement template
payment proof checklist
customer type without identity
linked AI run IDs
public-safe screenshot using synthetic/redacted data
P&L summary without sensitive details
```

## Payment Proof Redaction

Before sharing payment proof publicly, redact:

- sender name if private,
- recipient bank account number,
- transaction reference if sensitive,
- personal phone/email,
- QR/payment ID,
- address,
- signature,
- unrelated balance information.

Keep visible only if safe:

- payment date,
- amount,
- currency,
- payment status,
- invoice reference,
- service description.

## Revenue Claim Check

Before claiming revenue:

1. Was payment actually received?
2. Is the payment for the AI Operator offer, not only historical Siskeu work?
3. Is the invoice or agreement dated within the relevant period?
4. Is related-party revenue disclosed separately?
5. Is customer identity redacted or approved for public use?
6. Are linked AI run IDs recorded?
