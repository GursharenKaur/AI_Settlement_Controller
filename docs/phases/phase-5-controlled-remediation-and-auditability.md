# Phase 5 --- Controlled Remediation & Auditability

## 1. Overview

Phase 5 extends the AI Settlement Controller from exception detection
and AI-assisted decisioning into a **controlled, auditable remediation
workflow**.

The central design principle is:

> **AI recommends. Deterministic controller logic authorizes the action
> class. Controlled workflows execute only permitted operational
> actions. Human review remains authoritative for exception resolution.
> Every remediation step is audited.**

Phase 5 does **not** allow an LLM to directly move money, alter
settlement records, or arbitrarily execute financial operations.

The resulting flow is:

``` text
Transactions + Settlements
        ↓
Reconciliation
        ↓
Exception Intelligence
        ↓
Financial Impact + Priority
        ↓
Exception Lifecycle
        ↓
Trusted AI Context
        ↓
Gemini Analysis
        ↓
Controller Decision
        ↓
Controlled Remediation Workflow
        ↓
Action Validation / Safety Boundary
        ↓
Operational Action
        ↓
Action Result / State
        ↓
Audit Log
        ↓
Human Review / Resolution
```

------------------------------------------------------------------------

# 2. Phase 5 Objectives

Phase 5 provides:

1.  A controlled action domain model.
2.  Persistent controlled-action state.
3.  Deterministic validation of permitted actions.
4.  API-based creation of controlled remediation requests.
5.  Controlled execution with explicit state transitions.
6.  Action results and execution timestamps.
7.  Append-only audit records for remediation events.
8.  Integration between controlled actions and exception lifecycle.
9.  Explicit human acknowledgement and resolution.
10. End-to-end verification that remediation does not modify underlying
    financial records.

------------------------------------------------------------------------

# 3. Controlled Action Domain Model

## File

``` text
backend/app/models/controlled_action.py
```

## Controlled Action Types

``` text
INVESTIGATE_MISSING_SETTLEMENT
REVIEW_SETTLEMENT_AMOUNT
REVIEW_CURRENCY_MISMATCH
INVESTIGATE_INVALID_STATE
```

## Controlled Action Statuses

``` text
REQUESTED
IN_PROGRESS
COMPLETED
FAILED
REJECTED
```

The current execution workflow uses:

``` text
REQUESTED
    ↓
IN_PROGRESS
    ↓
COMPLETED
```

------------------------------------------------------------------------

# 4. Action Authorization Rules

The deterministic controller maps exception categories to permitted
controlled actions.

  Exception Category   Permitted Controlled Action
  -------------------- --------------------------------
  MISSING_SETTLEMENT   INVESTIGATE_MISSING_SETTLEMENT
  UNDER_SETTLEMENT     REVIEW_SETTLEMENT_AMOUNT
  OVER_SETTLEMENT      REVIEW_SETTLEMENT_AMOUNT
  CURRENCY_MISMATCH    REVIEW_CURRENCY_MISMATCH
  INVALID_STATE        INVESTIGATE_INVALID_STATE

Additional safety rules:

-   No controlled action is permitted for a non-exception.
-   No controlled action is permitted for a resolved exception.
-   A requested action must match the expected action for its exception
    category.
-   Unsupported exception categories cannot produce controlled actions.
-   Invalid action-category combinations are rejected before execution.

This creates a deterministic safety boundary between AI/controller
recommendations and operational execution.

------------------------------------------------------------------------

# 5. Action Validation Service

## File

``` text
backend/app/services/controlled_action_validation.py
```

## Purpose

The validation service ensures that the requested action is consistent
with the controller decision and exception category.

Main function:

``` text
validate_controller_action(
    decision,
    requested_action
)
```

Valid requests return:

``` text
(True, "Controlled action is permitted.")
```

Invalid requests return:

``` text
(False, <reason>)
```

For example, an `UNDER_SETTLEMENT` exception permits:

``` text
REVIEW_SETTLEMENT_AMOUNT
```

but does not permit:

``` text
INVESTIGATE_INVALID_STATE
```

This prevents an AI recommendation or API caller from bypassing the
deterministic action policy.

------------------------------------------------------------------------

# 6. Controlled Action Creation API

## File

``` text
backend/app/core/api/routes/controlled_actions.py
```

## Endpoint

``` http
POST /controlled-actions
```

## Request

``` json
{
  "payment_id": "pay_recon_invalid_001",
  "action_type": "INVESTIGATE_INVALID_STATE"
}
```

## Processing Flow

The endpoint:

1.  Locates the payment through reconciliation.
2.  Determines the exception category.
3.  Retrieves the exception lifecycle state.
4.  Builds the deterministic controller decision.
5.  Converts the requested action into the controller action
    representation.
6.  Validates the action through the controlled-action validation
    service.
7.  Rejects unauthorized actions.
8.  Creates a `ControlledAction`.
9.  Sets its initial status to `REQUESTED`.
10. Stores the controller decision reason as the action reason.
11. Creates a `CONTROLLED_ACTION_CREATED` audit event.
12. Returns the created action.

A newly created action starts as:

``` text
status = REQUESTED
```

Before execution:

``` text
result = null
executed_at = null
```

------------------------------------------------------------------------

# 7. Controlled Action Execution

## File

``` text
backend/app/services/controlled_action_execution.py
```

## Endpoint

``` http
POST /controlled-actions/{action_id}/execute
```

## Execution Lifecycle

``` text
REQUESTED
    ↓
IN_PROGRESS
    ↓
COMPLETED
```

### Start Operation

`start_controlled_action()`:

-   Requires the action to be `REQUESTED`.
-   Changes the status to `IN_PROGRESS`.
-   Persists the change.
-   Creates a `CONTROLLED_ACTION_STARTED` audit event.

### Completion Operation

`complete_controlled_action()`:

-   Requires the action to be `IN_PROGRESS`.
-   Changes the status to `COMPLETED`.
-   Stores the execution result.
-   Records the execution timestamp.
-   Persists the change.
-   Creates a `CONTROLLED_ACTION_COMPLETED` audit event.

### State Protection

An already completed action cannot be executed again.

``` text
COMPLETED → execute
```

is rejected.

------------------------------------------------------------------------

# 8. Action Results and Execution State

## Migration

``` text
backend/alembic/versions/bcf9531b54e8_add_controlled_action_results.py
```

Added fields:

``` text
result
executed_at
```

A completed action contains:

``` text
status      = COMPLETED
result      = Controlled action completed successfully.
executed_at = <execution timestamp>
```

This separates:

-   What action was requested.
-   What state the action reached.
-   What result was produced.
-   When execution occurred.

------------------------------------------------------------------------

# 9. Auditability

## Model

``` text
backend/app/models/audit_log.py
```

## Service

``` text
backend/app/services/audit_log.py
```

## Migration

``` text
backend/alembic/versions/832533f1f844_add_audit_logs.py
```

## Audit Event Types

``` text
CONTROLLED_ACTION_CREATED
CONTROLLED_ACTION_STARTED
CONTROLLED_ACTION_COMPLETED
CONTROLLED_ACTION_FAILED
CONTROLLED_ACTION_REJECTED
```

## Audit Log Fields

``` text
id
payment_id
controlled_action_id
event_type
message
created_at
```

The audit log intentionally does not depend on a foreign-key
relationship to the controlled action. This keeps the audit trail
independent and suitable for append-only operational history.

------------------------------------------------------------------------

# 10. Successful Remediation Audit Trail

For controlled action `5`, the verified audit trail was:

``` text
5  CONTROLLED_ACTION_CREATED
6  CONTROLLED_ACTION_STARTED
7  CONTROLLED_ACTION_COMPLETED
```

All three events referenced:

``` text
controlled_action_id = 5
```

The messages confirmed:

``` text
Controlled action 5 created
Controlled action 5 started execution
Controlled action 5 completed successfully
```

This proves that the remediation lifecycle is traceable from creation
through successful completion.

------------------------------------------------------------------------

# 11. Rejected Action Audit Trail

Phase 5 also verified the negative path.

An intentionally incorrect action was submitted for an exception.

The system returned:

``` text
HTTP 400
```

The rejection was also recorded as:

``` text
CONTROLLED_ACTION_REJECTED
```

This ensures that failed authorization attempts are also operationally
visible and auditable.

------------------------------------------------------------------------

# 12. Exception Lifecycle Integration

## Service

``` text
backend/app/services/exception_lifecycle.py
```

## Schema

``` text
backend/app/schemas/exception_lifecycle.py
```

The exception lifecycle response now includes controlled actions
associated with the exception.

The response exposes:

``` text
payment_id
status
created_at
updated_at
controlled_actions
```

Each controlled action includes:

``` text
id
action_type
status
result
executed_at
```

This connects:

``` text
Exception
    ↕
Controlled Remediation
```

without making the remediation workflow responsible for resolving the
exception.

------------------------------------------------------------------------

# 13. Critical Safety Decision --- No Automatic Resolution

A controlled action completing does **not** automatically resolve the
exception.

This is an intentional architectural decision.

Example:

``` text
Exception
    ↓
OPEN

Controlled Action
    ↓
COMPLETED

Exception
    ↓
STILL OPEN
```

The exception lifecycle remains authoritative.

The lifecycle is:

``` text
OPEN
  ↓
ACKNOWLEDGED
  ↓
RESOLVED
```

Resolution remains an explicit human-controlled operation.

An investigation or review action may complete without proving that the
underlying financial exception has actually been corrected.

Therefore:

``` text
Action Completed
```

must not be interpreted as:

``` text
Exception Resolved
```

This is a critical financial-control boundary.

------------------------------------------------------------------------

# 14. Human Review Boundary

The architecture intentionally separates responsibilities.

## AI Layer

``` text
Analyze
Explain
Prioritize
Recommend
```

## Deterministic Controller

``` text
Interpret recommendation
Map exception → permitted action
Enforce safety rules
Require human review where appropriate
```

## Controlled Workflow

``` text
Execute only an allowed operational action
Track action state
Record result
```

## Human

``` text
Acknowledge
Review
Resolve
```

Therefore the system follows:

``` text
Detect
   ↓
Understand
   ↓
Prioritize
   ↓
Recommend
   ↓
Control
   ↓
Audit
```

rather than:

``` text
Detect
   ↓
LLM decides
   ↓
Money moves automatically
```

------------------------------------------------------------------------

# 15. Database Changes

Phase 5 introduced three database migrations.

## Migration 1 --- Controlled Actions

``` text
Revision:
9e28d8768411

Down Revision:
d12f6209e0b3

File:
backend/alembic/versions/9e28d8768411_add_controlled_actions.py
```

Creates:

``` text
controlled_actions
```

## Migration 2 --- Action Results

``` text
Revision:
bcf9531b54e8

Down Revision:
9e28d8768411

File:
backend/alembic/versions/bcf9531b54e8_add_controlled_action_results.py
```

Adds:

``` text
result
executed_at
```

## Migration 3 --- Audit Logs

``` text
Revision:
832533f1f844

Down Revision:
bcf9531b54e8

File:
backend/alembic/versions/832533f1f844_add_audit_logs.py
```

Creates:

``` text
audit_logs
```

## Final Alembic Head

``` text
832533f1f844
```

------------------------------------------------------------------------

# 16. Phase 5.9 End-to-End Verification

Existing exception:

``` text
payment_id = pay_recon_invalid_001
```

was used for end-to-end verification.

This avoided unnecessary duplicate test data and avoided resetting the
existing database.

------------------------------------------------------------------------

## Checkpoint 1 --- Reconciliation

Verified:

``` text
payment_id            = pay_recon_invalid_001
status                = INVALID_STATE
expected_amount       = 5000.00
actual_settled_amount = 5000.00
drift                  = NONE
drift_direction       = NONE
transaction_currency  = INR
settlement_currency   = INR
```

**Result: PASS**

------------------------------------------------------------------------

## Checkpoint 2 --- Exception Intelligence

Verified:

``` text
is_exception     = true
category         = INVALID_STATE
severity         = HIGH
financial_impact = None
priority_score   = 75
```

**Result: PASS**

------------------------------------------------------------------------

## Checkpoint 3 --- Controller Decision

Verified:

``` text
exception_category    = INVALID_STATE
recommended_action    = INVESTIGATE_INVALID_STATE
priority_score        = 75
human_review_required = true
```

Decision reason:

``` text
The transaction and settlement states form an invalid operational
combination and require investigation.
```

**Result: PASS**

------------------------------------------------------------------------

## Checkpoint 4 --- Controlled Action Creation

Created:

``` text
action_id   = 5
payment_id  = pay_recon_invalid_001
action_type = INVESTIGATE_INVALID_STATE
status      = REQUESTED
```

Reason:

``` text
The transaction and settlement states form an invalid operational
combination and require investigation.
```

**Result: PASS**

------------------------------------------------------------------------

## Checkpoint 5 --- Controlled Action Execution

Executed action `5`.

Verified:

``` text
id          = 5
payment_id  = pay_recon_invalid_001
action_type = INVESTIGATE_INVALID_STATE
status      = COMPLETED
result      = Controlled action completed successfully.
```

Execution timestamp:

``` text
2026-09-03T06:43:35.080061
```

**Result: PASS**

------------------------------------------------------------------------

## Checkpoint 6 --- Audit Trail

Verified exactly three audit events for action `5`:

``` text
CONTROLLED_ACTION_CREATED
CONTROLLED_ACTION_STARTED
CONTROLLED_ACTION_COMPLETED
```

All referenced:

``` text
controlled_action_id = 5
```

**Result: PASS**

------------------------------------------------------------------------

## Checkpoint 7 --- Lifecycle Safety

After controlled action completion:

``` text
Exception status = OPEN
Controlled action status = COMPLETED
```

This proved:

``` text
Controlled Action COMPLETED
          ≠
Exception RESOLVED
```

**Result: PASS**

------------------------------------------------------------------------

## Checkpoint 8 --- Human Acknowledgement

The exception was explicitly acknowledged.

Lifecycle changed:

``` text
OPEN
  ↓
ACKNOWLEDGED
```

The controlled action remained:

``` text
INVESTIGATE_INVALID_STATE
COMPLETED
```

**Result: PASS**

------------------------------------------------------------------------

## Checkpoint 9 --- Human Resolution

The exception was explicitly resolved.

Lifecycle changed:

``` text
ACKNOWLEDGED
  ↓
RESOLVED
```

The controlled action remained:

``` text
COMPLETED
```

This confirmed that exception resolution is independent from
controlled-action execution.

**Result: PASS**

------------------------------------------------------------------------

## Checkpoint 10 --- Final Financial Safety Verification

After the complete remediation lifecycle, reconciliation was queried
again.

Verified:

``` text
payment_id            = pay_recon_invalid_001
status                = INVALID_STATE
expected_amount       = 5000.00
actual_settled_amount = 5000.00
drift                  = NONE
drift_direction       = NONE
transaction_currency  = INR
settlement_currency   = INR
```

The underlying transaction and settlement financial data remained
unchanged.

**Result: PASS**

------------------------------------------------------------------------

# 17. Phase 5 Safety Invariants

  Safety Invariant                                                Result
  --------------------------------------------------------------- --------
  AI/controller cannot request arbitrary action classes           PASS
  Invalid action-category combinations are rejected               PASS
  Rejected actions are audited                                    PASS
  Actions begin in `REQUESTED`                                    PASS
  Actions require valid state transitions                         PASS
  Completed actions cannot be started again                       PASS
  Execution produces a result                                     PASS
  Execution records an execution timestamp                        PASS
  Action creation is audited                                      PASS
  Action start is audited                                         PASS
  Action completion is audited                                    PASS
  Controlled action completion does not auto-resolve exceptions   PASS
  Human acknowledgement remains explicit                          PASS
  Human resolution remains explicit                               PASS
  Underlying financial reconciliation data remains unchanged      PASS

------------------------------------------------------------------------

# 18. Controlled Remediation Boundary

Phase 5 implements:

``` text
Controlled Remediation
```

not:

``` text
Automatic Financial Correction
```

The current actions are operational/investigative:

``` text
Investigate missing settlement
Review settlement amount
Review currency mismatch
Investigate invalid state
```

They do not directly:

-   Transfer funds.
-   Modify transaction amounts.
-   Modify settlement amounts.
-   Fabricate financial corrections.
-   Change reconciliation results.
-   Allow an LLM to execute arbitrary financial operations.
-   Automatically resolve financial exceptions.

This preserves a strong financial-control boundary while still allowing
the system to move beyond passive anomaly detection.

------------------------------------------------------------------------

# 19. Architecture After Phase 5

``` text
┌───────────────────────────────────────────────┐
│ Transaction Foundation                       │
│ Payments / transaction records               │
└──────────────────────┬────────────────────────┘
                       ↓
┌───────────────────────────────────────────────┐
│ Settlement Ingestion                          │
│ Settlement records / CSV / batch ingestion    │
└──────────────────────┬────────────────────────┘
                       ↓
┌───────────────────────────────────────────────┐
│ Reconciliation Engine                         │
│ MATCHED / MISMATCH / MISSING / INVALID        │
└──────────────────────┬────────────────────────┘
                       ↓
┌───────────────────────────────────────────────┐
│ Exception Intelligence                        │
│ Category / Severity / Financial Impact        │
└──────────────────────┬────────────────────────┘
                       ↓
┌───────────────────────────────────────────────┐
│ AI Intelligence                               │
│ Explanation / Risk / Priority / Recommendation│
└──────────────────────┬────────────────────────┘
                       ↓
┌───────────────────────────────────────────────┐
│ Deterministic Controller                      │
│ Permitted action classification               │
└──────────────────────┬────────────────────────┘
                       ↓
┌───────────────────────────────────────────────┐
│ Controlled Remediation                        │
│ Validate / Request / Execute / Track          │
└──────────────────────┬────────────────────────┘
                       ↓
┌───────────────────────────────────────────────┐
│ Auditability                                  │
│ Created / Started / Completed / Rejected      │
└──────────────────────┬────────────────────────┘
                       ↓
┌───────────────────────────────────────────────┐
│ Human Resolution                              │
│ OPEN → ACKNOWLEDGED → RESOLVED                │
└───────────────────────────────────────────────┘
```

------------------------------------------------------------------------

# 20. Phase 5 File Structure

``` text
AI_Settlement_Controller/
│
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   └── api/
│   │   │       └── routes/
│   │   │           ├── controlled_actions.py
│   │   │           └── exceptions.py
│   │   │
│   │   ├── models/
│   │   │   ├── controlled_action.py
│   │   │   └── audit_log.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── controlled_action.py
│   │   │   └── exception_lifecycle.py
│   │   │
│   │   └── services/
│   │       ├── controlled_action_validation.py
│   │       ├── controlled_action_execution.py
│   │       ├── audit_log.py
│   │       └── exception_lifecycle.py
│   │
│   └── alembic/
│       └── versions/
│           ├── 9e28d8768411_add_controlled_actions.py
│           ├── bcf9531b54e8_add_controlled_action_results.py
│           └── 832533f1f844_add_audit_logs.py
│
└── docs/
    └── PHASE_5_CONTROLLED_REMEDIATION_AND_AUDITABILITY.md
```

------------------------------------------------------------------------

# 21. Phase 5 Completion Status

  Phase   Component                                       Status
  ------- ----------------------------------------------- ----------
  5.1     Controlled Action Domain Model                  COMPLETE
  5.2     Database Migration                              COMPLETE
  5.3     Action Validation / Safety Boundary             COMPLETE
  5.4     Controlled Action Creation API                  COMPLETE
  5.5     Action Execution Workflow                       COMPLETE
  5.6     Action Result / State Management                COMPLETE
  5.7     Auditability                                    COMPLETE
  5.8     Remediation ↔ Exception Lifecycle Integration   COMPLETE
  5.9     End-to-End Verification                         COMPLETE
  5.10    Documentation                                   COMPLETE

------------------------------------------------------------------------

# 22. Final Phase 5 Outcome

Phase 5 transforms the AI Settlement Controller from an
intelligence-only system into a:

> **Controlled operational decision and remediation platform**

The system can now:

-   Identify payment and settlement exceptions.
-   Quantify known financial exposure.
-   Prioritize operational risk.
-   Use Gemini for contextual explanation and recommendations.
-   Convert recommendations into deterministic controlled action
    classes.
-   Reject unauthorized action requests.
-   Execute permitted operational workflows.
-   Track action state and results.
-   Maintain an auditable remediation trail.
-   Keep exception resolution under explicit human control.
-   Preserve the underlying financial records during controlled
    remediation.

The architecture therefore follows:

``` text
Detect
   ↓
Understand
   ↓
Prioritize
   ↓
Recommend
   ↓
Control
   ↓
Audit
```

rather than:

``` text
Detect
   ↓
LLM decides
   ↓
Money moves automatically
```

The core principle of the AI Settlement Controller remains:

> **AI should improve financial operations without becoming an
> uncontrolled financial actor.**

------------------------------------------------------------------------

# 23. Phase 5 Final Status

``` text
====================================================
              AI SETTLEMENT CONTROLLER
                    PHASE 5
====================================================

Controlled Remediation       ✅ COMPLETE
Action Validation             ✅ COMPLETE
Action Execution              ✅ COMPLETE
Action State Management       ✅ COMPLETE
Auditability                  ✅ COMPLETE
Lifecycle Integration         ✅ COMPLETE
Human Review Boundary         ✅ VERIFIED
Financial Safety Boundary     ✅ VERIFIED
End-to-End Verification       ✅ COMPLETE
Documentation                 ✅ COMPLETE

```
