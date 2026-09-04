# Design Decisions — AI Settlement Controller

This document records important engineering decisions made during the development of the **AI Settlement Controller** and the reasoning behind them.

The purpose is to make the project's technical evolution understandable, explainable, and auditable.

The project follows a core principle:

> **AI should assist with understanding and recommendation, while deterministic financial logic and controlled workflows remain responsible for correctness, authorization, and operational safety.**

---

# Foundation Decisions

## DD-001 — Deterministic Reconciliation Before AI

**Decision:** Build deterministic reconciliation before introducing AI-based analysis.

### Rationale

Financial reconciliation is fundamentally a correctness problem.

### Consequence

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

---

## DD-025 — Controlled Actions Have Their Own Lifecycle

**Decision:** Controlled action execution state is separate from exception lifecycle state.

### Consequence

```text
REQUESTED
IN_PROGRESS
COMPLETED
FAILED
REJECTED
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

---

## DD-027 — Controlled Remediation Does Not Directly Modify Financial Records

**Decision:** Current controlled remediation actions are operational investigation/review actions rather than arbitrary financial mutations.

---

## DD-028 — Human Review Remains the Resolution Boundary

**Decision:** Unresolved financial exceptions remain subject to human review and explicit resolution.

---

## DD-029 — Audit Both Successful and Rejected Actions

**Decision:** Controlled action creation, execution, completion, failure, and rejection should be represented in the audit trail.

---

## DD-030 — Keep Audit History Separate from Operational State

**Decision:** Audit logs are stored separately from controlled-action state.

---

## DD-031 — Preserve the Underlying Financial Record During Controlled Remediation

**Decision:** Controlled remediation must not silently change underlying transaction or settlement financial data.

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

---

## DD-034 — Preserve Uncertainty Instead of Fabricating Certainty

**Decision:** When the system cannot safely determine a financial value or operational conclusion, it should preserve the uncertainty.

---

## DD-035 — The Controller Is the Operational Safety Boundary

**Decision:** The deterministic controller and controlled-action validation layer form the authorization boundary between intelligence and execution.

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

---

# Phase 6 — Operational Control and Risk Decisions

## DD-038 — Operational Control Is a Read-Only Projection

**Decision:** The operational control layer derives a read-only representation of existing financial and operational state.

---

## DD-039 — Operational Risk Must Reuse Existing Deterministic Risk State

**Decision:** The operational risk queue must consume existing deterministic exception, financial-impact, and priority results rather than independently recalculating them.

---

## DD-040 — Explicit Operational Attention States

**Decision:** Operational attention should be represented using explicit deterministic states.

### Consequence

```text
ACTION_REQUIRED
IN_PROGRESS
HUMAN_RESOLUTION_REQUIRED
MONITOR
NO_ACTION_REQUIRED
```

---

## DD-041 — Risk Queue Ordering Must Be Deterministic

**Decision:** Operational risk ordering must be deterministic and explainable.

### Consequence

```text
1. Attention rank
2. Priority score
3. Known financial impact
```

---

## DD-042 — Missing Lifecycle Persistence Must Not Suppress Risk

**Decision:** An exception with no persisted lifecycle record must still be eligible for operational attention.

---

## DD-043 — Operational Detail Must Not Become an Execution Endpoint

**Decision:** Operational detail and dashboard APIs must remain strictly read-only.

---

## DD-044 — Operational Control Is the Bridge from Exception Detection to Financial Operations

**Decision:** The operational control layer should evolve the system from exception detection and remediation into an operational financial-control platform.

---

# Phase 7 — Governance and Operational Resilience Decisions

## DD-045 — Enforce Explicit Operational State Transitions

**Decision:** Exception lifecycle and controlled-action state transitions must be explicitly validated.

### Rationale

Operational state must not change through arbitrary status assignment.

### Consequence

Illegal transitions are rejected deterministically.

The system preserves explicit state-machine semantics rather than relying on callers to behave correctly.

---

## DD-046 — Base Exception Aging on Authoritative Creation Time

**Decision:** Exception aging is calculated from the authoritative `ExceptionRecord.created_at`.

### Rationale

Operational aging should measure how long the persisted exception has existed, rather than relying on mutable or unrelated timestamps.

### Consequence

```text
0h <= age < 1h   → FRESH
1h <= age < 4h   → AGING
4h <= age < 24h  → ATTENTION
age >= 24h       → OVERDUE
```

Unknown age is not treated as overdue.

---

## DD-047 — Keep Governance Deterministic and Separate from AI

**Decision:** Governance level and escalation state are derived deterministically from exception, lifecycle, remediation, aging, and priority state.

### Rationale

Escalation is an operational-control decision and should remain predictable and explainable.

### Consequence

AI cannot change governance level or escalation status.

---

## DD-048 — Preserve Historical Audit Records

**Decision:** Strengthening audit schemas must not require rewriting historical audit records.

### Rationale

Historical evidence should remain historically faithful.

### Consequence

New transition evidence applies to relevant new events, while older records remain preserved.

---

# Phase 8 — Human Operations and Resolution Decisions

## DD-049 — Human Resolution Is a Separate Lifecycle from Controlled Remediation

**Decision:** Human resolution is distinct from controlled-action completion.

### Rationale

An investigation/review can finish without proving that the underlying exception is resolved.

### Consequence

```text
Controlled Action
    → COMPLETED

Exception
    → OPEN / ACKNOWLEDGED
```

can be valid until a human explicitly resolves the exception.

---

## DD-050 — Exception Resolution Requires Explicit Metadata

**Decision:** Resolving an exception requires a structured resolution reason and a non-empty resolution note.

### Rationale

A resolved financial exception should contain enough evidence to explain why the resolution occurred.

### Consequence

Resolution persists:

```text
resolution_reason
resolution_note
resolved_at
```

Supported reasons are:

```text
SETTLEMENT_CONFIRMED
MANUAL_RECONCILIATION
FALSE_POSITIVE
DUPLICATE_EXCEPTION
OTHER
```

---

## DD-051 — Human Lifecycle Transitions Must Be Audited

**Decision:** Acknowledgement and resolution transitions create explicit audit events.

### Consequence

```text
EXCEPTION_ACKNOWLEDGED
EXCEPTION_RESOLVED
```

Human lifecycle events are auditable independently of controlled actions.

---

## DD-052 — Human Resolution Cannot Bypass the State Machine

**Decision:** A resolution request is valid only from the appropriate lifecycle state.

### Consequence

```text
OPEN → ACKNOWLEDGED → RESOLVED
```

is valid, while invalid transitions are rejected without mutating the record.

---

# Phase 9 — Advanced Settlement Intelligence Decisions

## DD-053 — Historical Intelligence Must Reuse Deterministic Financial Assessment

**Decision:** Historical exception intelligence must derive from the existing transaction, settlement, reconciliation, and exception-assessment pipeline.

### Rationale

Historical analysis must use the same financial truth rules as current analysis.

### Consequence

Historical intelligence does not create an independent exception classifier.

---

## DD-054 — Historical Analysis Must Exclude the Current Payment

**Decision:** When analyzing historical context for a payment, the current payment is excluded from the historical comparison population.

### Rationale

Including the current payment would contaminate the historical baseline and could falsely inflate recurrence or timing evidence.

---

## DD-055 — ExceptionRecord Is Operational Lifecycle State, Not Historical Event History

**Decision:** The persisted exception lifecycle record is not treated as a historical exception-event log.

### Rationale

There is one operational lifecycle representation per payment, while historical intelligence must reason over financial transaction/settlement records and deterministic assessments.

### Consequence

Historical intelligence does not require redesigning `ExceptionRecord` into an event-history table.

---

## DD-056 — Recurrence Signals Must Be Explicit and Deterministic

**Decision:** Recurrence is represented through explicit population signals rather than opaque probability scores.

### Consequence

The system exposes signals such as:

```text
same_category_exception_count
same_currency_exception_count
same_category_and_currency_exception_count
recurrence_detected
```

These signals are evidence, not probabilistic risk predictions.

---

## DD-057 — Recurrence Must Preserve Population-Level Semantics

**Decision:** Population-level recurrence must not be described as proof that the current payment itself previously experienced the same exception.

### Rationale

A broader population pattern and a payment's own history are different claims.

### Consequence

AI and API semantics must preserve the distinction between:

```text
Current Payment
        versus
Historical Population
```

---

## DD-058 — Settlement Timing Is Contextual Evidence

**Decision:** Settlement timing deviation is provided as contextual evidence rather than being converted into an automatic risk or priority decision.

### Consequence

The system exposes:

```text
timing_available
settlement_delay_hours
historical_settlement_count
historical_average_delay_hours
timing_deviation_hours
```

It does not introduce an arbitrary `timing_deviation_detected` threshold.

---

## DD-059 — Missing Timing Evidence Must Remain Explicit

**Decision:** Timing analysis must preserve unavailable timestamps as unknown.

### Rationale

The system should not fabricate settlement delays or historical comparisons when required timestamps are absent.

### Consequence

If timing cannot be calculated:

```text
timing_available = false
settlement_delay_hours = null
timing_deviation_hours = null
```

---

## DD-060 — Population Pattern Intelligence Must Be Deterministic

**Decision:** Population exception patterns are calculated from deterministic exception assessments.

### Consequence

The pattern layer exposes:

```text
total_transactions
total_exceptions
exception counts by category
high-severity counts
recurring categories
```

It does not introduce an opaque risk score.

---

## DD-061 — Aggregate Financial Exposure by Currency

**Decision:** Population-level known financial impact is grouped by currency.

### Rationale

Amounts denominated in different currencies cannot safely be added without an explicit conversion basis.

### Consequence

Pattern intelligence represents:

```text
known_financial_impact_by_currency
```

rather than a blind cross-currency total.

---

## DD-062 — AI Investigation Must Use Trusted Deterministic Context

**Decision:** AI investigation receives structured context generated by deterministic application services.

### Consequence

```text
Database
   ↓
Deterministic Services
   ↓
Investigation Context
   ↓
Gemini
```

The model is not given authority to establish financial truth independently.

---

## DD-063 — AI Investigation Cannot Change Control Decisions

**Decision:** AI investigation output is explanatory and guidance-oriented and cannot mutate financial, lifecycle, remediation, priority, or governance state.

### Consequence

AI cannot:

```text
Change category
Change severity
Change financial impact
Change priority
Change governance
Create remediation
Execute remediation
Acknowledge
Resolve
```

---

## DD-064 — AI Must Preserve Evidence Gaps

**Decision:** AI investigation must explicitly communicate unavailable or insufficient evidence.

### Rationale

A trustworthy investigation assistant should distinguish evidence from inference.

### Consequence

Examples include:

```text
Timing unavailable
Financial impact unknown
Insufficient historical evidence
```

rather than fabricated conclusions.

---

## DD-065 — Investigation Guidance Remains Human-Owned

**Decision:** AI investigation guidance is guidance for an operator, not an autonomous operational command.

### Consequence

```text
AI Investigation
      ↓
Human Operator
      ↓
Controlled / Explicit Workflow
```

---

# Cross-Phase Architectural Decisions

## DD-066 — Preserve Separation Between Financial Truth, Operational State, and Audit History

**Decision:** Financial source data, operational workflow state, and audit history remain separate concerns as the system evolves.

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

## DD-067 — Preserve the Deterministic Safety Boundary as Intelligence Expands

**Decision:** New AI and intelligence capabilities must integrate above the deterministic financial/control layers rather than bypassing them.

### Consequence

```text
Financial Truth
      ↓
Deterministic Assessment
      ↓
Operational Control
      ↓
AI Context
      ↓
AI Explanation
      ↓
Human / Controlled Workflow
```

---

## DD-068 — Derived Intelligence Should Not Create a Second Financial Truth

**Decision:** Historical, timing, pattern, governance, and operational intelligence should derive from existing authoritative records and deterministic rules.

### Rationale

Multiple independent interpretations of the same financial records could produce contradictory results.

### Consequence

Derived intelligence reuses existing reconciliation and assessment semantics whenever applicable.

---

## DD-069 — Preserve Explicit Uncertainty Across All Intelligence Layers

**Decision:** Missing or non-quantifiable evidence remains explicitly unknown throughout downstream intelligence and AI layers.

### Consequence

```text
Unknown
   ↓
Unknown
   ↓
Explained as unknown
```

rather than becoming an invented value.

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

10. AI recommendations pass through deterministic control.

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

26. Governance and escalation remain deterministic.

27. Exception aging uses authoritative lifecycle creation time.

28. Illegal state transitions are rejected deterministically.

29. Historical intelligence reuses deterministic financial assessment.

30. Historical analysis excludes the current payment.

31. Exception lifecycle state is not historical event history.

32. Recurrence signals are explicit rather than opaque probabilities.

33. Population recurrence is not proof of current-payment history.

34. Settlement timing is contextual evidence, not automatic risk.

35. Missing timing evidence remains explicit.

36. Population patterns are deterministic.

37. Financial exposure is aggregated by currency.

38. AI investigation consumes trusted deterministic context.

39. AI investigation cannot mutate control state.

40. AI preserves evidence gaps.

41. Investigation guidance remains human-owned.

42. New intelligence layers must not create a second financial truth.

```

The resulting design principle is:

> **AI recommends and explains. Deterministic financial logic establishes truth and decides what is allowed. Controlled workflows execute permitted operational actions. Humans retain resolution authority. Governance determines escalation. Audit logs preserve what happened. Intelligence provides historical and population context without replacing the underlying financial truth.**
