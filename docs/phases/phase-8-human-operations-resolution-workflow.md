# Phase 8 — Human Operations & Resolution Workflow


## 1. Overview

Phase 8 establishes a governed human-resolution layer on top of the deterministic exception and controlled-remediation system built in Phases 1–7.

The core project principle remains:

> **AI recommends; deterministic business logic authorizes; controlled workflows execute; humans retain resolution authority; everything important is audited.**

Phase 8 strengthens the final human decision boundary by making human acknowledgement and resolution explicit, validated, persisted, and auditable.

---

## 2. Objectives

Phase 8 was completed in four subphases:

### 8.1 Human Resolution Contract
Introduced a structured request contract requiring a valid resolution reason and a non-empty resolution note.

### 8.2 Resolution Validation + Persistence
Added persistent resolution metadata and a resolution timestamp to `ExceptionRecord`.

### 8.3 Human Lifecycle Audit Evidence
Added dedicated audit events for human acknowledgement and human resolution, including transition evidence.

### 8.4 End-to-End Resolution Verification
Verified valid and invalid inputs, lifecycle guardrails, audit evidence, and regression against the Phase 7 governance baseline.

---

## 3. Human Resolution Lifecycle

The lifecycle intentionally remains:

```text
OPEN
  │
  │ Acknowledge
  ▼
ACKNOWLEDGED
  │
  │ Resolve with reason + note
  ▼
RESOLVED
```

Allowed transitions:

```text
OPEN → ACKNOWLEDGED
ACKNOWLEDGED → RESOLVED
```

Rejected transitions include:

```text
OPEN → RESOLVED
RESOLVED → ACKNOWLEDGED
RESOLVED → RESOLVED
```

`RESOLVED` is terminal.

---

## 4. Phase 8.1 — Human Resolution Contract

### File

```text
backend/app/schemas/resolution.py
```

### Contract

```python
from enum import Enum

from pydantic import BaseModel, Field


class ResolutionReason(str, Enum):
    SETTLEMENT_CONFIRMED = "SETTLEMENT_CONFIRMED"
    MANUAL_RECONCILIATION = "MANUAL_RECONCILIATION"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    DUPLICATE_EXCEPTION = "DUPLICATE_EXCEPTION"
    OTHER = "OTHER"


class ExceptionResolutionRequest(BaseModel):
    resolution_reason: ResolutionReason
    resolution_note: str = Field(
        min_length=1,
        max_length=1000,
    )
```

### Validation

`resolution_reason` must be one of the five defined values.

`resolution_note` must contain between 1 and 1000 characters.

This prevents an exception from being resolved without structured human rationale.

---

## 5. Phase 8.2 — Resolution Metadata Persistence

### Migration

```text
backend/alembic/versions/3aa18e2e7797_add_exception_resolution_metadata.py
```

Revision:

```text
3aa18e2e7797
```

Previous revision:

```text
e7f4a9c21b6d
```

### Added database fields

```text
resolution_reason VARCHAR(50) NULL
resolution_note   TEXT NULL
resolved_at       TIMESTAMP WITH TIME ZONE NULL
```

### Model

`ExceptionRecord` now stores:

```python
resolution_reason: Mapped[str | None] = mapped_column(
    String(50),
    nullable=True,
)

resolution_note: Mapped[str | None] = mapped_column(
    Text,
    nullable=True,
)

resolved_at: Mapped[datetime | None] = mapped_column(
    DateTime(timezone=True),
    nullable=True,
)
```

`resolved_at` is populated during the human `ACKNOWLEDGED → RESOLVED` transition.

---

## 6. Resolution Semantics

A valid resolution performs:

1. Validate lifecycle state.
2. Validate request body.
3. Persist resolution reason.
4. Persist resolution note.
5. Set `resolved_at`.
6. Transition status to `RESOLVED`.
7. Commit and refresh.
8. Record `EXCEPTION_RESOLVED` audit evidence.
9. Return the lifecycle state.

Human resolution does **not** create or execute a controlled financial remediation action.

---

## 7. Phase 8.3 — Human Lifecycle Audit Evidence

Two audit event types were added:

```text
EXCEPTION_ACKNOWLEDGED
EXCEPTION_RESOLVED
```

Existing controlled-action audit events remain separate:

```text
CONTROLLED_ACTION_CREATED
CONTROLLED_ACTION_STARTED
CONTROLLED_ACTION_COMPLETED
CONTROLLED_ACTION_FAILED
CONTROLLED_ACTION_REJECTED
```

This makes the distinction between controlled remediation and human lifecycle decisions explicit.

### Audit transition evidence

Acknowledgement:

```text
event_type       = EXCEPTION_ACKNOWLEDGED
previous_status  = OPEN
new_status       = ACKNOWLEDGED
controlled_action_id = NULL
```

Resolution:

```text
event_type       = EXCEPTION_RESOLVED
previous_status  = ACKNOWLEDGED
new_status       = RESOLVED
controlled_action_id = NULL
```

The resolution audit message also records the selected human resolution reason.

---

## 8. Phase 8.3 Migration

Migration:

```text
backend/alembic/versions/13f3527ae092_add_human_exception_audit_events.py
```

Revision:

```text
13f3527ae092
```

Previous revision:

```text
3aa18e2e7797
```

The PostgreSQL enum type was verified as:

```text
public.auditeventtype
```

The migration adds:

```sql
ALTER TYPE public.auditeventtype
ADD VALUE IF NOT EXISTS 'EXCEPTION_ACKNOWLEDGED';

ALTER TYPE public.auditeventtype
ADD VALUE IF NOT EXISTS 'EXCEPTION_RESOLVED';
```

Downgrade intentionally does not remove enum values because PostgreSQL does not safely support removing individual enum values with `ALTER TYPE`.

Final Alembic head:

```text
13f3527ae092
```

---

## 9. Lifecycle APIs

### Acknowledge

```http
POST /exceptions/{payment_id}/acknowledge
```

Allowed only from `OPEN`.

Produces:

```text
OPEN → ACKNOWLEDGED
```

and creates an `EXCEPTION_ACKNOWLEDGED` audit event.

### Resolve

```http
POST /exceptions/{payment_id}/resolve
```

Requires:

```json
{
  "resolution_reason": "MANUAL_RECONCILIATION",
  "resolution_note": "Validated through manual reconciliation."
}
```

Allowed only from `ACKNOWLEDGED`.

Produces:

```text
ACKNOWLEDGED → RESOLVED
```

and creates an `EXCEPTION_RESOLVED` audit event.

### Lifecycle read

```http
GET /exceptions/{payment_id}/lifecycle
```

Now exposes:

```text
payment_id
status
created_at
updated_at
resolution_reason
resolution_note
resolved_at
controlled_actions
```

---

## 10. Validation Verification

### Invalid resolution reason

Submitted:

```json
{
  "resolution_reason": "INVALID_REASON",
  "resolution_note": "This should be rejected."
}
```

Result:

```text
HTTP 422 Unprocessable Entity
```

The request was rejected by schema validation.

Database remained:

```text
status            = ACKNOWLEDGED
resolution_reason = NULL
resolution_note   = NULL
resolved_at       = NULL
```

Therefore invalid input did not mutate business state.

### Empty resolution note

Submitted:

```json
{
  "resolution_reason": "SETTLEMENT_CONFIRMED",
  "resolution_note": ""
}
```

Result:

```text
HTTP 422 Unprocessable Entity
```

The API reported that the string must contain at least one character.

Database again remained:

```text
status            = ACKNOWLEDGED
resolution_reason = NULL
resolution_note   = NULL
resolved_at       = NULL
```

---

## 11. End-to-End Resolution Verification

Test record:

```text
phase8_invalid_reason_test_001
```

Verified lifecycle:

```text
OPEN
  ↓
ACKNOWLEDGED
  ↓
RESOLVED
```

Final persisted values:

```text
resolution_reason = MANUAL_RECONCILIATION

resolution_note =
Validated through manual reconciliation during Phase 8 verification.

resolved_at =
2026-09-04T11:42:39.859675Z
```

No controlled actions were created for this test record.

---

## 12. Audit Verification

The test record generated exactly two human lifecycle audit events.

### Audit event 22

```text
event_type           = EXCEPTION_ACKNOWLEDGED
previous_status      = OPEN
new_status            = ACKNOWLEDGED
controlled_action_id = NULL
```

### Audit event 23

```text
event_type           = EXCEPTION_RESOLVED
previous_status      = ACKNOWLEDGED
new_status            = RESOLVED
controlled_action_id = NULL
```

The resolution event message recorded:

```text
Resolution reason: MANUAL_RECONCILIATION.
```

This proves human lifecycle decisions are independently auditable.

---

## 13. Terminal-State Verification

After resolution:

```text
RESOLVED → ACKNOWLEDGED
```

was rejected with HTTP 400.

Also:

```text
RESOLVED → RESOLVED
```

was rejected with HTTP 400.

Rejected transitions did not create additional lifecycle audit events.

---

## 14. Phase 7 Regression

The original six-exception Phase 7 dataset remained unchanged.

Expected and current values:

```text
total_exceptions                  = 6
action_required_count             = 1
in_progress_count                 = 0
human_resolution_required_count   = 1
monitor_count                     = 0
no_action_required_count          = 4
total_known_financial_impact      = 15500.00
outstanding_control_count         = 2
```

Regression: **PASS**

---

## 15. Risk Queue Regression

The critical payment `2` remained:

```text
category              = MISSING_SETTLEMENT
severity              = HIGH
financial_impact      = 15000.00
priority_score        = 100
remediation_status    = COMPLETED
attention_status      = HUMAN_RESOLUTION_REQUIRED
governance_level      = HIGH
escalation_required   = TRUE
```

`pay_test_001` remained:

```text
category              = INVALID_STATE
severity              = HIGH
priority_score        = 75
remediation_status    = NOT_STARTED
attention_status      = ACTION_REQUIRED
governance_level      = HIGH
escalation_required   = TRUE
```

Previously resolved exceptions continued to produce:

```text
RESOLVED
→ NO_ACTION_REQUIRED
→ NORMAL
→ escalation_required = FALSE
```

Regression: **PASS**

---

## 16. Governance Regression

`GET /control/governance` continued to return exactly the two exceptions requiring escalation:

```text
payment_id = 2
priority = 100
governance_level = HIGH
escalation_required = TRUE
```

and:

```text
payment_id = pay_test_001
priority = 75
governance_level = HIGH
escalation_required = TRUE
```

Regression: **PASS**

---

## 17. Critical Safety Invariant — Payment `2`

Payment `2` remained intentionally unresolved.

Final relevant state:

```text
MISSING_SETTLEMENT
HIGH
financial impact = 15000.00
priority = 100
remediation = COMPLETED
human review = REQUIRED
governance = HIGH
escalation = TRUE
```

Existing controlled actions remained:

```text
Action 6 → COMPLETED
Action 7 → COMPLETED
```

No additional controlled action was created.

The exception was not resolved during Phase 8 testing.

This preserves the core invariant:

> **Controlled Action COMPLETED != Exception RESOLVED**

A legitimate human-resolution workflow is still required.

---

## 18. Files Added

```text
backend/app/schemas/resolution.py

backend/alembic/versions/3aa18e2e7797_add_exception_resolution_metadata.py

backend/alembic/versions/13f3527ae092_add_human_exception_audit_events.py
```

## Files Updated

```text
backend/app/models/exception.py

backend/app/schemas/exception_lifecycle.py

backend/app/core/api/routes/exceptions.py

backend/app/models/audit_log.py

backend/app/services/audit_log.py
```

---

## 19. Architectural Decisions

### Keep the lifecycle unchanged

Retained:

```text
OPEN → ACKNOWLEDGED → RESOLVED
```

No extra lifecycle states were introduced.

### Require human resolution evidence

Every resolution requires:

```text
resolution_reason
resolution_note
```

### Separate remediation from resolution

Completing a controlled action never automatically resolves the exception.

### Separate human and controlled-action audit events

Human lifecycle events use their own event types and do not masquerade as remediation events.

### Validate before mutation

Malformed resolution requests are rejected at the API schema boundary.

### Preserve historical audit records

Older audit records are not rewritten to manufacture transition evidence that did not exist when they were created.

---

## 20. Known Limitations

### Audit transaction atomicity

`create_audit_log()` currently commits independently. Lifecycle persistence and audit persistence are therefore not yet one atomic database transaction.

### Concurrency

Database row locking/versioning for concurrent lifecycle transitions remains deferred.

### Operator identity

The current audit model records human lifecycle activity but does not yet attach a full authenticated operator identity.

### Temporary test data

Phase 8 introduced isolated test records. Cleanup should be deliberate and should not affect the curated Phase 7 demonstration dataset.

---

## 21. Verification Checklist

- [x] Human resolution request contract created
- [x] Resolution reason enum created
- [x] Resolution note validation added
- [x] Resolution metadata persisted
- [x] Resolution timestamp persisted
- [x] Lifecycle response expanded
- [x] Human acknowledgement audit event added
- [x] Human resolution audit event added
- [x] Transition evidence recorded
- [x] PostgreSQL audit enum migration completed
- [x] Invalid reason rejected with 422
- [x] Invalid reason caused no DB mutation
- [x] Empty note rejected with 422
- [x] Empty note caused no DB mutation
- [x] Valid resolution verified
- [x] Resolution metadata verified
- [x] Human audit evidence verified
- [x] Terminal-state guardrails verified
- [x] No controlled action created by human resolution
- [x] Phase 7 summary regression passed
- [x] Phase 7 risk queue regression passed
- [x] Phase 7 governance regression passed
- [x] Payment `2` remained unresolved and escalation-required
- [x] `python -m compileall app` passed
- [x] Alembic head verified

---

## 22. Final Outcome

Phase 8 establishes a governed human decision boundary.

The system now distinguishes:

```text
1. Exception exists
2. Controlled remediation completed
3. Human formally resolved the exception
```

These are separate business concepts.

The resulting control chain is:

```text
AI / Intelligence
        │
        ▼
Deterministic Exception Classification
        │
        ▼
Deterministic Controller
        │
        ▼
Controlled Remediation
        │
        ▼
Human Acknowledgement
        │
        ▼
Human Resolution Decision
        │
        ▼
Audited RESOLVED State
```

The system remains:

- deterministic where financial truth matters,
- controlled where actions are executed,
- human-governed where final resolution occurs,
- auditable throughout important lifecycle transitions.

# Phase 8 Status

> **COMPLETE AND VERIFIED**

---

## 23. Next Phase Direction

The planned next phase is:

# Phase 9 — Advanced Settlement Intelligence

The next phase should increase analytical depth without weakening the human-control boundary.

Potential areas:

- richer historical settlement analysis,
- recurring exception patterns,
- anomaly/context signals,
- exception clustering,
- merchant/payment behavior patterns,
- stronger investigation context,
- AI-assisted analytical explanations.

The guiding principle remains:

> **More intelligence, not more autonomy.**

Phase 9 should first be analyzed against the architecture established through Phases 1–8 before implementation begins. The planned phase order can be challenged if a stronger architectural sequence is identified.
