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

The system must first establish facts such as:

* expected payment amount
* actual settlement amount
* whether a settlement exists
* whether currencies match
* whether transaction and settlement states are compatible
* whether an amount difference exists

These facts should be derived deterministically.

AI can later help explain, prioritize, or investigate anomalies, but it should not be responsible for determining basic financial arithmetic or reconciliation truth.

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

The AI layer therefore operates on top of established financial facts rather than creating those facts.

---

## DD-002 — Use Decimal for Monetary Values

**Decision:** Represent monetary values using Python `Decimal` and PostgreSQL fixed-precision numeric fields.

### Rationale

Floating-point arithmetic can introduce precision errors.

Financial calculations require predictable decimal precision and consistent comparison behavior.

### Consequence

Monetary values are stored using PostgreSQL numeric fields such as:

```text
NUMERIC(12,2)
```

and represented in application code using:

```text
Decimal
```

Financial comparisons and drift calculations therefore avoid floating-point arithmetic.

---

## DD-003 — Separate Transaction and Settlement Models

**Decision:** Maintain separate `Transaction` and `Settlement` entities.

### Rationale

A payment transaction and its settlement are different financial events.

A transaction represents the payment-side event.

A settlement represents the downstream settlement-side event.

Keeping them separate allows the system to identify situations such as:

* missing settlement
* amount mismatch
* currency mismatch
* invalid operational state
* unexpected settlement behavior

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

Both transaction and settlement records contain the payment identifier.

This provides a simple and explainable initial relationship for deterministic reconciliation.

### Consequence

The reconciliation engine begins with:

```text
Transaction.payment_id
        ↕
Settlement.payment_id
```

More sophisticated matching strategies can be introduced later if required.

---

## DD-005 — Database-Level Uniqueness for Primary Identifiers

**Decision:** Enforce uniqueness at the database level for identifiers that must be unique.

### Rationale

Application-level duplicate checks alone are insufficient because concurrent requests can still produce duplicates.

Database constraints provide the final integrity boundary.

### Consequence

The system enforces uniqueness for:

```text
transactions.payment_id
settlements.settlement_id
```

Application code handles integrity errors and converts them into meaningful API or ingestion outcomes.

---

## DD-006 — Validate Financial Input Before Persistence

**Decision:** Validate incoming records using Pydantic before writing them to PostgreSQL.

### Rationale

Malformed financial records should be rejected as early as possible.

Examples include:

* negative amounts
* missing identifiers
* invalid timestamps
* invalid currencies
* invalid field lengths
* malformed request structures

### Consequence

The validation boundary follows:

```text
Input
  ↓
Pydantic Validation
  ↓
Business Processing
  ↓
Database
```

This reduces the amount of invalid data reaching core financial processing.

---

## DD-007 — Support Partial Success During CSV Ingestion

**Decision:** A malformed CSV row should not automatically prevent valid rows from being ingested.

### Rationale

Settlement files are operational data sources and may contain isolated bad records.

Discarding an entire valid file because of one malformed row can create unnecessary operational delay.

### Consequence

Each row is independently classified as:

```text
created
duplicate
failed
```

Ingestion errors preserve information about the affected row and validation failure.

This allows valid settlement records to continue through the system while invalid records remain visible for correction.

---

## DD-008 — Keep Ingestion Processing Outside API Routes

**Decision:** Settlement parsing and batch-processing logic are implemented in services rather than directly inside FastAPI route handlers.

### Rationale

Keeping business logic outside the API layer improves:

* testability
* maintainability
* reuse
* separation of concerns

It also establishes a consistent pattern for reconciliation and later control services.

### Consequence

The API layer orchestrates operations while dedicated services contain business processing such as:

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

Manual database changes make it difficult to reproduce the environment and verify that application models match the actual database.

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

The same approach is used as new operational entities such as controlled actions and audit logs are introduced.

---

## DD-010 — Complete Core Features Before Advanced Enhancements

**Decision:** Prioritize completion of the planned core phases before spending significant time on advanced production-style enhancements.

### Rationale

The project is being developed for a buildathon with a defined scope.

A polished individual component is less valuable if major capabilities of the overall system remain unfinished.

### Consequence

The development priority is:

```text
Core Functionality
       ↓
End-to-End System
       ↓
Verification
       ↓
Advanced Improvements
```

Advanced ingestion capabilities, production hardening, architecture refinements, and other enhancements can be revisited after the core phases are complete.

---

## DD-011 — Keep the Architecture Extensible for AI

**Decision:** The deterministic financial layer must not depend on the specific AI implementation.

### Rationale

AI technology and providers may evolve.

The financial facts produced by reconciliation should remain usable regardless of the specific model or AI provider.

### Consequence

AI components consume structured application-generated context rather than directly manipulating raw financial records.

The current architecture therefore follows:

```text
Financial Records
      ↓
Deterministic Processing
      ↓
Structured Context
      ↓
AI Analysis
```

This keeps the financial core independent of the AI provider.

---

## DD-012 — Build and Verify Incrementally

**Decision:** Each development phase is implemented in small, verifiable steps.

### Rationale

The project contains multiple interacting layers:

```text
API
Schemas
Services
Models
Database
Migrations
AI Integration
Control Logic
Auditability
```

Incremental verification reduces the chance of hidden integration errors.

### Consequence

Important changes are verified through a combination of:

* Python imports
* schema validation
* API/OpenAPI inspection
* database inspection
* migration checks
* actual API requests
* end-to-end workflow checks

This incremental verification approach continues throughout the remaining phases.

---

# Phase 3 — Reconciliation Decisions

## DD-013 — Reconciliation Must Produce Explicit Operational States

**Decision:** Reconciliation results use explicit, deterministic status categories rather than a simple matched/unmatched boolean.

### Rationale

A payment that does not reconcile can fail for fundamentally different reasons.

For example:

```text
Missing Settlement
Amount Mismatch
Currency Mismatch
Invalid State
```

These require different operational responses.

A binary result would lose important financial and operational context.

### Consequence

The reconciliation engine produces explicit states:

```text
MATCHED
AMOUNT_MISMATCH
MISSING_SETTLEMENT
CURRENCY_MISMATCH
INVALID_STATE
```

It also represents settlement drift direction as:

```text
NONE
UNDER_SETTLED
OVER_SETTLED
```

This structured output becomes the foundation for exception intelligence.

---

## DD-014 — Reconciliation Rules Remain Deterministic

**Decision:** Reconciliation classifications are determined by explicit application rules rather than AI.

### Rationale

The system must be able to explain exactly why a payment was classified as matched or exceptional.

The same financial inputs should produce the same reconciliation result.

### Consequence

The reconciliation layer deterministically evaluates:

```text
Settlement existence
Amount equality
Amount difference
Currency equality
Transaction state
Settlement state
```

For example:

```text
Transaction amount = Settlement amount
and currencies match
        ↓
MATCHED
```

while:

```text
Settlement amount < Transaction amount
        ↓
AMOUNT_MISMATCH
        +
UNDER_SETTLED
```

AI is not involved in these fundamental classifications.

---

# Phase 4 — Exception Intelligence Decisions

## DD-015 — Convert Reconciliation Results into Structured Exceptions

**Decision:** Reconciliation results are transformed into operational exception categories.

### Rationale

A reconciliation result describes what happened financially.

An exception category describes what requires operational attention.

Separating these concepts allows the system to evolve from simple comparison into payment-operations intelligence.

### Consequence

The system uses exception categories:

```text
NONE
MISSING_SETTLEMENT
UNDER_SETTLEMENT
OVER_SETTLEMENT
CURRENCY_MISMATCH
INVALID_STATE
```

These categories become inputs to severity, financial-impact, priority, AI analysis, and controller decisions.

---

## DD-016 — Severity Must Be Deterministic

**Decision:** Exception severity is assigned using deterministic business rules.

### Rationale

Severity affects operational attention and therefore should not vary based on probabilistic AI output.

### Consequence

The current severity mapping is:

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

AI may explain why an exception is significant, but the authoritative severity classification remains application-controlled.

---

## DD-017 — Financial Impact Must Be Deterministic

**Decision:** Known financial impact is calculated by deterministic application logic and is never invented by AI.

### Rationale

Financial exposure is a high-sensitivity value.

Allowing an AI model to independently calculate or estimate authoritative financial impact could introduce fabricated or inconsistent monetary values.

### Consequence

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

If the available data cannot safely quantify the exposure, the system preserves that uncertainty.

---

## DD-018 — Priority Combines Severity and Financial Exposure

**Decision:** Exception priority is calculated deterministically using severity and known financial impact.

### Rationale

Operational importance is not determined by exception type alone.

A relatively simple discrepancy can become high priority when a large amount of money is involved.

### Consequence

The priority system considers:

```text
Exception Severity
        +
Known Financial Impact
        ↓
Priority Score
```

Priority scoring remains deterministic.

This allows the system to distinguish between:

```text
Most frequent problem
        versus
Largest financial exposure
```

which may be different categories.

---

## DD-019 — Individual and Portfolio Intelligence Are Separate

**Decision:** The system supports both payment-level and portfolio-level exception intelligence.

### Rationale

An individual exception answers:

> "What happened to this payment?"

Portfolio intelligence answers:

> "What is happening across the settlement operation?"

Both perspectives are required for an operational control system.

### Consequence

Individual analysis focuses on a specific payment.

Portfolio analysis considers:

```text
Exception counts
Severity distribution
Financial exposure
Priority distribution
Risk bands
Dominant categories
Financial exposure concentration
Open operational risk
```

This allows the system to prioritize systemic operational concerns rather than only individual records.

---

# AI and Safety Decisions

## DD-020 — AI Operates on Trusted Application Context

**Decision:** Gemini receives structured, application-generated context rather than independently querying or modifying financial records.

### Rationale

The AI should interpret trusted facts rather than establish financial truth from raw data.

This reduces the risk of inconsistent calculations and hallucinated financial information.

### Consequence

The flow is:

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

The AI therefore acts as an intelligence layer on top of the application's financial control layer.

---

## DD-021 — AI Must Not Invent Financial Values

**Decision:** AI analysis must preserve deterministic financial impact and explicitly acknowledge unknown exposure.

### Rationale

A plausible-sounding monetary estimate from an LLM is not an authoritative financial calculation.

Fabricated amounts could create serious operational risk in a payment-settlement environment.

### Consequence

AI analysis is instructed to:

* use known financial impact when provided
* not independently invent monetary values
* distinguish known from unknown exposure
* explicitly state when financial impact cannot safely be quantified

This establishes a hard boundary between AI explanation and financial truth.

---

## DD-022 — AI Recommends; Deterministic Logic Controls

**Decision:** AI recommendations must not directly become executable operational commands.

### Rationale

An LLM can provide useful reasoning but is probabilistic.

Operational actions affecting financial operations require predictable and enforceable rules.

### Consequence

The architecture follows:

```text
AI Recommendation
        ↓
Deterministic Controller
        ↓
Allowed Action
```

The AI can recommend an action, but the controller determines whether that action is permitted for the given exception.

---

# Phase 5 — Controlled Remediation Decisions

## DD-023 — Introduce an Explicit Controlled Action Layer

**Decision:** Operational remediation must pass through a dedicated controlled-action layer.

### Rationale

The system should not allow AI output to directly trigger arbitrary operational behavior.

A separate controlled-action model creates an explicit boundary between:

```text
Decision
```

and:

```text
Execution
```

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

Supported action types are explicitly enumerated.

---

## DD-024 — Only Explicitly Allowed Actions Can Execute

**Decision:** Controlled actions are validated against a deterministic exception-to-action mapping.

### Rationale

A valid exception does not imply that every possible action is valid for that exception.

The system must enforce action authorization independently of AI recommendations.

### Consequence

The current mapping is:

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

Invalid combinations are rejected.

For example:

```text
UNDER_SETTLEMENT
        +
INVESTIGATE_INVALID_STATE
        ↓
REJECTED
```

This creates a deterministic authorization boundary.

---

## DD-025 — Controlled Actions Have Their Own Lifecycle

**Decision:** Controlled action execution state is separate from exception lifecycle state.

### Rationale

An operational action and the underlying financial exception represent different concepts.

An investigation can complete without the financial issue being resolved.

### Consequence

Controlled actions use states such as:

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

This prevents one state machine from incorrectly representing another.

---

## DD-026 — Controlled Action Completion Must Not Auto-Resolve an Exception

**Decision:** Completing a controlled action must not automatically resolve the associated exception.

### Rationale

An action such as:

```text
Investigate Missing Settlement
```

or:

```text
Review Settlement Amount
```

does not necessarily mean that the underlying financial discrepancy has been corrected.

Automatically resolving the exception would create a false representation of financial state.

### Consequence

The system explicitly allows:

```text
Controlled Action
    → COMPLETED

Exception
    → OPEN
```

The exception lifecycle remains authoritative.

Resolution requires an explicit lifecycle transition.

---

## DD-027 — Controlled Remediation Does Not Directly Modify Financial Records

**Decision:** Current controlled remediation actions are operational investigation/review actions rather than arbitrary financial mutations.

### Rationale

The project's control layer should demonstrate safe operational automation without allowing an AI-generated command to directly modify payment or settlement money values.

### Consequence

Controlled remediation currently focuses on actions such as:

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

The architecture can be extended later with additional tightly controlled operations if required, but any such operation must have explicit authorization and safety rules.

---

## DD-028 — Human Review Remains the Resolution Boundary

**Decision:** Unresolved financial exceptions remain subject to human review and explicit resolution.

### Rationale

Payment-settlement discrepancies can have financial, operational, and compliance implications.

The system should assist operators rather than silently replace financial-control decisions with autonomous AI behavior.

### Consequence

The intended flow is:

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

The controller can identify that human review is required, but it does not silently resolve the exception.

---

## DD-029 — Audit Both Successful and Rejected Actions

**Decision:** Controlled action creation, execution, completion, failure, and rejection should be represented in the audit trail.

### Rationale

An audit system should not only record successful operations.

Rejected actions are also important because they demonstrate that the control boundary prevented an invalid operation.

### Consequence

The audit layer records events such as:

```text
CONTROLLED_ACTION_CREATED
CONTROLLED_ACTION_STARTED
CONTROLLED_ACTION_COMPLETED
CONTROLLED_ACTION_FAILED
CONTROLLED_ACTION_REJECTED
```

This makes it possible to answer:

```text
What was requested?
Why was it requested?
Was it permitted?
Did execution begin?
Did it complete?
Was it rejected?
```

---

## DD-030 — Keep Audit History Separate from Operational State

**Decision:** Audit logs are stored separately from controlled-action state.

### Rationale

Operational state answers:

> "What is the current state of this action?"

Audit history answers:

> "What happened over time?"

These are different requirements.

### Consequence

Controlled actions maintain current operational state, while audit logs preserve historical events.

The audit trail is intentionally append-oriented and is not used as a replacement for current workflow state.

---

## DD-031 — Preserve the Underlying Financial Record During Controlled Remediation

**Decision:** Controlled remediation must not silently change the underlying transaction or settlement financial data.

### Rationale

The purpose of the remediation layer is to investigate and control operational exceptions.

Changing the underlying financial record without an explicit financial operation would make it impossible to distinguish original financial truth from subsequent operational actions.

### Consequence

The system preserves:

```text
Transaction Data
Settlement Data
Reconciliation Result
```

while tracking remediation separately through:

```text
Controlled Action
Exception Lifecycle
Audit Log
```

This preserves traceability between financial facts and operational handling.

---

# Architectural Governance Decisions

## DD-032 — Separate Financial Truth, Operational State, and Audit History

**Decision:** Financial data, operational workflow state, and audit history are separate concerns.

### Rationale

These data categories have different meanings and different integrity requirements.

### Consequence

The architecture separates:

```text
Financial Truth
    ├── transactions
    └── settlements

Operational State
    ├── exception lifecycles
    └── controlled actions

Audit History
    └── audit logs
```

This separation improves traceability and prevents workflow state from being confused with financial state.

---

## DD-033 — Prefer Explicit State Machines Over Implicit Status Changes

**Decision:** Important operational transitions should be explicit and controlled.

### Rationale

Financial operations benefit from predictable state transitions.

Implicit state changes can make the system difficult to reason about and audit.

### Consequence

Exception lifecycle transitions are explicitly controlled:

```text
OPEN
  ↓
ACKNOWLEDGED
  ↓
RESOLVED
```

Similarly, controlled actions follow an explicit execution lifecycle.

A completed controlled action does not implicitly transition an exception to `RESOLVED`.

---

## DD-034 — Preserve Uncertainty Instead of Fabricating Certainty

**Decision:** When the system cannot safely determine a financial value or operational conclusion, it should preserve the uncertainty.

### Rationale

In financial systems, an unknown value is safer than a fabricated value.

For example, currency mismatches may prevent safe determination of a monetary difference without an appropriate conversion context.

### Consequence

The system allows values such as:

```text
financial_impact = unknown / None
```

when the available data is insufficient.

AI explanations must preserve this distinction.

---

## DD-035 — The Controller Is the Operational Safety Boundary

**Decision:** The deterministic controller and controlled-action validation layer form the authorization boundary between intelligence and execution.

### Rationale

AI is useful for analysis but should not have unrestricted authority over operational behavior.

The controller provides a deterministic layer that can enforce permitted actions.

### Consequence

The final control sequence is:

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

The architecture therefore avoids:

```text
AI
 ↓
Arbitrary Action
 ↓
Financial Mutation
```

---

# Current Development Philosophy

## DD-036 — Evolve from Detection to Controlled Financial Operations

**Decision:** The project should evolve beyond anomaly detection into an auditable financial-control workflow.

### Rationale

A payment-settlement system should not stop at identifying that something is wrong.

It should help answer:

```text
What changed?
Why did it happen?
How much money is affected?
How serious is it?
What should happen next?
Was the action permitted?
What happened after the action?
Who / what resolved the exception?
```

### Consequence

The project's architectural evolution is:

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

This is the central product and engineering direction of the AI Settlement Controller.

---

## DD-037 — Preserve the Deterministic Core as the System Expands

**Decision:** Future phases should extend the existing control architecture rather than bypassing it.

### Rationale

Each additional capability should strengthen the financial-control workflow rather than introduce an uncontrolled parallel path.

### Consequence

Future components should integrate through the established layers:

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

New AI capabilities, automation, dashboards, or operational workflows should respect these boundaries.

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

20. The system evolves from detection toward controlled, auditable financial operations.
```

The resulting design principle is:

> **AI recommends. Deterministic logic decides what is allowed. Controlled workflows execute. Humans retain resolution authority. Audit logs preserve what happened.**

This principle should remain intact as subsequent phases are implemented.
