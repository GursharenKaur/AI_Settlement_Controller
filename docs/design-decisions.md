# Design Decisions — AI Settlement Controller

This document records important engineering decisions made during the development of the **AI Settlement Controller** and the reasoning behind them.

The purpose is to make the project's technical evolution understandable, explainable, and auditable.

The project follows a core principle:

> **AI should assist with understanding and recommendation, while deterministic financial logic and controlled workflows remain responsible for correctness, authorization, and operational safety.**

---

## DD-001 — Deterministic Reconciliation Before AI

**Decision:** Build deterministic reconciliation before introducing AI-based analysis.

### Rationale

Financial reconciliation is fundamentally a correctness problem.

The system must first establish facts such as expected payment amount, actual settlement amount, settlement existence, currency compatibility, transaction/settlement state compatibility, and amount differences.

These facts should be derived deterministically.

### Consequence

The system follows:

```text
Financial Data
      ↓
Deterministic Reconciliation
      ↓
Exception Intelligence
      ↓
AI Analysis
```

---

## DD-002 — Use Decimal for Monetary Values

**Decision:** Represent monetary values using Python `Decimal` and PostgreSQL fixed-precision numeric fields.

### Rationale

Floating-point arithmetic can introduce precision errors.

### Consequence

Monetary values use fixed-precision storage such as:

```text
NUMERIC(12,2)
```

and application-level `Decimal`.

---

## DD-003 — Separate Transaction and Settlement Models

**Decision:** Maintain separate `Transaction` and `Settlement` entities.

### Rationale

A payment transaction and its settlement are different financial events.

### Consequence

Reconciliation happens across the two datasets rather than treating them as one record.

```text
Transaction
     +
Settlement
     ↓
Reconciliation
```

---

## DD-004 — Use `payment_id` as the Initial Reconciliation Key

**Decision:** Use `payment_id` to associate transaction and settlement records.

### Rationale

Both records contain the payment identifier, providing a simple initial relationship.

### Consequence

```text
Transaction.payment_id
        ↕
Settlement.payment_id
```

More sophisticated matching can be introduced later if required.

---

## DD-005 — Database-Level Uniqueness for Primary Identifiers

**Decision:** Enforce uniqueness at the database level for identifiers that must be unique.

### Rationale

Application-level duplicate checks alone are insufficient under concurrent requests.

### Consequence

Uniqueness is enforced for:

```text
transactions.payment_id
settlements.settlement_id
```

---

## DD-006 — Validate Financial Input Before Persistence

**Decision:** Validate incoming records using Pydantic before writing to PostgreSQL.

### Rationale

Malformed financial records should be rejected as early as possible.

### Consequence

```text
Input
  ↓
Pydantic Validation
  ↓
Business Processing
  ↓
Database
```

---

## DD-007 — Support Partial Success During CSV Ingestion

**Decision:** A malformed CSV row should not automatically prevent valid rows from being ingested.

### Rationale

Settlement files may contain isolated bad records.

### Consequence

Each row is independently classified as:

```text
created
duplicate
failed
```

Valid records continue while invalid records remain visible for correction.

---

## DD-008 — Keep Ingestion Processing Outside API Routes

**Decision:** Settlement parsing and batch-processing logic live in services rather than directly inside FastAPI route handlers.

### Rationale

This improves testability, maintainability, reuse, and separation of concerns.

### Consequence

Dedicated services contain business processing such as:

```text
CSV Parsing
Settlement Ingestion
Batch Processing
Reconciliation
Exception Intelligence
Controlled Actions
Audit Logging
```

---

## DD-009 — Use Alembic for Schema Evolution

**Decision:** Database schema changes are managed through Alembic migrations.

### Rationale

The project needs a reproducible and version-controlled database schema.

### Consequence

Schema changes follow:

```text
Model Change
     ↓
Alembic Migration
     ↓
Database Upgrade
     ↓
Schema Verification
```

---

## DD-010 — Complete Core Features Before Advanced Enhancements

**Decision:** Prioritize completion of planned core phases before significant advanced production-style enhancements.

### Rationale

The project is being developed for a buildathon with a defined scope.

### Consequence

```text
Core Functionality
       ↓
End-to-End System
       ↓
Verification
       ↓
Advanced Improvements
```

---

## DD-011 — Keep the Architecture Extensible for AI

**Decision:** The deterministic financial layer must not depend on the specific AI implementation.

### Rationale

AI providers and models may evolve.

### Consequence

```text
Financial Records
      ↓
Deterministic Processing
      ↓
Structured Context
      ↓
AI Analysis
```

---

## DD-012 — Build and Verify Incrementally

**Decision:** Each development phase is implemented in small, verifiable steps.

### Rationale

The project contains multiple interacting layers.

### Consequence

Important changes are verified through imports, schema validation, API/OpenAPI inspection, database inspection, migration checks, API requests, and end-to-end workflow checks.

---

# Phase 3 — Reconciliation Decisions

## DD-013 — Reconciliation Must Produce Explicit Operational States

**Decision:** Reconciliation results use explicit deterministic status categories rather than a simple matched/unmatched boolean.

### Consequence

```text
MATCHED
AMOUNT_MISMATCH
MISSING_SETTLEMENT
CURRENCY_MISMATCH
INVALID_STATE
```

Drift direction is:

```text
NONE
UNDER_SETTLED
OVER_SETTLED
```

---

## DD-014 — Reconciliation Rules Remain Deterministic

**Decision:** Reconciliation classifications are determined by explicit application rules rather than AI.

### Consequence

The reconciliation layer evaluates settlement existence, amount equality/difference, currency equality, and transaction/settlement state.

---

# Phase 4 — Exception Intelligence Decisions

## DD-015 — Convert Reconciliation Results into Structured Exceptions

**Decision:** Reconciliation results are transformed into operational exception categories.

### Consequence

```text
NONE
MISSING_SETTLEMENT
UNDER_SETTLEMENT
OVER_SETTLEMENT
CURRENCY_MISMATCH
INVALID_STATE
```

---

## DD-016 — Severity Must Be Deterministic

**Decision:** Exception severity is assigned using deterministic business rules.

### Consequence

```text
MISSING_SETTLEMENT → HIGH
CURRENCY_MISMATCH  → HIGH
INVALID_STATE      → HIGH
UNDER_SETTLEMENT   → MEDIUM
OVER_SETTLEMENT    → HIGH
MATCHED            → NONE
```

---

## DD-017 — Financial Impact Must Be Deterministic

**Decision:** Known financial impact is calculated by deterministic application logic and is never invented by AI.

### Consequence

```text
MISSING_SETTLEMENT → Expected transaction amount
UNDER_SETTLEMENT   → Amount difference
OVER_SETTLEMENT    → Amount difference
CURRENCY_MISMATCH  → Unknown / not safely quantifiable
INVALID_STATE      → Unknown / not safely quantifiable
```

---

## DD-018 — Priority Combines Severity and Financial Exposure

**Decision:** Exception priority is calculated deterministically using severity and known financial impact.

### Consequence

The system distinguishes:

```text
Most frequent problem
        versus
Largest financial exposure
```

---

## DD-019 — Individual and Portfolio Intelligence Are Separate

**Decision:** The system supports both payment-level and portfolio-level exception intelligence.

### Consequence

Individual analysis focuses on one payment, while portfolio analysis considers exception counts, severity, financial exposure, priority distribution, risk bands, dominant categories, and financial exposure concentration.

---

# AI and Safety Decisions

## DD-020 — AI Operates on Trusted Application Context

**Decision:** Gemini receives structured, application-generated context rather than independently querying or modifying financial records.

### Consequence

```text
Database
   ↓
Deterministic Services
   ↓
Trusted Context
   ↓
Gemini
   ↓
Explanation / Recommendation
```

---

## DD-021 — AI Must Not Invent Financial Values

**Decision:** AI analysis must preserve deterministic financial impact and explicitly acknowledge unknown exposure.

### Consequence

AI must use known financial impact when provided, must not independently invent monetary values, and must explicitly state when exposure cannot safely be quantified.

---

## DD-022 — AI Recommends; Deterministic Logic Controls

**Decision:** AI recommendations must not directly become executable operational commands.

### Consequence

```text
AI Recommendation
        ↓
Deterministic Controller
        ↓
Allowed Action
```

---

# Phase 5 — Controlled Remediation Decisions

## DD-023 — Introduce an Explicit Controlled Action Layer

**Decision:** Operational remediation must pass through a dedicated controlled-action layer.

### Consequence

Controlled actions are persisted with:

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

---

## DD-024 — Only Explicitly Allowed Actions Can Execute

**Decision:** Controlled actions are validated against a deterministic exception-to-action mapping.

### Consequence

```text
MISSING_SETTLEMENT → INVESTIGATE_MISSING_SETTLEMENT
UNDER_SETTLEMENT   → REVIEW_SETTLEMENT_AMOUNT
OVER_SETTLEMENT    → REVIEW_SETTLEMENT_AMOUNT
CURRENCY_MISMATCH  → REVIEW_CURRENCY_MISMATCH
INVALID_STATE      → INVESTIGATE_INVALID_STATE
```

Invalid combinations are rejected.

---

## DD-025 — Controlled Actions Have Their Own Lifecycle

**Decision:** Controlled action execution state is separate from exception lifecycle state.

### Consequence

Controlled actions use:

```text
REQUESTED
IN_PROGRESS
COMPLETED
FAILED
REJECTED
```

while exceptions separately use:

```text
OPEN
ACKNOWLEDGED
RESOLVED
```

---

## DD-026 — Controlled Action Completion Must Not Auto-Resolve an Exception

**Decision:** Completing a controlled action must not automatically resolve the associated exception.

### Consequence

```text
Controlled Action
    → COMPLETED

Exception
    → OPEN
```

can be valid.

Resolution requires an explicit lifecycle transition.

---

## DD-027 — Controlled Remediation Does Not Directly Modify Financial Records

**Decision:** Current controlled remediation actions are operational investigation/review actions rather than arbitrary financial mutations.

### Consequence

Current remediation focuses on:

```text
Investigate
Review
```

rather than:

```text
Change settlement amount
Move money
Modify transaction amount
Modify financial records
```

---

## DD-028 — Human Review Remains the Resolution Boundary

**Decision:** Unresolved financial exceptions remain subject to human review and explicit resolution.

### Consequence

```text
AI Analysis
      ↓
Controller Decision
      ↓
Controlled Action
      ↓
Human Review
      ↓
Explicit Resolution
```

---

## DD-029 — Audit Both Successful and Rejected Actions

**Decision:** Controlled action creation, execution, completion, failure, and rejection should be represented in the audit trail.

### Consequence

```text
CONTROLLED_ACTION_CREATED
CONTROLLED_ACTION_STARTED
CONTROLLED_ACTION_COMPLETED
CONTROLLED_ACTION_FAILED
CONTROLLED_ACTION_REJECTED
```

---

## DD-030 — Keep Audit History Separate from Operational State

**Decision:** Audit logs are stored separately from controlled-action state.

### Consequence

Controlled actions maintain current operational state, while audit logs preserve historical events.

---

## DD-031 — Preserve the Underlying Financial Record During Controlled Remediation

**Decision:** Controlled remediation must not silently change underlying transaction or settlement financial data.

### Consequence

The system preserves:

```text
Transaction Data
Settlement Data
Reconciliation Result
```

while tracking remediation separately through controlled actions, exception lifecycle, and audit logs.

---

# Architectural Governance Decisions

## DD-032 — Separate Financial Truth, Operational State, and Audit History

**Decision:** Financial data, operational workflow state, and audit history are separate concerns.

### Consequence

```text
Financial Truth
    ├── transactions
    └── settlements

Operational State
    ├── exception_lifecycles
    └── controlled_actions

Audit History
    └── audit_logs
```

---

## DD-033 — Prefer Explicit State Machines Over Implicit Status Changes

**Decision:** Important operational transitions should be explicit and controlled.

### Consequence

```text
OPEN
  ↓
ACKNOWLEDGED
  ↓
RESOLVED
```

and controlled actions follow their own execution lifecycle.

---

## DD-034 — Preserve Uncertainty Instead of Fabricating Certainty

**Decision:** When the system cannot safely determine a financial value or operational conclusion, it should preserve the uncertainty.

### Consequence

```text
financial_impact = unknown / None
```

is valid when source data is insufficient.

---

## DD-035 — The Controller Is the Operational Safety Boundary

**Decision:** The deterministic controller and controlled-action validation layer form the authorization boundary between intelligence and execution.

### Consequence

```text
Trusted Financial Context
        ↓
AI Analysis
        ↓
Controller Decision
        ↓
Action Validation
        ↓
Controlled Execution
        ↓
Audit
        ↓
Human Resolution
```

---

# Current Development Philosophy

## DD-036 — Evolve from Detection to Controlled Financial Operations

**Decision:** The project should evolve beyond anomaly detection into an auditable financial-control workflow.

### Consequence

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
```

---

## DD-037 — Preserve the Deterministic Core as the System Expands

**Decision:** Future phases should extend the existing control architecture rather than bypassing it.

### Consequence

New AI capabilities, automation, dashboards, or operational workflows should integrate through:

```text
Transaction / Settlement Data
          ↓
Reconciliation
          ↓
Exception Intelligence
          ↓
Financial Impact / Priority
          ↓
AI Analysis
          ↓
Controller
          ↓
Controlled Action
          ↓
Audit
```

---

# Phase 6 — Operational Control and Risk Decisions

## DD-038 — Operational Control Is a Read-Only Projection

**Decision:** The operational control layer derives a read-only representation of existing financial and operational state.

### Rationale

Operational users need a consolidated view of settlement exceptions, remediation progress, audit history, and risk without allowing dashboard or monitoring APIs to mutate the underlying system.

Creating a separate operational processing path could risk duplicating financial logic and introducing inconsistent state.

### Consequence

Operational control APIs consume:

```text
Reconciliation
Exception Intelligence
Priority
Lifecycle
Controller Decision
Controlled Actions
Audit History
```

and expose a derived operational representation.

They do not:

```text
Modify financial records
Execute actions
Resolve exceptions
Create audit events
Invoke AI
```

---

## DD-039 — Operational Risk Must Reuse Existing Deterministic Risk State

**Decision:** The operational risk queue must consume existing deterministic exception, financial-impact, and priority results rather than independently recalculating them.

### Rationale

Duplicating financial-impact or priority calculations in the operational layer could create conflicting interpretations of the same exception.

### Consequence

The operational risk layer derives its queue from the existing operational control representation.

It does not create a second financial-impact calculation or alternative priority algorithm.

This preserves consistency between:

```text
Exception Intelligence
Risk Queue
Risk Summary
Control Summary
```

---

## DD-040 — Explicit Operational Attention States

**Decision:** Operational attention should be represented using explicit deterministic states.

### Rationale

A dashboard should not need to infer operational urgency from several independent fields.

### Consequence

The system uses:

```text
ACTION_REQUIRED
IN_PROGRESS
HUMAN_RESOLUTION_REQUIRED
MONITOR
NO_ACTION_REQUIRED
```

The classification is deterministic and considers lifecycle state, remediation state, and human-review requirements.

---

## DD-041 — Risk Queue Ordering Must Be Deterministic

**Decision:** Operational risk ordering must be deterministic and explainable.

### Rationale

Operational users need predictable queue behavior.

### Consequence

The queue is ordered by:

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

---

## DD-042 — Missing Lifecycle Persistence Must Not Suppress Risk

**Decision:** An exception with no persisted lifecycle record must still be eligible for operational attention.

### Rationale

A newly identified exception may exist before a lifecycle record has been persisted.

Treating a null lifecycle as equivalent to "no action required" could hide a genuine financial exception.

### Consequence

If:

```text
lifecycle_status = null
```

but:

```text
human_review_required = true
```

the operational risk state can still be:

```text
ACTION_REQUIRED
```

---

## DD-043 — Operational Detail Must Not Become an Execution Endpoint

**Decision:** Operational detail and dashboard APIs must remain strictly read-only.

### Rationale

A monitoring or dashboard request should never unexpectedly trigger remediation, lifecycle transitions, financial mutation, or audit side effects.

### Consequence

The operational detail layer can:

```text
Read
Reconcile
Assess
Aggregate
Correlate
```

but cannot:

```text
Execute
Resolve
Mutate
Audit
```

Execution remains exclusively behind the controlled-action execution workflow.

---

## DD-044 — Operational Control Is the Bridge from Exception Detection to Financial Operations

**Decision:** The operational control layer should evolve the system from exception detection and remediation into an operational financial-control platform.

### Rationale

A settlement controller is valuable not only because it can identify discrepancies, but because it can help operations determine:

```text
What requires attention?
What is the financial exposure?
What is the priority?
What action is permitted?
What remediation has occurred?
What remains unresolved?
What audit history exists?
What should operations focus on next?
```

### Consequence

The architecture evolves as:

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
Execute Safely
   ↓
Audit
   ↓
Resolve Explicitly
```

The operational control layer becomes the bridge between the underlying financial-control engine and an eventual operational dashboard or control center.

---

# Decision Summary

The major architectural decisions made so far can be summarized as:

```text
1. Financial correctness is deterministic.

2. Monetary values use Decimal and fixed-precision storage.

3. Transactions and settlements remain separate financial entities.

4. Reconciliation uses explicit, explainable rules.

5. Reconciliation results become structured exceptions.

6. Severity, financial impact, and priority are deterministic.

7. AI operates on trusted application-generated context.

8. AI explains and recommends; it does not define financial truth.

9. AI cannot invent financial exposure.

10. AI recommendations pass through a deterministic controller.

11. Only explicitly allowed controlled actions can execute.

12. Controlled action state is separate from exception lifecycle state.

13. Completing an operational action does not automatically resolve an exception.

14. Current remediation does not directly modify financial records.

15. Human review remains the resolution boundary.

16. Successful and rejected operational attempts are audited.

17. Financial data, operational state, and audit history remain separate.

18. Uncertainty is preserved rather than fabricated.

19. The controller and validation layer form the operational safety boundary.

20. Operational control and risk views are read-only projections of existing state.

21. Operational risk reuses deterministic financial and priority state.

22. Operational attention states are explicit and deterministic.

23. Risk queue ordering is deterministic and explainable.

24. Missing lifecycle persistence must not suppress actionable risk.

25. Operational detail APIs cannot become execution paths.

26. The system evolves from exception detection toward controlled, auditable financial operations.
```

The resulting design principle is:

> **AI recommends. Deterministic logic decides what is allowed. Controlled workflows execute. Humans retain resolution authority. Audit logs preserve what happened. Operational control makes that state visible and actionable.**
