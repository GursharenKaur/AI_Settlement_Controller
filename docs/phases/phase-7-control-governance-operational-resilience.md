# Phase 7 — Control Governance & Operational Resilience

## AI Settlement Controller — Razorpay Buildathon

---

## 1. Purpose

Phase 7 turns the existing operational risk/control layer into a governed settlement-operations control system.

The core project principle remains:

> **AI recommends; deterministic business logic authorizes; controlled workflows execute; humans retain resolution authority; everything important is audited.**

Phase 7 adds:

- hardened control-state transitions,
- deterministic exception aging,
- operational urgency,
- deterministic governance/escalation classification,
- stronger audit evidence,
- and a read-only governed operational API.

It does **not** change deterministic financial truth.

Architecture:

```text
Detect → Understand → Prioritize → Recommend → Control → Audit → Govern
```

---

## 2. Scope and Non-Goals

Phase 7 covers:

1. 7.1 — Control-State Hardening
2. 7.2 — Exception Aging & Operational Urgency
3. 7.3 — Governance / Escalation Classification
4. 7.4 — Stronger Audit / Control Evidence
5. 7.5 — Governed Operational Control API

Phase 7 deliberately does not introduce:

- automatic exception resolution,
- automatic financial correction,
- automatic escalation actions,
- email/notification workflows,
- AI-generated governance decisions,
- persisted governance state,
- new governance tables,
- changes to reconciliation truth,
- changes to priority scoring,
- changes to controller recommendations,
- or frontend implementation.

Frontend/demo presentation remains part of the later production/demonstration phase.

---

## 3. Architecture

```text
Transaction / Settlement
        ↓
Reconciliation
        ↓
Exception Intelligence
        ↓
Controller Decision
        ↓
Operational Control
     ↙       ↘
  Aging    Governance
     ↘       ↙
    Risk / Control APIs
          ↓
    Human Operators
```

Responsibilities remain separated:

| Component | Responsibility |
|---|---|
| Reconciliation | Determines deterministic financial/reconciliation truth |
| Exception Intelligence | Determines exception, severity, impact, and priority |
| Controller Decision | Determines the controlled action recommendation |
| Controlled Remediation | Executes supported operational actions |
| Exception Lifecycle | Tracks human-facing exception state |
| Exception Aging | Determines how old an exception is |
| Governance | Determines how it should be governed/escalated |
| Audit | Records control activity and transition evidence |
| Operational APIs | Expose derived control state |

---

# 4. Phase 7.1 — Control-State Hardening

## 4.1 Exception Lifecycle

The supported lifecycle is:

```text
OPEN → ACKNOWLEDGED → RESOLVED
```

Rules:

- `OPEN` can transition to `ACKNOWLEDGED`.
- `ACKNOWLEDGED` can transition to `RESOLVED`.
- Invalid transitions are rejected.
- Resolved exceptions cannot be transitioned again through invalid operations.
- Lifecycle reads are read-only.

The previous read-side `get_or_create_exception_record()` behavior was removed from lifecycle access.

Therefore:

> A GET operation must not create an exception record as a side effect.

If no lifecycle record exists, a read request returns the appropriate not-found result.

## 4.2 Controlled Action State Machine

```text
REQUESTED → IN_PROGRESS → COMPLETED
                         ↘ FAILED
```

Rules:

- start only from `REQUESTED`,
- complete only from `IN_PROGRESS`,
- duplicate starts are rejected,
- duplicate completions are rejected,
- invalid transitions are rejected,
- completion does not resolve the exception.

## 4.3 Critical Invariant

> **Controlled Action COMPLETED ≠ Exception RESOLVED**

A remediation action can complete successfully while the underlying exception still requires human resolution.

## 4.4 Concurrency Limitation

Phase 7.1 uses application-level transition validation.

It does not introduce database row locking or optimistic versioning. True DB-level concurrency hardening remains a later production-reliability concern.

---

# 5. Phase 7.2 — Exception Aging & Operational Urgency

## 5.1 Objective

Aging provides deterministic visibility into how long an exception has existed.

It does not change:

- reconciliation status,
- financial impact,
- priority,
- lifecycle state,
- remediation state,
- or controller recommendation.

## 5.2 Authoritative Timestamp

The authoritative aging timestamp is:

```text
ExceptionRecord.created_at
```

Reason:

> It represents entry into the operational exception lifecycle.

The following are intentionally not used as the authoritative exception age:

- `Transaction.created_at`
- `Transaction.paid_at`
- `ExceptionRecord.updated_at`

## 5.3 Aging Calculation

```text
ExceptionRecord.created_at
        ↓
current UTC time
        ↓
age_minutes
age_hours
aging_band
```

Age is derived at request time. Negative ages are bounded at zero.

## 5.4 Aging Bands

| Age | Band |
|---|---|
| `0 ≤ age < 1 hour` | `FRESH` |
| `1 hour ≤ age < 4 hours` | `AGING` |
| `4 hours ≤ age < 24 hours` | `ATTENTION` |
| `age ≥ 24 hours` | `OVERDUE` |

Boundaries were verified at:

```text
0, 59, 60, 239, 240, 1439, 1440 minutes
```

## 5.5 Unknown Age

If an exception has no `ExceptionRecord`:

```text
age_minutes = null
age_hours   = null
aging_band  = null
```

Unknown age is never treated as `FRESH` or `OVERDUE`.

> **Unknown operational evidence remains unknown.**

## 5.6 Aging Does Not Change Priority

Aging is an operational urgency signal, not a replacement for the existing priority score.

```text
priority_score ≠ aging_score
```

## 5.7 Resolved Exceptions

A resolved exception may still display historical aging information, but attention/governance precedence makes:

```text
RESOLVED
→ NO_ACTION_REQUIRED
```

Thus a resolved overdue exception does not remain escalated merely because it is old.

---

# 6. Phase 7.3 — Governance / Escalation Classification

## 6.1 Objective

Governance converts existing operational signals into a deterministic classification.

It does not change:

- financial truth,
- priority,
- lifecycle,
- remediation,
- controller recommendation,
- or AI behavior.

Governance answers:

> **How should this exception be governed or escalated operationally?**

## 6.2 Responsibility Separation

| Service | Question |
|---|---|
| `exception_intelligence.py` | What is wrong? |
| `controller_decision.py` | What controlled action is recommended? |
| `exception_aging.py` | How old is it? |
| `governance.py` | How should it be governed/escalated? |

## 6.3 Governance Contract

```text
governance_level
escalation_required
governance_reason
```

Levels:

```text
NORMAL
ELEVATED
HIGH
CRITICAL
```

## 6.4 Deterministic Rules

1. `RESOLVED` → `NORMAL`, no escalation.
2. `IN_PROGRESS` remediation → `ELEVATED`, no escalation.
3. `HUMAN_RESOLUTION_REQUIRED` + priority ≥ 75 → `HIGH`, escalation.
4. `HUMAN_RESOLUTION_REQUIRED` → `ELEVATED`, escalation.
5. `OVERDUE` + unresolved + priority ≥ 75 → `CRITICAL`, escalation.
6. `OVERDUE` + unresolved → `HIGH`, escalation.
7. `ACTION_REQUIRED` + priority ≥ 75 → `HIGH`, escalation.
8. `ACTION_REQUIRED` → `ELEVATED`, escalation.
9. Otherwise → `NORMAL`, no escalation.

## 6.5 Unknown-Age Safeguard

Unknown age must never be treated as overdue.

For `payment_id=2`:

```text
priority_score = 100
aging_band     = null
attention      = HUMAN_RESOLUTION_REQUIRED
```

Therefore:

```text
governance_level    = HIGH
escalation_required = true
```

It is not `CRITICAL`, because there is no evidence that it is overdue.

## 6.6 AI Boundary

Governance is deterministic.

AI is not used to determine governance level, escalation, aging, lifecycle, remediation, or financial truth.

---

# 7. Phase 7.4 — Stronger Audit / Control Evidence

## 7.1 Objective

Audit evidence now answers:

1. What happened?
2. Which control/action was involved?
3. What state transition occurred?
4. When did it happen?

## 7.2 New Audit Fields

`AuditLog` now contains nullable:

```text
previous_status
new_status
```

## 7.3 Transition Evidence

Controlled-action start:

```text
REQUESTED → IN_PROGRESS
```

records:

```text
previous_status = REQUESTED
new_status      = IN_PROGRESS
```

Controlled-action completion:

```text
IN_PROGRESS → COMPLETED
```

records:

```text
previous_status = IN_PROGRESS
new_status      = COMPLETED
```

Creation events use the initial action state where applicable.

Historical audit entries created before transition evidence was wired may have null transition fields and are intentionally preserved.

## 7.4 Migration

Migration:

```text
Revision: e7f4a9c21b6d
Down revision: 832533f1f844
```

Added nullable:

```text
AuditLog.previous_status
AuditLog.new_status
```

Migration succeeded and became the active Alembic head.

No database reset was performed.

## 7.5 Audit Is Evidence, Not a Second Financial Database

The phase intentionally did not add:

- AI decision snapshots,
- risk-score snapshots,
- financial-amount snapshots,
- operator identity fields,
- or duplicated financial records.

Audit exists to provide control evidence.

## 7.6 Verified Audit State

For `payment_id=2`:

- controlled actions `6` and `7` are both `COMPLETED`,
- audit history remains intact,
- action 7 includes `IN_PROGRESS → COMPLETED`,
- action 6 includes `REQUESTED → IN_PROGRESS` and `IN_PROGRESS → COMPLETED`.

Historical records were not rewritten.

---

# 8. Phase 7.5 — Governed Operational Control API

## 8.1 Objective

Phase 7.5 exposes governance through a focused deterministic read-only API.

## 8.2 New Endpoint

```http
GET /control/governance
```

Purpose:

> Return operational exceptions for which `escalation_required = true`.

The endpoint does not:

- execute actions,
- modify financial records,
- modify lifecycle state,
- modify remediation,
- resolve exceptions,
- create audit events,
- call AI,
- or persist governance state.

## 8.3 Governed Queue

```text
existing operational controls
        ↓
filter escalation_required = true
        ↓
deterministic governance ordering
        ↓
return governed controls
```

Governance rank:

```text
CRITICAL = 4
HIGH     = 3
ELEVATED = 2
NORMAL   = 1
```

Priority and known financial impact are used as deterministic tie-breakers.

## 8.4 Verified Governed Queue

The final dataset contains two governed cases.

### payment_id=2

```text
category              = MISSING_SETTLEMENT
severity              = HIGH
financial_impact      = 15000.00
priority_score        = 100
remediation_status    = COMPLETED
attention_status      = HUMAN_RESOLUTION_REQUIRED
governance_level      = HIGH
escalation_required   = true
```

Reason:

> Controlled remediation completed, but human resolution is still required for a high-priority exception.

### pay_test_001

```text
category              = INVALID_STATE
severity              = HIGH
financial_impact      = null
priority_score        = 75
remediation_status    = NOT_STARTED
attention_status      = ACTION_REQUIRED
governance_level      = HIGH
escalation_required   = true
```

Reason:

> Immediate operational action is required for a high-priority exception.

## 8.5 Read-Only Verification

The governed endpoint was called twice consecutively and returned the same two cases.

A subsequent detail request for `payment_id=2` confirmed:

- actions `6` and `7` remain `COMPLETED`,
- remediation remains `COMPLETED`,
- the exception remains unresolved,
- financial impact remains `15000.00`,
- priority remains `100`,
- governance remains `HIGH / true`,
- audit history remains intact.

Therefore the governed API is observational and non-mutating.

---

# 9. Operational API Surface After Phase 7

Control APIs:

```http
GET /control/exceptions
GET /control/exceptions/{payment_id}
GET /control/exceptions/{payment_id}/detail
GET /control/summary
GET /control/governance
```

Risk APIs:

```http
GET /risk/queue
GET /risk/summary
```

The two queue concepts remain separate:

```text
/risk/queue
    → operational attention / priority view

/control/governance
    → escalation-required governance view
```

---

# 10. Final Verified Operational State

The final control/risk summary is:

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

The highest-priority actionable exception is:

```text
payment_id = pay_test_001
priority   = 75
```

Payment `2` has priority `100` but is now in:

```text
HUMAN_RESOLUTION_REQUIRED
```

because its controlled remediation has completed.

---

# 11. Verified Risk Queue

Final ordering:

```text
1. pay_test_001
2. 2
3. pay_recon_over_001
4. pay_recon_currency_001
5. pay_recon_invalid_001
6. pay_recon_mismatch_001
```

Governance:

```text
pay_test_001
    HIGH
    escalation_required = true

payment_id=2
    HIGH
    escalation_required = true

resolved cases
    NORMAL
    escalation_required = false
```

Resolved overdue cases remain non-escalated because resolved-state precedence wins.

---

# 12. Safety Properties

## Financial truth preserved

Known financial impact remains:

```text
15500.00
```

No governance operation changes financial records.

## Human resolution preserved

Payment `2` demonstrates:

```text
remediation_status     = COMPLETED
exception unresolved   = true
human_review_required  = true
```

## Unknown financial impact preserved

Cases without a safely determinable financial amount retain:

```text
financial_impact = null
```

## Unknown age preserved

Payment `2` retains:

```text
age_minutes = null
age_hours   = null
aging_band  = null
```

It is not incorrectly treated as overdue.

## Read-only control surfaces remain read-only

GET operational endpoints do not create records, execute actions, resolve exceptions, modify financial data, or create audit events.

---

# 13. Database Changes

Phase 7 introduced only the audit evidence migration:

```text
AuditLog.previous_status
AuditLog.new_status
```

No governance state is persisted.

No aging state is persisted.

No new governance tables were introduced.

Aging and governance are derived from authoritative existing state at request time.

---

# 14. Design Decisions

## 14.1 ExceptionRecord.created_at is authoritative for age

It represents entry into the operational exception lifecycle.

## 14.2 Aging is derived

Age changes continuously with time, so persisting it would introduce unnecessary synchronization.

## 14.3 Unknown age remains null

The system must not manufacture operational evidence.

## 14.4 Governance is deterministic

Governance affects operational escalation and must be predictable, testable, and explainable.

## 14.5 Resolved state has precedence

A resolved exception does not remain escalated merely because historical aging is overdue.

## 14.6 Remediation completion does not resolve an exception

Execution success does not prove that the underlying financial/operational problem is resolved.

## 14.7 Audit transition fields are nullable

Not every audit event represents a state transition.

## 14.8 Historical audit evidence is preserved

Existing evidence is not rewritten after new evidence capabilities are introduced.

## 14.9 Governance API is read-only

Governance visibility must not become an execution path.

---

# 15. Known Limitations

## Database-level concurrency

No row locking or optimistic versioning was added. Application-level validation remains the current mechanism.

## Historical audit entries

Older events may have null transition fields because they were created before transition evidence was introduced.

## Settlement payment_id limitation

The existing settlement `payment_id` non-unique limitation is preserved. Reconciliation behavior is unchanged.

## Simulated remediation

Controlled action execution remains simulated and does not perform real financial correction.

---

# 16. Verification Summary

Phase 7 verification covered:

### Control summary

```text
6 exceptions
1 action required
1 human resolution required
4 no action required
0 in progress
15500.00 known financial impact
2 outstanding controls
```

### Risk queue

Verified:

- existing deterministic ordering,
- governance propagation,
- attention-state correctness,
- resolved-state precedence,
- aging behavior,
- unknown-age behavior.

### Risk summary

Verified consistency with the control summary.

### Governed queue

Verified:

- only escalation-required cases are returned,
- governance classifications are correct,
- deterministic ordering is preserved,
- repeated reads are non-mutating.

### Detail/audit view

Verified:

- actions `6` and `7` remain completed,
- payment `2` remains unresolved,
- audit evidence remains intact,
- transition evidence is preserved,
- read-only requests do not create additional audit events.

---

# 17. Phase 7 Completion Criteria

Phase 7 is complete because the system now provides:

- hardened operational state transitions,
- deterministic exception aging,
- explicit operational urgency,
- deterministic governance classification,
- escalation-required visibility,
- stronger audit evidence,
- a read-only governance API,
- preservation of financial truth,
- explicit human resolution authority,
- and regression-verified control/risk APIs.

The resulting control system is:

```text
Deterministic
Auditable
Read-only where appropriate
Human-controlled
AI-bounded
Financially non-mutating
```

---

# 18. End-to-End Control Flow

```text
                    ┌─────────────────────┐
                    │ Transaction /       │
                    │ Settlement Data     │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Reconciliation      │
                    │ Deterministic Truth │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Exception           │
                    │ Intelligence        │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Controller Decision │
                    │ Recommended Action  │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Controlled          │
                    │ Remediation         │
                    └──────────┬──────────┘
                               ↓
                 ┌─────────────┴─────────────┐
                 ↓                           ↓
        ┌──────────────────┐       ┌──────────────────┐
        │ Exception        │       │ Audit Evidence   │
        │ Lifecycle        │       │                  │
        └────────┬─────────┘       └──────────────────┘
                 ↓
        ┌──────────────────┐
        │ Aging            │
        └────────┬─────────┘
                 ↓
        ┌──────────────────┐
        │ Governance       │
        │ Classification   │
        └────────┬─────────┘
                 ↓
        ┌────────────────────────────┐
        │ Operational Control / Risk │
        │ / Governance APIs          │
        └─────────────┬──────────────┘
                      ↓
              ┌───────────────┐
              │ Human         │
              │ Operators     │
              └───────────────┘
```

The authority boundary remains:

```text
AI recommends
      ↓
Deterministic system controls
      ↓
Controlled remediation
      ↓
Human resolution
      ↓
Audit evidence
```

---

# 19. Transition to Phase 8

Phase 7 establishes the governance and operational-control foundation required for human operations.

The system can now answer:

- What is wrong?
- How severe is it?
- What is the known financial impact?
- How urgent is it?
- What controlled action is recommended?
- What remediation has occurred?
- How should the case be governed?
- Does it require escalation?
- What audit evidence exists?
- Does a human still need to resolve it?

The next logical layer is:

> **Phase 8 — Human Operations & Resolution Workflow**

Phase 8 should build on the existing state rather than replace it.

The core principle remains:

> **The system can detect, explain, prioritize, recommend, govern, and provide controlled operational actions — but final exception resolution remains an explicit human decision.**
