# Architecture — AI Settlement Controller

## 1. System Overview

The **AI Settlement Controller** is a payment-settlement control system being developed for a Razorpay-like payment environment.

Its purpose is to establish financial correctness between payment transactions and settlement outcomes, detect settlement exceptions, quantify known financial exposure, prioritize operational risk, use AI to explain and contextualize exceptions, provide controlled remediation workflows, retain human resolution authority, and expose historical and population-level settlement intelligence.

The system has been developed incrementally around a deterministic financial core.

The current end-to-end architecture follows:

```text
Transactions
     +
Settlements
     ↓
Deterministic Reconciliation
     ↓
Exception Intelligence
     ↓
Financial Impact + Priority
     ↓
Exception Lifecycle
     ↓
Controlled Remediation
     ↓
Audit Trail
     ↓
Human Review / Resolution
     ↓
Operational Control + Risk + Governance
     ↓
Historical Settlement Intelligence
     ↓
Population Pattern Intelligence
     ↓
Trusted AI Investigation
     ↓
Operator / Human
```

The fundamental architectural principle is:

> **AI should assist with understanding and recommendation, while deterministic financial logic, controlled workflows, governance, and human resolution remain responsible for correctness, authorization, and operational safety.**

The project follows:

```text
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
  ↓
Resolve
  ↓
Learn from History
```

---

## 2. Current Architecture

The current system consists of the following major layers:

```text
                         ┌─────────────────────────────┐
                         │           FastAPI           │
                         │            API Layer        │
                         └──────────────┬──────────────┘
                                        │
        ┌───────────────────────────────┼────────────────────────────────┐
        │                               │                                │
        ▼                               ▼                                ▼
┌──────────────────┐          ┌──────────────────┐          ┌────────────────────┐
│ Transaction APIs │          │ Settlement APIs  │          │ Control / Risk /   │
│                  │          │ + CSV Ingestion  │          │ Governance / Human │
└────────┬─────────┘          └────────┬─────────┘          │ Resolution / AI    │
         │                             │                    └──────────┬─────────┘
         └──────────────────┬──────────┴───────────────────────────────┘
                            ▼
                   ┌──────────────────────┐
                   │    Service Layer     │
                   │                      │
                   │ Ingestion             │
                   │ Reconciliation        │
                   │ Exception Intelligence│
                   │ Lifecycle             │
                   │ Governance            │
                   │ AI Context / Analysis │
                   │ Controller            │
                   │ Controlled Actions    │
                   │ Audit Logging         │
                   │ Historical Intelligence│
                   │ Pattern Intelligence   │
                   │ Operational Control    │
                   └──────────┬──────────────┘
                              │
              ┌───────────────┼────────────────┐
              ▼               ▼                ▼
       ┌────────────┐   ┌────────────┐   ┌────────────────┐
       │ SQLAlchemy │   │   Gemini   │   │ Deterministic  │
       │   Models   │   │  2.5 Flash │   │ Control Logic  │
       └─────┬──────┘   └────────────┘   └────────────────┘
             │
             ▼
       ┌──────────────────────────────┐
       │          PostgreSQL          │
       │                              │
       │ transactions                 │
       │ settlements                  │
       │ exception_lifecycles         │
       │ controlled_actions           │
       │ audit_logs                   │
       └──────────────────────────────┘
```

The architecture now extends beyond ingestion and persistence into reconciliation, exception intelligence, AI-assisted analysis, deterministic action control, remediation tracking, auditability, governance, human resolution, operational risk/control views, historical intelligence, timing analysis, and population pattern analysis.

---

## 3. API Layer

FastAPI exposes the application's HTTP interface.

The API layer provides endpoints for:

```text
Health
Transactions
Settlements
Settlement Ingestion
Reconciliation
Exception Intelligence
Exception Lifecycle
Human Acknowledgement / Resolution
AI Analysis
Controller Decisions
Controlled Actions
Operational Control
Operational Risk
Governance
Historical Intelligence
Pattern Intelligence
AI Investigation
```

Representative endpoint groups include:

```text
GET  /health

POST /transactions
GET  /transactions
GET  /transactions/{transaction_id}

POST /settlements
POST /ingestion/settlements

GET  /reconciliation/{payment_id}

GET  /exceptions/{payment_id}
GET  /exceptions
GET  /exceptions/{payment_id}/lifecycle
POST /exceptions/{payment_id}/acknowledge
POST /exceptions/{payment_id}/resolve

GET  /exceptions/{payment_id}/ai-analysis
GET  /exceptions/ai-analysis

GET  /exceptions/{payment_id}/decision

POST /controlled-actions
POST /controlled-actions/{action_id}/execute

GET  /control/exceptions
GET  /control/exceptions/{payment_id}
GET  /control/exceptions/{payment_id}/detail
GET  /control/summary

GET  /risk/queue
GET  /risk/summary

GET  /control/governance

GET  /intelligence/exceptions/{payment_id}
GET  /intelligence/patterns
GET  /intelligence/exceptions/{payment_id}/investigation
```

The API layer is responsible for HTTP request handling, response serialization, validation boundaries, and orchestration of application services.

Financial decision logic is intentionally kept outside API routes wherever possible.

Operational read APIs do not create side effects.

Human lifecycle endpoints explicitly perform controlled state transitions and create the corresponding audit records.

---

## 4. Schema Layer

Pydantic schemas define the structure and validation rules for incoming and outgoing API data.

The schema layer provides boundaries for:

* Transaction requests and responses
* Settlement requests and responses
* Settlement ingestion results
* Reconciliation results
* Exception intelligence
* Exception lifecycle
* Human resolution requests
* AI analysis
* Controller decisions
* Controlled actions
* Operational control views
* Operational risk views
* Governance views
* Historical intelligence
* Pattern intelligence
* AI investigation
* Operational summaries
* Operational control detail and audit representations

Important validation properties include:

* positive monetary values
* bounded identifiers
* currency validation
* timestamp validation
* structured ingestion errors
* explicit enumerated statuses and categories
* required human resolution reason and note
* bounded resolution-note length

The schema layer prevents malformed data from reaching core processing unnecessarily.

---

## 5. Transaction and Settlement Data Layer

The system intentionally represents payment transactions and settlement records as separate financial entities.

Current primary financial entities are:

```text
Transaction
Settlement
```

A transaction represents the expected payment-side financial event.

A settlement represents the downstream settlement-side financial event.

The common `payment_id` provides the initial association between these two event types.

This separation is important because reconciliation must compare independently recorded financial events rather than treating them as a single record.

The current data model also reflects an important operational distinction:

```text
Transaction / Settlement
        =
Financial source data

ExceptionRecord
        =
Operational exception lifecycle state

AuditLog
        =
Historical audit event
```

An `ExceptionRecord` is not a general historical exception-event log; it is the persisted lifecycle representation for an exception/payment.

---

## 6. Settlement Ingestion Architecture

Settlement data can enter the system through:

```text
Settlement API
      │
      ▼
Settlement Creation

Settlement CSV
      │
      ▼
CSV Parser
      │
      ▼
Row Validation
      │
      ▼
Duplicate Detection
      │
      ▼
Batch Ingestion
      │
      ▼
Settlement Store
```

The ingestion services are responsible for:

* CSV parsing
* row-level validation
* settlement creation
* duplicate detection
* batch processing
* partial-success handling
* structured ingestion errors

Ingestion is deliberately separated from reconciliation.

The ingestion layer establishes trustworthy settlement records; reconciliation subsequently determines whether those records agree with the corresponding transaction.

Advanced bulk-ingestion enhancements remain a separate possible improvement and do not replace the existing ingestion architecture.

---

## 7. Reconciliation Architecture

The reconciliation engine is the deterministic financial comparison layer.

The flow is:

```text
Transaction
     +
Settlement
     ↓
Reconciliation Service
     ↓
Financial Comparison
     ↓
Reconciliation Result
```

The reconciliation engine currently evaluates:

```text
MATCHED
AMOUNT_MISMATCH
MISSING_SETTLEMENT
CURRENCY_MISMATCH
INVALID_STATE
```

It also identifies settlement drift:

```text
NONE
UNDER_SETTLED
OVER_SETTLED
```

The reconciliation engine compares:

* expected transaction amount
* actual settled amount
* transaction currency
* settlement currency
* transaction state
* settlement state

The reconciliation engine uses deterministic business rules and `Decimal` arithmetic.

AI is not involved in establishing whether a transaction is financially reconciled.

This ensures that financial correctness remains deterministic, explainable, and independently testable.

---

## 8. Exception Intelligence Architecture

Reconciliation results are transformed into structured exception intelligence.

The system classifies exceptions into:

```text
NONE
MISSING_SETTLEMENT
UNDER_SETTLEMENT
OVER_SETTLEMENT
CURRENCY_MISMATCH
INVALID_STATE
```

Each exception receives deterministic:

```text
Category
Severity
Financial Impact
Priority Score
```

Severity levels are:

```text
NONE
LOW
MEDIUM
HIGH
```

Current severity mapping includes:

```text
MATCHED
    → NONE

MISSING_SETTLEMENT
    → HIGH

CURRENCY_MISMATCH
    → HIGH

INVALID_STATE
    → HIGH

UNDER_SETTLEMENT
    → MEDIUM

OVER_SETTLEMENT
    → HIGH
```

This layer converts raw reconciliation differences into operationally meaningful exceptions.

---

## 9. Financial Impact Architecture

Known financial exposure is calculated deterministically from reconciliation results.

The system follows:

```text
MISSING_SETTLEMENT
    → Expected transaction amount

UNDER_SETTLEMENT
    → Amount difference

OVER_SETTLEMENT
    → Amount difference

CURRENCY_MISMATCH
    → Unknown / not safely quantifiable

INVALID_STATE
    → Unknown / not safely quantifiable
```

The system never invents monetary values when financial exposure cannot be safely determined.

Financial impact is represented as a known value or explicit absence of a safely quantifiable value.

For population-level pattern reporting, known financial impact is grouped by currency rather than blindly aggregated across currencies.

---

## 10. Priority and Risk Architecture

Exceptions receive deterministic priority scores based on severity and known financial exposure.

The priority layer considers:

```text
Exception Severity
        +
Known Financial Impact
        ↓
Priority Score
```

Priority values are explainable and deterministic.

The architecture distinguishes:

```text
Exception Category
Severity
Financial Impact
Priority
Risk / Governance
```

These are related but intentionally separate concepts.

The system can therefore answer:

> Is there an exception?

> How serious is it?

> How much known money is affected?

> What operational attention does it require?

> Does it require escalation?

---

## 11. Exception Lifecycle Architecture

Exceptions have an explicit operational lifecycle:

```text
OPEN
  │
  ▼
ACKNOWLEDGED
  │
  ▼
RESOLVED
```

The lifecycle is maintained separately from reconciliation.

Reconciliation determines the financial state.

The lifecycle determines the operational handling state.

Only valid lifecycle transitions are permitted.

Invalid transitions are rejected deterministically.

Resolution requires explicit human-provided metadata:

```text
resolution_reason
resolution_note
resolved_at
```

Supported resolution reasons include:

```text
SETTLEMENT_CONFIRMED
MANUAL_RECONCILIATION
FALSE_POSITIVE
DUPLICATE_EXCEPTION
OTHER
```

A controlled action reaching `COMPLETED` does not automatically resolve the exception.

---

## 12. Controlled Remediation Architecture

Controlled actions provide the operational execution boundary.

The flow is:

```text
Controller Decision
        ↓
Action Request
        ↓
Action Validation
        ↓
REQUESTED
        ↓
IN_PROGRESS
        ↓
COMPLETED / FAILED / REJECTED
```

Supported action types are explicitly enumerated:

```text
INVESTIGATE_MISSING_SETTLEMENT
REVIEW_SETTLEMENT_AMOUNT
REVIEW_CURRENCY_MISMATCH
INVESTIGATE_INVALID_STATE
```

Only valid exception-to-action combinations can execute.

Current remediation is operational investigation/review and does not directly modify financial records.

---

## 13. Audit Architecture

The audit trail records important operational events.

Controlled-action events include:

```text
CONTROLLED_ACTION_CREATED
CONTROLLED_ACTION_STARTED
CONTROLLED_ACTION_COMPLETED
CONTROLLED_ACTION_FAILED
CONTROLLED_ACTION_REJECTED
```

Human lifecycle events include:

```text
EXCEPTION_ACKNOWLEDGED
EXCEPTION_RESOLVED
```

Transition evidence for relevant state changes includes:

```text
previous_status
new_status
```

Human resolution events do not require a controlled action and therefore may have:

```text
controlled_action_id = NULL
```

Audit history is append-oriented historical evidence.

Historical audit records are preserved rather than retroactively rewritten when the audit schema becomes stronger.

---

## 14. Governance and Operational Resilience

The governance layer derives deterministic operational escalation state from existing exception, lifecycle, remediation, priority, and aging information.

Exception aging is based on the authoritative exception creation timestamp.

Current aging bands are:

```text
0h <= age < 1h
    → FRESH

1h <= age < 4h
    → AGING

4h <= age < 24h
    → ATTENTION

age >= 24h
    → OVERDUE
```

Unknown age is preserved as unknown and is never treated as overdue.

Governance levels are:

```text
NORMAL
ELEVATED
HIGH
CRITICAL
```

Escalation is deterministic.

Examples include:

```text
RESOLVED
    → NORMAL

IN_PROGRESS
    → ELEVATED

HUMAN_RESOLUTION_REQUIRED + priority >= 75
    → HIGH + escalation

OVERDUE + unresolved + priority >= 75
    → CRITICAL + escalation

OVERDUE + unresolved
    → HIGH + escalation

ACTION_REQUIRED + priority >= 75
    → HIGH + escalation

ACTION_REQUIRED
    → ELEVATED + escalation
```

The governance API is read-only and does not mutate operational state, execute actions, invoke AI, or create audit events.

---

## 15. Operational Control and Risk Architecture

The operational control layer is a read-only projection of existing financial and operational state.

It combines:

```text
Reconciliation
+
Exception Intelligence
+
Financial Impact
+
Priority
+
Lifecycle
+
Controller Decision
+
Controlled Actions
+
Audit History
+
Governance
```

Operational attention states are:

```text
ACTION_REQUIRED
IN_PROGRESS
HUMAN_RESOLUTION_REQUIRED
MONITOR
NO_ACTION_REQUIRED
```

Precedence is deterministic:

```text
RESOLVED
    → NO_ACTION_REQUIRED

Remediation IN_PROGRESS
    → IN_PROGRESS

Remediation COMPLETED + unresolved
    → HUMAN_RESOLUTION_REQUIRED

Human Review Required
    → ACTION_REQUIRED

Otherwise
    → MONITOR
```

If an exception has no persisted lifecycle record but still requires human review, it must not be suppressed:

```text
lifecycle_status = null
+
human_review_required = true
    ↓
ACTION_REQUIRED
```

Risk queue ordering is:

```text
1. Attention rank
2. Priority score
3. Known financial impact
```

Attention rank is:

```text
ACTION_REQUIRED = 5
IN_PROGRESS = 4
HUMAN_RESOLUTION_REQUIRED = 3
MONITOR = 2
NO_ACTION_REQUIRED = 1
```

Operational control and risk APIs are strictly read-only.

They may read, reconcile, assess, aggregate, and correlate existing state, but they cannot:

```text
Execute
Resolve
Mutate
Create Audit Events
Invoke AI
```

---

## 16. Human Operations and Resolution

Human operations form the final resolution boundary for unresolved exceptions.

The lifecycle endpoints are:

```text
POST /exceptions/{payment_id}/acknowledge
POST /exceptions/{payment_id}/resolve
GET  /exceptions/{payment_id}/lifecycle
```

The lifecycle is:

```text
OPEN
  ↓
ACKNOWLEDGED
  ↓
RESOLVED
```

Resolution requires:

```text
resolution_reason
resolution_note
```

and records:

```text
resolved_at
```

The human resolution flow is intentionally separate from controlled remediation:

```text
Controlled Action
    → operational investigation/review

Human Resolution
    → explicit decision that the exception is resolved
```

This prevents operational work from being mistaken for financial resolution.

---

## 17. Historical Exception Intelligence

Phase 9 introduces historical intelligence derived from existing financial data.

Historical exception analysis does not create a new financial truth source.

Instead, it reuses:

```text
Transaction Data
+
Settlement Data
+
Deterministic Reconciliation
+
Deterministic Exception Assessment
```

A historical exception is a transaction which, through the existing deterministic reconciliation and exception assessment path, produces an exception.

Historical analysis excludes the current payment being investigated.

The historical intelligence response can expose:

```text
historical_transaction_count
historical_exception_count
same_category_exception_count
same_currency_exception_count
same_category_and_currency_exception_count
recurrence_detected
```

The recurrence signal is population-oriented and must not be interpreted as proof that the current payment itself previously had exceptions.

The historical intelligence layer does not introduce an opaque probability score or probabilistic risk model.

---

## 18. Settlement Timing Intelligence

Historical intelligence also provides settlement timing context.

Current timing evidence is derived from:

```text
settled_at - paid_at
```

when both timestamps are available.

The system exposes:

```text
timing_available
settlement_delay_hours
historical_settlement_count
historical_average_delay_hours
timing_deviation_hours
```

Historical timing comparison uses relevant historical records and excludes the current payment.

Timing deviation is contextual evidence.

The system deliberately does not introduce an arbitrary threshold such as:

```text
timing_deviation_detected = true
```

and does not convert timing deviation directly into financial priority or governance.

If required timestamps are unavailable, timing remains explicitly unavailable rather than being estimated.

---

## 19. Population Pattern Intelligence

Population-level pattern intelligence aggregates deterministic exception assessments across the available transaction population.

The pattern response provides:

```text
total_transactions
total_exceptions
categories
recurring_categories
```

For each category it provides:

```text
category
exception_count
high_severity_count
known_financial_impact_by_currency
```

Known financial impact is grouped by currency:

```text
INR
USD
...
```

rather than aggregated across currencies without a valid conversion basis.

Recurring categories are derived deterministically from population observations.

Pattern intelligence does not create an opaque risk score and does not replace the individual exception assessment.

---

## 20. AI Investigation Architecture

The Phase 9 AI investigation layer extends the existing AI architecture without changing its safety boundary.

The flow is:

```text
Financial Source Data
        +
Deterministic Exception Assessment
        +
Historical Intelligence
        +
Timing Intelligence
        +
Population Pattern Intelligence
        ↓
Trusted Investigation Context
        ↓
Gemini
        ↓
Investigation Explanation / Guidance
        ↓
Human Operator
```

The AI investigation context contains deterministic application-generated information such as:

```text
payment_id
exception category
severity
financial impact
priority score
historical counts
recurrence signals
timing fields
population recurring categories
```

The AI output provides:

```text
investigation_summary
historical_context_explanation
timing_context_explanation
evidence_gaps
investigation_guidance
```

The AI investigation layer does not:

```text
Recalculate authoritative financial truth
Invent financial impact
Change category
Change severity
Change priority
Change governance
Create controlled actions
Execute controlled actions
Acknowledge exceptions
Resolve exceptions
Make unsupported fraud claims
```

When timing evidence is unavailable, the AI must explicitly preserve that limitation.

When historical counts describe the broader population excluding the current payment, the AI must preserve that semantic distinction.

Human review remains mandatory.

---

## 21. AI Safety Boundary

The AI layer operates behind a strict financial-control boundary.

Gemini is not responsible for:

```text
Determining reconciliation correctness
Calculating authoritative financial impact
Changing transaction records
Changing settlement records
Changing exception lifecycle state
Authorizing arbitrary operational actions
Moving money
Resolving exceptions automatically
```

Instead:

```text
Deterministic Application Logic
        ↓
Trusted Financial / Operational Context
        ↓
AI Explanation / Recommendation
        ↓
Human / Deterministic Control Boundary
```

AI is an intelligence layer, not the financial authority.

---

## 22. Data Persistence Architecture

The PostgreSQL database persists the major financial and operational entities:

```text
transactions
settlements
exception_lifecycles
controlled_actions
audit_logs
```

The operational, governance, historical, pattern, and AI-context layers primarily derive information from existing financial and operational state.

The architecture intentionally separates:

```text
Financial Data
    ├── transactions
    └── settlements

Operational State
    ├── exception_lifecycles
    └── controlled_actions

Audit History
    └── audit_logs

Derived Intelligence / Views
    ├── reconciliation
    ├── exception intelligence
    ├── governance
    ├── operational control
    ├── operational risk
    ├── historical intelligence
    ├── pattern intelligence
    └── AI investigation context
```

No separate operational database is required for these derived views.

---

## 23. Migration Layer

Alembic manages database schema evolution.

Schema changes are introduced through migration files and applied to PostgreSQL.

The migration history has evolved to support:

```text
Transaction schema
Settlement schema
Exception lifecycle schema
Controlled action schema
Controlled action result fields
Audit log schema
Exception resolution metadata
Human exception audit events
```

The current Phase 8 migration sequence is followed by the Phase 9 application-level intelligence additions, which do not require a separate persisted intelligence table.

The latest verified migration head at the end of Phase 8 was:

```text
13f3527ae092
```

Phase 9 intelligence is derived through services and schemas rather than persisted as a new intelligence store.

---

## 24. Separation of Concerns

The architecture separates:

```text
API Layer
Schema / Validation
Business Services
Financial Models
Operational State
Governance
AI Integration
Control Logic
Audit Logging
Database
Derived Intelligence
```

Key boundaries are:

```text
Financial Truth
    ≠
Operational State
    ≠
Audit History
    ≠
AI Interpretation
```

More specifically:

```text
Reconciliation
    → establishes financial comparison

Exception Intelligence
    → classifies the exception

Priority / Financial Impact
    → quantifies deterministic operational exposure

Lifecycle
    → tracks human operational handling

Controlled Actions
    → tracks permitted operational execution

Governance
    → determines escalation state

Audit
    → preserves historical evidence

Historical / Pattern Intelligence
    → provides contextual evidence from existing data

AI Investigation
    → explains evidence and guides human investigation
```

---

## 25. End-to-End Financial Control Flow

The complete architecture now follows:

```text
                 ┌──────────────────────┐
                 │   Payment Transaction│
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │  Transaction Store   │
                 └──────────┬───────────┘
                            │
                            │
Settlement Files ───────────┤
                            │
                            ▼
                 ┌──────────────────────┐
                 │ Settlement Ingestion │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ Reconciliation Engine│
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ Exception Intelligence│
                 └──────────┬───────────┘
                            │
                 ┌──────────┴───────────┐
                 ▼                      ▼
        Financial Impact          Priority / Risk
                 │                      │
                 └──────────┬───────────┘
                            ▼
                 ┌──────────────────────┐
                 │ Exception Lifecycle │
                 └──────────┬───────────┘
                            │
              ┌─────────────┼───────────────┐
              ▼             ▼               ▼
        Governance     Historical       Operational
        / Escalation   Intelligence      Control / Risk
                            │
                            ▼
                 ┌──────────────────────┐
                 │ Pattern Intelligence │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ Trusted AI Context   │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │    Gemini Analysis   │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ Deterministic        │
                 │ Controller Decision  │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ Controlled Action    │
                 │ Validation           │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ Controlled Action    │
                 │ Execution            │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │      Audit Log       │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ Human Review /       │
                 │ Explicit Resolution  │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ Operator / Control   │
                 │ Center / Dashboard   │
                 └──────────────────────┘
```

---

## 26. Architectural Principles

### Deterministic Financial Core

Financial correctness must not depend on probabilistic AI output.

### AI as an Intelligence Layer, Not a Financial Authority

AI explains, contextualizes, and guides investigation. It does not establish financial truth or authorize execution.

### Deterministic Control Boundary

Operational actions are authorized through deterministic controller and validation logic.

### Human Resolution Boundary

The system may detect, analyze, prioritize, recommend, and execute controlled operational work, but explicit exception resolution remains human-owned.

### Read-Only Operational Visibility

Control, risk, governance, historical intelligence, pattern intelligence, and detail APIs are derived views unless an endpoint explicitly represents a controlled lifecycle operation.

### Separation of Concerns

Financial source data, operational state, audit history, intelligence, and AI interpretation remain distinct.

### Financial Precision

Monetary calculations use `Decimal` and fixed-precision database fields.

### Explicit Uncertainty

Unknown financial exposure and unavailable timing evidence remain explicitly unknown.

### Lifecycle Separation

```text
Reconciliation State
        ≠
Exception Lifecycle
        ≠
Controlled Action Status
        ≠
Governance State
```

### Population vs Individual Semantics

Historical population signals must not be described as proof of prior behavior by the current payment.

### Deterministic Population Intelligence

Population patterns and financial exposure summaries are derived from deterministic assessments.

### Auditability

Important operational actions, rejected actions, and human lifecycle transitions are represented in the audit history.

### Incremental Evolution

The architecture evolves in phases without bypassing earlier safety boundaries.

---

## 27. Current Architectural State — End of Phase 9

The system has progressed from a transaction/settlement data layer into a controlled, auditable settlement intelligence platform:

```text
Phase 1
Transaction Foundation
        ↓
Phase 2
Settlement Ingestion
        ↓
Phase 3
Deterministic Reconciliation
        ↓
Phase 4
Exception Intelligence + AI + Controller
        ↓
Phase 5
Controlled Remediation + Auditability
        ↓
Phase 6
Operational Control + Risk
        ↓
Phase 7
Governance + Operational Resilience
        ↓
Phase 8
Human Operations + Explicit Resolution
        ↓
Phase 9
Advanced Settlement Intelligence
        ├── Historical Exception Intelligence
        ├── Recurrence Signals
        ├── Settlement Timing Intelligence
        ├── Population Pattern Intelligence
        └── AI Investigation
        ↓
Phase 10
Production Readiness + Operator Experience
```

The central design philosophy remains:

> **AI should help the settlement operations system understand and prioritize problems, but deterministic financial logic and controlled workflows must remain responsible for what the system is allowed to do. Humans retain the authority to resolve exceptions, while audit history preserves what happened.**
