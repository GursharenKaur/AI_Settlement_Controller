# Phase 6 — Operational Control & Risk

## 1. Overview

Phase 6 extends the AI Settlement Controller from an exception remediation system into an operational control system.

The objective of this phase is to provide a deterministic operational view of settlement exceptions, prioritize cases requiring attention, correlate exceptions with remediation and audit activity, and expose consolidated control information for an operational dashboard.

Phase 6 does not introduce a new financial processing layer.

Instead, it builds an operational control layer on top of the capabilities established in Phases 1–5.

The resulting control flow is:

```text
Transactions
      +
Settlements
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
Deterministic Controller Decision
      ↓
Controlled Action Validation
      ↓
Controlled Action Execution
      ↓
Audit Log
      ↓
Human Review / Explicit Resolution
      ↓
Operational Control
      ↓
Operational Risk
      ↓
Control Summary
```

The core principle remains:

> AI recommends; deterministic business logic authorizes; controlled workflows execute; humans retain resolution authority; important actions are audited.

---

## 2. Phase 6 Objectives

Phase 6 was divided into five major objectives:

1. Operational Exception Control View
2. Action / Exception Correlation API
3. Operational Risk Prioritization
4. Control Dashboard / Operational APIs
5. End-to-End Control Verification

The implementation focused on extending the existing architecture rather than introducing a separate parallel exception-management system.

---

## 3. Architectural Role of Phase 6

Before Phase 6, the system could:

- ingest transactions and settlements
- reconcile transactions against settlements
- classify exceptions
- calculate financial impact
- calculate deterministic priority
- generate AI analysis
- generate deterministic controller decisions
- create controlled remediation actions
- execute controlled actions
- record audit events
- maintain explicit exception lifecycle states

Phase 6 adds the operational layer required to answer:

- Which exceptions require attention?
- Which cases are currently being remediated?
- Which cases require human resolution?
- Which cases require no further action?
- What is the current operational risk queue?
- What is the highest-priority case?
- How much known financial exposure remains?
- What remediation and audit activity has occurred for a specific exception?
- How many outstanding controls exist?

This creates the transition:

```text
Exception Management
        ↓
Operational Control
```

---

# 4. Phase 6.1 — Operational Exception Control View

## 4.1 Purpose

The first objective was to create a deterministic operational representation of an exception.

The operational control view combines:

- exception category
- severity
- financial impact
- priority score
- lifecycle status
- controller recommendation
- human-review requirement
- controlled actions
- remediation status

The view is intentionally read-only.

It does not:

- execute actions
- modify financial records
- resolve exceptions
- create audit events
- invoke AI

---

## 4.2 Schema

Implemented in:

```text
backend/app/schemas/operational_control.py
```

The primary operational exception representation is:

```python
class OperationalExceptionControl(BaseModel):
    payment_id: str
    category: ExceptionCategory
    severity: ExceptionSeverity
    financial_impact: Decimal | None
    priority_score: int
    lifecycle_status: ExceptionLifecycleStatus | None
    recommended_action: ControllerAction
    human_review_required: bool
    controlled_actions: list[OperationalControlledAction]
    remediation_status: str
```

Controlled actions exposed through the operational view include:

```text
id
action_type
status
result
executed_at
```

ORM compatibility is provided through:

```python
model_config = {
    "from_attributes": True,
}
```

---

# 5. Phase 6.2 — Operational Control API

## 5.1 Routes

Implemented in:

```text
backend/app/core/api/routes/operational_control.py
```

The following endpoints were added:

```text
GET /control/exceptions
GET /control/exceptions/{payment_id}
```

These endpoints expose the operational control view without modifying the underlying control state.

---

## 5.2 Collection View

```text
GET /control/exceptions
```

Provides the operational control representation of all known exceptions.

The endpoint combines the existing deterministic components:

```text
Reconciliation
      ↓
Exception Intelligence
      ↓
Lifecycle
      ↓
Controller Decision
      ↓
Controlled Actions
      ↓
Operational Control View
```

---

## 5.3 Individual Control View

```text
GET /control/exceptions/{payment_id}
```

Provides the operational state of one exception.

An unknown payment is rejected rather than silently producing an empty control object.

---

# 6. Phase 6.3 — Operational Risk Prioritization

Phase 6.3 introduces the operational risk queue.

The purpose is not to create a second priority calculation.

Instead, the operational risk layer consumes the already-established deterministic control state.

---

## 6.1 Risk Item Schema

Implemented in:

```text
backend/app/schemas/operational_risk.py
```

The risk item contains:

```python
class OperationalRiskItem(BaseModel):
    payment_id: str
    category: ExceptionCategory
    severity: ExceptionSeverity
    financial_impact: Decimal | None
    priority_score: int
    lifecycle_status: ExceptionLifecycleStatus | None
    recommended_action: ControllerAction
    human_review_required: bool
    remediation_status: str
    attention_status: AttentionStatus
```

---

# 7. Attention Classification

A major Phase 6 capability is deterministic attention classification.

The system converts the current operational state into one of five attention states:

```text
ACTION_REQUIRED
IN_PROGRESS
HUMAN_RESOLUTION_REQUIRED
MONITOR
NO_ACTION_REQUIRED
```

The classification follows this deterministic state machine:

```text
Lifecycle = RESOLVED
        ↓
NO_ACTION_REQUIRED
```

```text
Remediation = IN_PROGRESS
        ↓
IN_PROGRESS
```

```text
Remediation = COMPLETED
AND Lifecycle != RESOLVED
        ↓
HUMAN_RESOLUTION_REQUIRED
```

```text
Human Review Required = true
        ↓
ACTION_REQUIRED
```

```text
Otherwise
        ↓
MONITOR
```

The ordering is intentional because lifecycle and remediation state represent stronger operational signals than a generic review requirement.

---

# 8. Deterministic Risk Queue Ordering

The operational risk queue is ordered using:

1. Attention rank
2. Priority score
3. Known financial impact

Attention ranks are:

```python
ATTENTION_RANK = {
    "ACTION_REQUIRED": 5,
    "IN_PROGRESS": 4,
    "HUMAN_RESOLUTION_REQUIRED": 3,
    "MONITOR": 2,
    "NO_ACTION_REQUIRED": 1,
}
```

Therefore:

```text
ACTION_REQUIRED
        ↓
IN_PROGRESS
        ↓
HUMAN_RESOLUTION_REQUIRED
        ↓
MONITOR
        ↓
NO_ACTION_REQUIRED
```

Within the same attention state:

```text
Higher priority score
        ↓
Higher known financial impact
```

This ensures the queue remains deterministic and explainable.

---

# 9. Important Null Lifecycle Case

An exception does not necessarily have a persisted lifecycle record.

For example, newly identified exceptions may have:

```text
lifecycle_status = null
```

This does not mean the exception is safe to ignore.

If:

```text
human_review_required = true
```

the exception can still become:

```text
ACTION_REQUIRED
```

This prevents missing lifecycle persistence from incorrectly suppressing operational attention.

---

# 10. Phase 6.3.2 — Operational Risk Queue API

Implemented in:

```text
backend/app/core/api/routes/operational_risk.py
```

Endpoint:

```text
GET /risk/queue
```

The queue is read-only.

It does not:

- modify financial records
- execute controlled actions
- modify lifecycle state
- create audit events
- invoke AI
- recalculate the underlying financial source of truth

---

# 11. Verified Risk Queue

The verified queue ordering was:

```text
1. payment 2
   MISSING_SETTLEMENT
   ACTION_REQUIRED
   priority = 100
   financial impact = 15000.00

2. pay_test_001
   INVALID_STATE
   ACTION_REQUIRED
   priority = 75
   financial impact = unknown

3. pay_recon_over_001
   OVER_SETTLEMENT
   NO_ACTION_REQUIRED
   priority = 75
   financial impact = 300.00

4. pay_recon_currency_001
   CURRENCY_MISMATCH
   NO_ACTION_REQUIRED
   priority = 75
   financial impact = unknown

5. pay_recon_invalid_001
   INVALID_STATE
   NO_ACTION_REQUIRED
   priority = 75
   financial impact = unknown

6. pay_recon_mismatch_001
   UNDER_SETTLEMENT
   NO_ACTION_REQUIRED
   priority = 50
   financial impact = 200.00
```

The queue therefore surfaces actionable operational risk before resolved cases.

---

# 12. Phase 6.4.1 — Operational Risk Summary

The operational risk layer was extended with:

```text
GET /risk/summary
```

Schema:

```python
class OperationalRiskSummary(BaseModel):
    total_exceptions: int
    action_required_count: int
    in_progress_count: int
    human_resolution_required_count: int
    monitor_count: int
    no_action_required_count: int
    total_known_financial_impact: Decimal
    highest_priority_payment_id: str | None
    highest_priority_score: int | None
    highest_priority_financial_impact: Decimal | None
```

The summary is derived from the existing operational risk queue.

It does not independently recreate risk calculations.

---

# 13. Verified Risk Summary

The verified result was:

```json
{
    "total_exceptions": 6,
    "action_required_count": 2,
    "in_progress_count": 0,
    "human_resolution_required_count": 0,
    "monitor_count": 0,
    "no_action_required_count": 4,
    "total_known_financial_impact": "15500.00",
    "highest_priority_payment_id": "2",
    "highest_priority_score": 100,
    "highest_priority_financial_impact": "15000.00"
}
```

This confirms that the operational summary agrees with the risk queue.

---

# 14. Phase 6.4.2 — Operational Control Detail

Phase 6 adds a consolidated detail view for a single exception.

Endpoint:

```text
GET /control/exceptions/{payment_id}/detail
```

The detail API combines:

```text
Exception
+
Controller Decision
+
Lifecycle
+
Controlled Actions
+
Audit Events
```

This provides a single operational view of the complete control history.

---

# 15. Operational Control Detail Schema

Implemented in:

```text
backend/app/schemas/operational_control_detail.py
```

The detail response contains:

```text
payment_id
category
severity
financial_impact
priority_score
lifecycle_status
recommended_action
human_review_required
remediation_status
controlled_actions
audit_events
```

Each controlled action includes:

```text
id
action_type
status
reason
result
created_at
updated_at
executed_at
```

Each audit event includes:

```text
id
payment_id
controlled_action_id
event_type
message
created_at
```

Both ORM-backed representations support:

```python
model_config = {
    "from_attributes": True,
}
```

---

# 16. Operational Control Detail Safety Model

The detail service is explicitly read-only.

It performs:

```text
Reconciliation
      ↓
Exception Assessment
      ↓
Lifecycle Lookup
      ↓
Controller Decision
      ↓
Controlled Action Lookup
      ↓
Audit Lookup
      ↓
Operational Detail
```

It does not perform:

```text
Action Execution
Financial Mutation
Lifecycle Mutation
Audit Creation
AI Analysis
```

This separation prevents a dashboard/read operation from accidentally becoming an operational command.

---

# 17. Verified Completed Case

The following completed case was verified:

```text
payment_id:
pay_recon_invalid_001
```

Result:

```text
category:
INVALID_STATE

severity:
HIGH

financial_impact:
null

priority_score:
75

lifecycle_status:
RESOLVED

recommended_action:
NO_FURTHER_ACTION

human_review_required:
false

remediation_status:
COMPLETED
```

Controlled action:

```text
id = 5
action_type = INVESTIGATE_INVALID_STATE
status = COMPLETED
```

Audit events:

```text
CONTROLLED_ACTION_CREATED
CONTROLLED_ACTION_STARTED
CONTROLLED_ACTION_COMPLETED
```

This proves that the operational detail endpoint can reconstruct the complete control history.

---

# 18. Verified Untouched Case

The untouched high-risk exception was:

```text
payment_id = 2
```

Its operational detail was:

```text
category:
MISSING_SETTLEMENT

severity:
HIGH

financial_impact:
15000.00

priority_score:
100

recommended_action:
INVESTIGATE_MISSING_SETTLEMENT

human_review_required:
true

remediation_status:
NOT_STARTED
```

It contained:

```text
controlled_actions = []
audit_events = []
```

This is important because the system does not fabricate remediation or audit history merely because an action has been recommended.

---

# 19. Phase 6.4.3 — Control Dashboard Summary

A consolidated control summary was added through:

```text
GET /control/summary
```

Schema:

```python
class OperationalControlSummary(BaseModel):
    total_exceptions: int

    action_required_count: int
    in_progress_count: int
    human_resolution_required_count: int
    monitor_count: int
    no_action_required_count: int

    total_known_financial_impact: Decimal

    highest_priority_payment_id: str | None
    highest_priority_score: int | None
    highest_priority_financial_impact: Decimal | None

    outstanding_control_count: int
```

The dashboard summary derives its values from the operational risk queue.

Outstanding controls are:

```text
ACTION_REQUIRED
+
IN_PROGRESS
+
HUMAN_RESOLUTION_REQUIRED
```

---

# 20. Verified Control Summary

The verified response was:

```json
{
    "total_exceptions": 6,
    "action_required_count": 2,
    "in_progress_count": 0,
    "human_resolution_required_count": 0,
    "monitor_count": 0,
    "no_action_required_count": 4,
    "total_known_financial_impact": "15500.00",
    "highest_priority_payment_id": "2",
    "highest_priority_score": 100,
    "highest_priority_financial_impact": "15000.00",
    "outstanding_control_count": 2
}
```

This provides a compact operational dashboard representation of the current control state.

---

# 21. Phase 6 API Surface

Phase 6 exposes the following operational endpoints:

```text
GET /control/exceptions
GET /control/exceptions/{payment_id}
GET /control/exceptions/{payment_id}/detail
GET /control/summary

GET /risk/queue
GET /risk/summary
```

All six endpoints were verified in OpenAPI.

---

# 22. Phase 6.5 — End-to-End Control Verification

The final objective was to verify the complete control loop without introducing new test data or resetting the database.

The verified flow was:

```text
Reconciliation
      ↓
Exception
      ↓
Priority
      ↓
Controller Decision
      ↓
Risk Queue
      ↓
Controlled Action
      ↓
Execution
      ↓
Audit
      ↓
Human Resolution
      ↓
Control Summary / Detail
```

---

# 23. End-to-End Verification Results

## 23.1 Reconciliation

`pay_recon_invalid_001` remained:

```text
INVALID_STATE
expected_amount = 5000.00
actual_settled_amount = 5000.00
drift_direction = NONE
INR → INR
```

Payment `2` remained:

```text
MISSING_SETTLEMENT
expected_amount = 15000.00
actual_settled_amount = null
drift_direction = UNDER_SETTLED
```

---

## 23.2 Operational Risk

The queue continued to place payment `2` first:

```text
ACTION_REQUIRED
priority = 100
financial impact = 15000.00
```

This remained the highest-priority operational case.

---

## 23.3 Completed Remediation

`pay_recon_invalid_001` remained:

```text
remediation_status = COMPLETED
lifecycle_status = RESOLVED
attention_status = NO_ACTION_REQUIRED
```

---

## 23.4 Auditability

The completed controlled action retained:

```text
CONTROLLED_ACTION_CREATED
CONTROLLED_ACTION_STARTED
CONTROLLED_ACTION_COMPLETED
```

in chronological order.

---

## 23.5 Human Resolution

The controlled action did not automatically resolve the exception.

The exception was explicitly transitioned through:

```text
OPEN
  ↓
ACKNOWLEDGED
  ↓
RESOLVED
```

This preserves the distinction between:

```text
Remediation completed
```

and:

```text
Business exception resolved
```

---

# 24. Financial Integrity Verification

Phase 6 verification confirmed that the operational control layer did not modify financial records.

The system continues to maintain the invariant:

```text
Controlled Action
       ≠
Financial Mutation
```

Operational APIs only consume the existing financial and control state.

No transaction or settlement amount was changed during Phase 6.

Known financial impact remains distinct from unknown exposure.

For example:

```text
MISSING_SETTLEMENT
→ known impact = expected transaction amount
```

while:

```text
CURRENCY_MISMATCH
→ financial impact = unknown
```

The system does not invent a monetary estimate when the available data does not support one.

---

# 25. Migration Verification

The final Alembic migration state was verified as:

```text
832533f1f844 (head)
```

No additional migration was required for the Phase 6 operational views.

This is consistent with the Phase 6 design: the operational layer primarily derives information from the existing transaction, settlement, exception, lifecycle, controlled-action, and audit data.

---

# 26. OpenAPI Verification

The following Phase 6 endpoints were confirmed in the generated OpenAPI specification:

```text
/control/exceptions
/control/exceptions/{payment_id}
/control/exceptions/{payment_id}/detail
/control/summary
/risk/queue
/risk/summary
```

The corresponding operational schemas were also exposed.

---

# 27. Unknown Exception Handling

The following request was tested:

```text
GET /control/exceptions/nonexistent_payment_999/detail
```

The API correctly returned an error indicating that no operational exception exists for the supplied payment.

This prevents the detail API from silently presenting an empty or fabricated operational state.

---

# 28. Transaction API Compatibility Fix

During Phase 6.5 verification, an existing API response validation issue was discovered.

The database contains transactions where:

```text
paid_at = NULL
```

The original response schema required:

```python
paid_at: datetime
```

This caused FastAPI response validation failures.

The response schema was corrected to:

```python
paid_at: datetime | None
```

The creation schema remains:

```python
paid_at: datetime
```

This preserves the distinction:

```text
New transaction creation
→ paid_at required

Existing transaction representation
→ paid_at may be null
```

No database record was modified to resolve this issue.

---

# 29. Files Added / Updated

## Added

```text
backend/app/schemas/operational_control.py
backend/app/services/operational_control.py

backend/app/core/api/routes/operational_control.py

backend/app/schemas/operational_risk.py
backend/app/services/operational_risk.py

backend/app/core/api/routes/operational_risk.py

backend/app/schemas/operational_control_detail.py
backend/app/services/operational_control_detail.py
```

## Updated

```text
backend/app/main.py
backend/app/schemas/transaction.py
```

The operational routes were registered through `main.py`.

---

# 30. Phase 6 Design Principles

Phase 6 follows these principles.

### 30.1 Read-only operational views

Operational control and risk APIs do not mutate system state.

### 30.2 Single source of truth

Operational APIs consume existing reconciliation, exception, lifecycle, controller, remediation, and audit state.

### 30.3 No duplicated financial calculations

The operational layer does not independently redefine financial impact.

### 30.4 Deterministic prioritization

Risk ordering is deterministic and explainable.

### 30.5 Explicit attention states

Operational attention is represented explicitly rather than inferred by a dashboard client.

### 30.6 Remediation does not equal resolution

Completing a controlled action does not automatically resolve an exception.

### 30.7 Unknown remains unknown

The system does not fabricate financial impact when the source data cannot support it.

### 30.8 AI remains advisory

Phase 6 does not allow AI to control operational execution.

### 30.9 Human authority remains explicit

Human resolution remains a separate lifecycle transition.

### 30.10 Audit remains authoritative

Important remediation activity continues to produce an auditable history.

---

# 31. Final Phase 6 Architecture

The resulting architecture is:

```text
                 TRANSACTIONS
                      +
                  SETTLEMENTS
                      │
                      ↓
               RECONCILIATION
                      │
                      ↓
             EXCEPTION INTELLIGENCE
                      │
                      ↓
          FINANCIAL IMPACT + PRIORITY
                      │
                      ↓
             EXCEPTION LIFECYCLE
                      │
                      ↓
               TRUSTED AI CONTEXT
                      │
                      ↓
                GEMINI ANALYSIS
                      │
                      ↓
          DETERMINISTIC CONTROLLER
                      │
                      ↓
              OPERATIONAL RISK
                      │
              ┌───────┴────────┐
              ↓                ↓
       RISK QUEUE        RISK SUMMARY
              │
              ↓
       CONTROLLED ACTION
              │
              ↓
          EXECUTION
              │
              ↓
             AUDIT
              │
              ↓
       HUMAN RESOLUTION
              │
              ↓
       CONTROL DASHBOARD
              │
       ┌──────┴──────┐
       ↓             ↓
 CONTROL SUMMARY   CONTROL DETAIL
```

---

# 32. Phase 6 Completion Status

```text
6.1    Operational Exception Control View       COMPLETE
6.2    Action / Exception Correlation API       COMPLETE
6.3.1  Operational Risk Schema                  COMPLETE
6.3.2  Operational Risk Queue                  COMPLETE
6.3.3  Attention Classification                COMPLETE
6.3.4  Deterministic Queue Ordering            COMPLETE
6.4.1  Operational Risk Summary API             COMPLETE
6.4.2  Operational Control Detail API           COMPLETE
6.4.3  Control Dashboard Summary API            COMPLETE
6.5    End-to-End Control Verification          COMPLETE
```

# 33. Phase 6 Outcome

Phase 6 transforms the AI Settlement Controller from a system that can identify and remediate settlement exceptions into a system that can also provide an operational control view over those exceptions.

The system can now answer:

```text
What is wrong?
      ↓
How financially important is it?
      ↓
How urgent is it?
      ↓
What does the controller recommend?
      ↓
Does it require human attention?
      ↓
Has remediation started?
      ↓
Has remediation completed?
      ↓
Has the exception actually been resolved?
      ↓
What audit history exists?
      ↓
What should operations focus on next?
```

The final control philosophy remains:

```text
DETECT
   ↓
UNDERSTAND
   ↓
PRIORITIZE
   ↓
RECOMMEND
   ↓
CONTROL
   ↓
EXECUTE SAFELY
   ↓
AUDIT
   ↓
RESOLVE EXPLICITLY
```

This completes Phase 6 of the AI Settlement Controller.
