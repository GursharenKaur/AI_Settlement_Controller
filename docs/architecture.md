# Architecture — AI Settlement Controller

## 1. System Overview

The **AI Settlement Controller** is a payment-settlement control system being developed for a Razorpay-like payment environment.

Its purpose is to establish financial correctness between payment transactions and settlement outcomes, detect settlement exceptions, quantify known financial exposure, prioritize operational risk, use AI to explain and contextualize exceptions, and provide controlled remediation workflows with human review and auditability.

The system has been developed incrementally around a deterministic financial core.

The current end-to-end architecture follows:

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
AI Analysis
     ↓
Deterministic Controller Decision
     ↓
Controlled Action Validation
     ↓
Controlled Action Execution
     ↓
Audit Trail
     ↓
Human Review / Resolution
```

The fundamental architectural principle is:

> **Detect → Understand → Prioritize → Recommend → Control → Audit**

AI assists with understanding and recommendation, while deterministic application logic remains responsible for financial correctness, action authorization, and control boundaries.

---

## 2. Current Architecture

The current system consists of the following major layers:

```text
                         ┌─────────────────────────┐
                         │        FastAPI          │
                         │         API Layer       │
                         └────────────┬────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          │                           │                           │
          ▼                           ▼                           ▼
 ┌─────────────────┐       ┌─────────────────┐       ┌──────────────────┐
 │ Transaction APIs│       │ Settlement APIs │       │ Exception /      │
 │                 │       │ + CSV Ingestion │       │ Control APIs     │
 └────────┬────────┘       └────────┬────────┘       └────────┬─────────┘
          │                         │                         │
          └──────────────┬──────────┴─────────────────────────┘
                         ▼
                ┌─────────────────────┐
                │    Service Layer    │
                │                     │
                │ Ingestion            │
                │ Reconciliation       │
                │ Exception Intelligence│
                │ Lifecycle            │
                │ AI Analysis          │
                │ Controller           │
                │ Controlled Actions   │
                │ Audit Logging        │
                └──────────┬──────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
       ┌────────────┐ ┌───────────┐ ┌──────────────┐
       │ SQLAlchemy │ │  Gemini   │ │ Deterministic│
       │   Models   │ │    AI     │ │ Control Logic│
       └─────┬──────┘ └───────────┘ └──────────────┘
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

The architecture now extends beyond ingestion and persistence into reconciliation, exception intelligence, AI-assisted analysis, deterministic action control, remediation tracking, and auditability.

---

## 3. Major Components

### API Layer

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
AI Analysis
Controller Decisions
Controlled Actions
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
```

The API layer is responsible for HTTP request handling, response serialization, validation boundaries, and orchestration of the appropriate application services.

Financial decision logic is intentionally kept outside the API routes wherever possible.

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
* AI analysis
* Controller decisions
* Controlled actions

Important financial validation properties include:

* positive monetary values
* bounded identifiers
* currency validation
* timestamp validation
* structured ingestion errors
* explicit enumerated statuses and categories

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

Each exception receives a deterministic severity classification.

Current severity levels are:

```text
NONE
LOW
MEDIUM
HIGH
```

The current mapping is:

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

The system follows these rules:

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

This distinction is important because an operational exception does not necessarily imply that its monetary impact can be quantified from the available data.

Financial impact therefore remains an application-level financial control rather than an AI-generated estimate.

---

## 10. Priority and Risk Architecture

Exceptions are assigned deterministic priority scores based on severity and known financial exposure.

The priority layer considers:

```text
Exception Severity
        +
Known Financial Impact
        ↓
Priority Score
```

The system uses higher priority for severe exceptions and provides additional weighting for significant known monetary exposure.

The resulting priority is used to help determine which exceptions require greater operational attention.

The architecture distinguishes:

```text
Exception Category
Severity
Financial Impact
Priority
Risk
```

These are related but intentionally separate concepts.

This allows the system to answer not only:

> "Is there an exception?"

but also:

> "How serious is it, and how much known money is affected?"

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

This distinction is important because a financial exception can remain unresolved even after an investigation or controlled operational action has completed.

The lifecycle therefore prevents remediation execution from being incorrectly interpreted as financial resolution.

---

## 12. Portfolio Intelligence Architecture

The system can aggregate exception information across the transaction portfolio.

Portfolio-level intelligence includes:

```text
Total Transactions
Total Exceptions
Exception Rate
Open Exceptions
Acknowledged Exceptions
Resolved Exceptions
Financial Impact
Financial Impact Rate
Impact by Category
Exception Counts by Category
Severity Distribution
High-Priority Count
Highest Priority
Risk Band
Financial Risk Level
```

The portfolio layer allows the system to move beyond individual payment investigation and identify broader operational risk.

For example, the system can distinguish between:

```text
Most common exception category
        versus
Largest financial exposure category
```

These are not necessarily the same.

---

## 13. AI Analysis Architecture

The AI layer is implemented using Google's Gemini model through the official Google GenAI SDK.

The AI layer operates on trusted application-generated context.

The flow is:

```text
Deterministic Financial Data
            +
Exception Intelligence
            +
Financial Impact
            +
Priority
            +
Lifecycle State
            ↓
       Trusted AI Context
            ↓
        Gemini Analysis
            ↓
 ┌──────────┼───────────┐
 ▼          ▼           ▼
Explanation Risk      Recommended
            Analysis   Action
```

The AI layer provides:

* exception explanation
* financial impact explanation
* risk explanation
* recommended action
* portfolio-level executive summary
* key risk drivers
* priority assessment
* recommended operational focus

AI is used for interpretation and recommendation.

It does not replace deterministic financial processing.

---

## 14. AI Safety Boundary

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
```

Instead:

```text
Deterministic Application Logic
        ↓
Trusted Financial Context
        ↓
AI Explanation / Recommendation
```

The AI must not invent monetary values.

Where financial impact cannot safely be quantified, the AI must preserve that uncertainty rather than fabricate an amount.

This prevents probabilistic model output from becoming an authoritative financial record.

---

## 15. Controller Architecture

The controller translates exception intelligence into a deterministic operational decision.

The flow is:

```text
Exception Intelligence
        +
Lifecycle State
        +
Financial Impact
        +
Priority
        ↓
Controller Decision
        ↓
Recommended / Permitted Action
```

The controller currently maps exceptions to controlled action types:

```text
MISSING_SETTLEMENT
    → INVESTIGATE_MISSING_SETTLEMENT

UNDER_SETTLEMENT
    → REVIEW_SETTLEMENT_AMOUNT

OVER_SETTLEMENT
    → REVIEW_SETTLEMENT_AMOUNT

CURRENCY_MISMATCH
    → REVIEW_CURRENCY_MISMATCH

INVALID_STATE
    → INVESTIGATE_INVALID_STATE
```

Resolved exceptions produce:

```text
NO_FURTHER_ACTION
```

The controller is deterministic.

The LLM does not directly determine which operational action the system is allowed to execute.

---

## 16. Controlled Remediation Architecture

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

Supported controlled action types are explicitly enumerated:

```text
INVESTIGATE_MISSING_SETTLEMENT
REVIEW_SETTLEMENT_AMOUNT
REVIEW_CURRENCY_MISMATCH
INVESTIGATE_INVALID_STATE
```

The validation layer ensures that only permitted action/category combinations can execute.

For example:

```text
UNDER_SETTLEMENT
        ↓
REVIEW_SETTLEMENT_AMOUNT
```

is permitted.

An unrelated action for the same exception is rejected.

This establishes a deterministic safety boundary between AI recommendations and operational execution.

---

## 17. Controlled Action State Architecture

Controlled actions have their own execution state:

```text
REQUESTED
    ↓
IN_PROGRESS
    ↓
COMPLETED
```

Failure and rejection are also represented:

```text
FAILED
REJECTED
```

A controlled action stores:

```text
payment_id
action_type
status
reason
result
created_at
updated_at
executed_at
```

The action result records the operational outcome.

The action state is intentionally separate from exception lifecycle state.

For example:

```text
Controlled Action
    → COMPLETED

Exception
    → OPEN
```

is valid.

This ensures that completing an investigation/review action does not falsely imply that the underlying financial exception has been resolved.

---

## 18. Human Review Boundary

Human review remains an explicit control point for unresolved operational exceptions.

The controller identifies whether human review is required.

The architecture intentionally avoids:

```text
AI
 ↓
Automatic decision
 ↓
Automatic resolution
```

Instead, it follows:

```text
AI Recommendation
        ↓
Deterministic Controller
        ↓
Controlled Operational Action
        ↓
Human Review
        ↓
Explicit Exception Resolution
```

This preserves human authority over financial exception resolution.

---

## 19. Audit Architecture

Every controlled remediation attempt is auditable.

The audit trail records events such as:

```text
CONTROLLED_ACTION_CREATED
CONTROLLED_ACTION_STARTED
CONTROLLED_ACTION_COMPLETED
CONTROLLED_ACTION_FAILED
CONTROLLED_ACTION_REJECTED
```

The audit record contains:

```text
payment_id
controlled_action_id
event_type
message
created_at
```

Successful actions and rejected actions are both recorded.

This provides traceability for:

* what action was requested
* why it was requested
* whether it was permitted
* whether execution started
* whether execution completed
* whether the request was rejected

The audit log is intentionally independent from the controlled-action lifecycle so that rejected attempts can also be preserved as part of the audit history.

---

## 20. End-to-End Financial Control Flow

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
                            ▼
                 ┌──────────────────────┐
                 │  Trusted AI Context  │
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
                 └──────────────────────┘
```

The system therefore progresses from raw payment and settlement events to financial truth, operational intelligence, controlled action, and finally auditable human-governed resolution.

---

## 21. Data Persistence Architecture

The PostgreSQL database currently persists the major financial and operational entities:

```text
transactions
settlements
exception_lifecycles
controlled_actions
audit_logs
```

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
```

This separation prevents operational workflow state and audit history from being confused with the underlying financial records.

---

## 22. Migration Layer

Alembic manages database schema evolution.

Schema changes are introduced through migration files and applied to the running PostgreSQL database.

The migration history currently includes the evolution of:

```text
Transaction schema
Settlement schema
Exception lifecycle schema
Controlled action schema
Controlled action result fields
Audit log schema
```

Database migrations ensure that application models and the PostgreSQL schema remain synchronized.

---

## 23. Architectural Principles

### Deterministic Financial Core

Financial correctness must not depend on probabilistic AI output.

The reconciliation engine establishes the factual financial state first.

Financial impact and priority calculations are also governed by deterministic application rules.

AI operates on top of these trusted results.

---

### AI as an Intelligence Layer, Not a Financial Authority

AI is used to:

```text
Explain
Contextualize
Prioritize
Recommend
```

AI is not trusted to:

```text
Define financial truth
Invent financial exposure
Modify financial records
Authorize arbitrary actions
Move money
Resolve exceptions automatically
```

---

### Deterministic Control Boundary

Operational actions are authorized through deterministic controller and validation logic.

The system follows:

```text
AI Recommendation
        ↓
Deterministic Authorization
        ↓
Controlled Execution
```

This prevents arbitrary model output from becoming an operational command.

---

### Separation of Concerns

The architecture separates:

```text
API Layer

Schema / Validation

Business Services

Financial Models

Operational Models

AI Integration

Control Logic

Audit Logging

Database
```

This makes the system easier to test, reason about, extend, and govern.

---

### Financial Precision

Monetary calculations use `Decimal` and PostgreSQL fixed-precision numeric fields.

Floating-point arithmetic is avoided for financial values.

---

### Explicit Uncertainty

The system does not fabricate financial impact when the available data cannot safely quantify it.

Unknown financial exposure remains unknown.

This is particularly important for currency mismatches and invalid operational states.

---

### Lifecycle Separation

Financial state, exception lifecycle, and controlled-action lifecycle are separate concepts.

For example:

```text
Reconciliation State
        ≠
Exception Lifecycle
        ≠
Controlled Action Status
```

This prevents operational workflow completion from being mistaken for financial resolution.

---

### Human-in-the-Loop Control

Unresolved financial exceptions remain subject to human review and explicit resolution.

The system assists operators rather than silently replacing financial-control decisions with autonomous AI behavior.

---

### Auditability

Important operational actions and rejected action attempts produce audit records.

The system should be able to answer:

```text
What happened?
Why did it happen?
Which action was requested?
Was it permitted?
Did it execute?
What was the result?
Was the exception ultimately resolved?
```

---

### Incremental Evolution

The architecture is intentionally developed in phases.

Each phase adds a meaningful capability while preserving the deterministic financial foundation.

The system has evolved through:

```text
Phase 1 → Transaction Foundation
Phase 2 → Settlement Ingestion
Phase 3 → Reconciliation Engine
Phase 4 → Exception Intelligence + AI + Controller
Phase 5 → Controlled Remediation + Auditability
```

Future phases should extend this architecture rather than bypass its existing financial and control boundaries.

---

## 24. Current Architectural State

The architecture has progressed from a basic transaction and settlement data layer into a complete financial-control pipeline:

```text
                 DATA FOUNDATION
                       │
                       ▼
              Transaction + Settlement
                       │
                       ▼
              RECONCILIATION
                       │
                       ▼
             EXCEPTION INTELLIGENCE
                       │
                       ▼
           FINANCIAL IMPACT + PRIORITY
                       │
                       ▼
              AI-ASSISTED ANALYSIS
                       │
                       ▼
            DETERMINISTIC CONTROLLER
                       │
                       ▼
             CONTROLLED REMEDIATION
                       │
                       ▼
                 AUDIT TRAIL
                       │
                       ▼
              HUMAN RESOLUTION
```

The central design philosophy is:

> **AI should help the payment operations system understand and prioritize problems, but deterministic financial logic and controlled workflows must remain responsible for what the system is allowed to do.**

This architecture is intended to support a Razorpay-like settlement environment where correctness, financial exposure, operational risk, controlled remediation, human oversight, and auditability are first-class concerns.
