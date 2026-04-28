# JMT_ADMIN_ASSISTANT — Skill Proposal V1

```
authority:              NON_SOVEREIGN
canon:                  NO_SHIP
lifecycle:              PROPOSAL
implementation_status:  NOT_IMPLEMENTED
owner:                  JMT Consulting
skill_name:             JMT_ADMIN_ASSISTANT
schema:                 SKILL_PROPOSAL_V1
```

> **Core phrase**
>
> *JMT Admin Skill does not replace the operator. It clears the fog, prepares the packet, and waits for confirmation.*

---

## 1. Executive Summary

`JMT_ADMIN_ASSISTANT` is a HELEN skill designed to reduce administrative friction at JMT Consulting without ever displacing operator authority on legally or financially binding actions. It operates strictly in **proposal / organizer / drafter** mode: collecting documents, classifying them, drafting outputs, surfacing decisions, and preparing receipt-bearing packets — but never submitting, signing, paying, or declaring.

Every mutation it performs (file move, rename, draft, packet build) emits a non-sovereign receipt. Every output destined for an external party (email, invoice, quote, tax filing, government submission) is held in a `DRAFT` state until the operator confirms. The skill clears the fog around admin work; the operator remains the only legitimate hand on the action.

This document is a proposal. It defines scope, boundaries, workflows, receipt shape, and acceptance tests. **No code is implemented under this artifact.**

---

## 2. Skill Scope

### In scope
- Document intake from local sources (filesystem inboxes, manually-deposited folders)
- Classification of incoming documents by type (invoice, quote, contract, tax letter, client brief, banking statement, etc.)
- Renaming + folder organization per a stable taxonomy
- Drafting outbound communications (emails, invoices, quotes, follow-ups)
- Tracking due dates, unpaid invoices, contractual deadlines
- Preparing accountant packets (monthly/quarterly bundles)
- Preparing VAT/tax document packets for operator review
- Generating weekly briefings + monthly closeouts
- Surfacing a "needs operator decision" list

### Out of scope (explicit)
- Anything that places JMT Consulting under legal, financial, or fiduciary obligation without an operator-recorded confirmation
- Direct connections to bank, payment processor, government portals, or accounting authority systems (deferred to future integrations after explicit operator authorization)
- Final legal interpretation
- Any form of automated submission, signature, payment, or declaration

---

## 3. Non-Sovereign Authority Boundary

This skill is **NON_SOVEREIGN_ADMIN**. Authority boundary is enforced at three layers:

| Layer | What it does | What it cannot do |
|---|---|---|
| Intake | reads files, classifies, renames, organizes | modify the original document content; delete originals |
| Drafter | produces email/invoice/quote drafts in `status: DRAFT` | send, submit, or sign anything |
| Packet builder | assembles receipt-bearing bundles for review | route bundles to external systems |

The operator is the only entity allowed to:
- send drafts
- sign documents
- transmit invoices
- submit to authorities
- pay or authorize payment
- accept or reject contracts on JMT's behalf

The skill's allowed verbs are: **organize · draft · remind · classify · prepare**.
The skill's forbidden verbs are: **submit · sign · pay · declare · approve · certify**.

---

## 4. Supported Admin Workflows

| Workflow | Description |
|---|---|
| Inbox scan | Collect and list all new incoming documents from configured intake folders |
| Document classification | Tag each document by type (invoice / quote / contract / tax / banking / client / internal), entity, and priority |
| File rename + organize | Apply consistent taxonomy `<YYYY-MM-DD>_<client>_<type>_<slug>.<ext>` and move to canonical folders |
| Client folder creation | Scaffold a per-client directory tree on first sight |
| Email drafting | Produce drafts for client follow-up, payment reminders, scope clarifications, status updates |
| Quote draft | Prepare a structured quote packet from template and context |
| Invoice draft | Prepare invoice (number, line items, VAT, total, payment terms) — never sent automatically |
| Unpaid invoice tracker | List outstanding invoices with age in days and follow-up status |
| Due-date tracker | Surface upcoming fiscal, legal, and contractual deadlines |
| VAT / tax packet prep | Assemble relevant documents for a given tax period |
| Accountant packet | Compile monthly or quarterly bundle: invoices issued, invoices paid, expenses, VAT, banking statements |
| Contract summary | Extract key terms (parties, scope, fee, term, termination, IP) for operator review |
| Action item extraction | Pull to-dos and deadlines from letters, emails, and official notices |
| Weekly admin briefing | Structured summary: inbox, urgent, pending decisions |
| Monthly closeout | Full administrative status report for the month |
| Operator decision queue | List of items waiting for explicit operator confirmation |

---

## 5. Inputs and Sources

### Initial (V1)
- Local filesystem inbox folders (e.g., `~/Documents/JMT_INBOX/`)
- Operator-pasted text (a stdin / clipboard intake mode for ad-hoc items)
- HELEN ledger references (the skill reads its own prior receipts to stay coherent across sessions)

### Deferred (require explicit operator authorization to enable)
- IMAP / Gmail API for email intake
- Bank statement API connectors
- Accounting platform sync (e.g., Pennylane, QuickBooks, Sage)
- Government portal scraping
- Calendar / agenda integration

The operator must explicitly authorize each external connection before any code reaches it. Connections are not silent.

---

## 6. Output Types

| Output | Format | State on creation |
|---|---|---|
| Renamed/moved file | filesystem operation | committed (with receipt) |
| Email draft | `.eml` or markdown stub in `~/JMT_DRAFTS/email/` | `DRAFT` |
| Quote | structured markdown + PDF render in `~/JMT_DRAFTS/quotes/` | `DRAFT` |
| Invoice | structured markdown + PDF render in `~/JMT_DRAFTS/invoices/` | `DRAFT` |
| Packet | folder bundle with manifest.json + receipts | `READY_FOR_OPERATOR` |
| Weekly brief / monthly closeout | markdown report | `READY_FOR_OPERATOR` |
| Decisions list | markdown checklist | `READY_FOR_OPERATOR` |

**No output ever transitions out of `DRAFT` / `READY_FOR_OPERATOR` without an explicit operator confirmation step that emits its own receipt.**

---

## 7. Receipt Requirements

Every administrative mutation produces a non-sovereign receipt of schema `JMT_ADMIN_RECEIPT_V1`. Mutations covered:

- file moved
- file renamed
- draft created (email / quote / invoice / packet)
- packet prepared
- reminder created
- operator confirmation captured (separate receipt class: `JMT_ADMIN_CONFIRMATION_V1`)

Receipt fields (minimum):

```json
{
  "schema": "JMT_ADMIN_RECEIPT_V1",
  "authority_status": "NON_SOVEREIGN_ADMIN",
  "action_class": "FILE_MOVED | FILE_RENAMED | DRAFT_CREATED | PACKET_PREPARED | REMINDER_CREATED",
  "action_id": "...",
  "subject_path": "...",
  "subject_sha256": "...",
  "before_state": {...},
  "after_state": {...},
  "operator_confirmed": false,
  "confirmation_receipt_ref": null,
  "generated_at": "ISO-8601",
  "ledger_pointer": null
}
```

Concrete receipt example (filesystem move):

```
[RECEIPT] 2026-04-28T14:32:00Z
action:    FILE_MOVED
from:      ~/Documents/JMT_INBOX/scan_unsorted/facture_001.pdf
to:        ~/Documents/JMT_ADMIN/<entity>/clients/<client>/invoices/2026-04/2026-04-28_<client>_invoice_001.pdf
sha256:    9c1f…b3a2 (unchanged before/after move)
operator:  JM
confirmed: AUTO  (Tier 0 — file move within taxonomy)
ledger_pointer: null  (local-only; no spine entry)
```

If the action class is Tier 1 (e.g., `INVOICE_SENT`), the receipt holds two refs: the prior `DRAFT_CREATED` receipt and the `JMT_ADMIN_CONFIRMATION_V1` receipt. The chain `DRAFT → CONFIRMATION → SEND` is hash-linked end-to-end.

Receipts are stored under `~/Documents/JMT_ADMIN/receipts/YYYY/MM/` and **may be optionally pointer-linked into the HELEN ledger via `tools/helen_say.py`** when the operator wants HELEN's spine to record the admin event class. Default is local-only (no ledger spine entry) to keep admin volume from polluting the constitutional ledger.

---

## 8. Human Confirmation Rules

Three confirmation tiers:

**Tier 0 — automatic (no confirmation):**
- file move / rename within JMT_INBOX taxonomy
- draft creation (lives in DRAFT state, sends to no one)
- weekly briefing generation
- decisions-list compilation

**Tier 1 — single-step operator confirmation required:**
- Sending a drafted email
- Sending a drafted invoice
- Issuing a quote
- Marking an invoice paid
- Updating an unpaid-tracker entry
- Closing a tax packet for a period

**Tier 2 — multi-step confirmation required (operator must re-state intent):**
- Anything that creates an external legal/financial record (signed contract, tax filing, government submission, payment authorization)
- Tier 2 actions are **forbidden by default in V1** — the skill never reaches Tier 2 actions; those remain operator-only manual ops.

Confirmations themselves emit receipts (`JMT_ADMIN_CONFIRMATION_V1`) so the chain "draft → confirmation → external action" is auditable end-to-end.

---

## 9. Forbidden Actions

The skill **must not**:

- give legal advice as final authority
- file taxes
- submit to government portals
- execute payments
- sign documents (electronic or otherwise)
- accept contracts on JMT's behalf
- send invoices without operator confirmation
- delete original documents
- modify official records without a receipt
- perform hidden background automation
- write to HELEN's sovereign ledger except via the admissible bridge `tools/helen_say.py` and only when operator explicitly opts in

Violation of any forbidden action constitutes a constitutional break and aborts the skill.

---

## 10. Data Privacy Rules

- All admin documents stay on-device by default. No cloud upload without explicit operator authorization per source.
- Client names, financial figures, and personal data **never** appear in commits, public artifacts, or anything pushed to a remote.
- Receipts may carry SHA-256 of document contents but **not the contents themselves** when receipts are pointer-linked to HELEN's ledger.
- Local receipts under `~/Documents/JMT_ADMIN/receipts/` may carry richer metadata (still not document body), as that path is private.
- The skill provides a `redact-for-public` mode for any export bundle, scrubbing client identifiers.
- `~/.helen_env` and any credential files remain mode 600 and are never logged.

---

## 11. Admin Dashboard Concept

A single-screen overview for the operator. Pure read view; actions launched from here are still gated by the confirmation rules in §8.

```
JMT ADMIN — DASHBOARD
─────────────────────
INBOX        ▸ 7 unclassified
URGENT       ▸ 2 items past due
INVOICES     ▸ 4 drafted, 9 sent unpaid (3 >30d), 21 paid this month
QUOTES       ▸ 1 drafted, 2 awaiting client, 1 won, 1 lost
TAXES        ▸ next deadline: VAT Q2 — 28 days
ACCOUNTANT   ▸ April packet ready for review
CLIENT FU    ▸ 6 follow-ups due this week
DECISIONS    ▸ 3 items requiring operator ruling
RECEIPTS     ▸ last 7 days: 42 actions logged
```

Dashboard rendering target: terminal-first (CLI), browser-second. No GUI built in V1.

---

## 12. CLI Commands

Suggested verbs (V1, non-binding):

```bash
python -m helen_os.cli.helen admin inbox scan
python -m helen_os.cli.helen admin classify <folder>
python -m helen_os.cli.helen admin brief weekly
python -m helen_os.cli.helen admin brief monthly
python -m helen_os.cli.helen admin invoice draft <client>
python -m helen_os.cli.helen admin quote draft <client>
python -m helen_os.cli.helen admin accountant-packet <month>
python -m helen_os.cli.helen admin due-dates
python -m helen_os.cli.helen admin decisions
python -m helen_os.cli.helen admin receipt-log
python -m helen_os.cli.helen admin confirm <action_id>   # operator-only confirmation step
```

Flags:
- `--dry-run` (default for any mutating command on first run)
- `--apply` (actually mutate; emits receipt)
- `--ledger-link` (emit a ledger-spine pointer via `helen_say.py`)
- `--public` (redact client identifiers in any output bundle)

---

## 13. Future Integrations

Each requires explicit operator authorization and its own proposal extension. Phase column is indicative.

| Integration | Purpose | Phase |
|---|---|---|
| Gmail MCP connector | Inbox scan, email drafting, thread tracking (read-only first; sending is a separate later step) | Phase 2 |
| Google Drive MCP connector | Document sync, client folder creation | Phase 2 |
| Google Calendar MCP connector | Due-date injection, reminder surfacing | Phase 2 |
| Bank statement intake | Read-only API or local PDF intake (no payment authorization) | Phase 2 |
| OCR for paper documents | Tesseract local first; cloud OCR only with explicit consent per document batch | Phase 3 |
| PDF generation | Local renderers (WeasyPrint / LaTeX) only; no cloud renderers | Phase 3 |
| Accounting software | Pennylane / Sage / QuickBooks read-only sync first; write integrations are a separate proposal | Phase 3 |
| Government portals | impots.gouv.fr, URSSAF — **explicitly NOT in any V1+ roadmap; remain operator-manual** | Never |

No integration may be enabled without operator review and explicit activation. Cloud-side processing of any tax / VAT / banking data is barred without per-batch operator consent.

---

## 14. Minimal Acceptance Tests

A V1 implementation must pass the following before any merge:

1. **Receipt invariant** — every mutation produces a receipt; no mutation appears in filesystem without a corresponding receipt JSON.
2. **DRAFT containment** — emails/invoices/quotes never leave DRAFT state without a `JMT_ADMIN_CONFIRMATION_V1` receipt referencing them.
3. **Forbidden-action firewall** — every forbidden action listed in §9 has a unit test that proves the skill refuses it (or refuses to even reach it).
4. **No-mutation-of-original** — original documents are read-only; renaming/moving operates on copies if the source isn't already inside JMT_INBOX.
5. **Confirmation chain auditability** — for any sent invoice or sent email in test fixtures, the chain `DRAFT receipt → CONFIRMATION receipt → SEND receipt` exists and is hash-linked.
6. **Privacy redaction** — `--public` mode produces zero client identifiers in any output stream (regex-validated against a fixture client list).
7. **CLI dry-run safety** — running any mutating command without `--apply` produces no filesystem changes.
8. **Ledger-link opt-in** — without `--ledger-link`, no entry reaches `town/ledger_v1.ndjson` even via `helen_say.py`.

---

## 15. Final Receipt

```
[RECEIPT] 2026-04-28
schema:                  JMT_ADMIN_SKILL_PROPOSAL_RECEIPT_V1
document:                docs/proposals/JMT_ADMIN_SKILL_V1.md
action:                  proposal_created
authority:               NON_SOVEREIGN
canon:                   NO_SHIP
lifecycle:               PROPOSAL

implementation_scope:    JMT_ADMIN_SKILL_DOC_ONLY
commit_status:           NO_COMMIT
push_status:             NO_PUSH
gui_built:               NO
email_connected:         NO
bank_connected:          NO
submission_made:         NO

operator:                JM
next_verb:               review admin skill
```

This document is a proposal only. Nothing in it has been implemented, committed, or deployed. All described behaviors require operator review and explicit activation before any code is written or run.

---

*JMT Admin Skill does not replace the operator. It clears the fog, prepares the packet, and waits for confirmation.*
