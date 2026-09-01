# Design Decisions — AI Settlement Controller

This document records important engineering decisions made during the development of the AI Settlement Controller and the reasoning behind them.

The purpose is to make the project's technical evolution understandable and auditable.

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
* whether settlement timing is abnormal

These facts should be derived deterministically.

AI can later help explain, prioritize, or investigate anomalies, but it should not be responsible for determining basic financial arithmetic.

### Consequence

The system is being developed in the following order:

```text
Financial Data
     ↓
Deterministic Reconciliation
     ↓
Drift Detection
     ↓
AI Analysis
```

---

## DD-002 — Use Decimal for Monetary Values

**Decision:** Represent monetary values using Python `Decimal` and PostgreSQL fixed-precision numeric fields.

### Rationale

Floating-point arithmetic can introduce precision errors.

Financial calculations require predictable decimal precision.

### Consequence

Amounts are stored using:

```text
NUMERIC(12,2)
```

and represented in application code using:

```text
Decimal
```

---

## DD-003 — Separate Transaction and Settlement Models

**Decision:** Maintain separate `Transaction` and `Settlement` entities.

### Rationale

A payment transaction and its settlement are different financial events.

A transaction represents the payment-side event.

A settlement represents the later movement of funds through the settlement process.

Keeping them separate allows the system to identify situations such as:

* missing settlement
* delayed settlement
* amount mismatch
* duplicate settlement
* unexpected settlement behavior

### Consequence

Reconciliation happens across the two datasets rather than treating them as one record.

---

## DD-004 — Use `payment_id` as the Initial Reconciliation Key

**Decision:** Use `payment_id` to associate transaction and settlement records.

### Rationale

Both transaction and settlement records contain the payment identifier.

This provides a simple and explainable initial relationship for deterministic reconciliation.

### Consequence

The reconciliation engine can begin with:

```text
Transaction.payment_id
        ↕
Settlement.payment_id
```

More sophisticated reconciliation keys or matching strategies can be added later if the system requires them.

---

## DD-005 — Database-Level Uniqueness for Payment and Settlement Identifiers

**Decision:** Enforce uniqueness at the database level.

### Rationale

Application-level duplicate checks alone are insufficient because concurrent requests can still produce duplicates.

Database constraints provide the final integrity boundary.

### Consequence

The system uses unique constraints for:

```text
transactions.payment_id
settlements.settlement_id
```

Application code catches integrity errors and converts them into meaningful API/ingestion outcomes.

---

## DD-006 — Validate Financial Input Before Persistence

**Decision:** Validate incoming records using Pydantic before writing them to PostgreSQL.

### Rationale

Malformed financial records should be rejected as early as possible.

Examples include:

* negative amounts
* invalid timestamps
* missing identifiers
* invalid field lengths

### Consequence

The validation boundary sits before the persistence layer.

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

Settlement files are operational data sources and may contain isolated bad records.

Discarding an entire valid file because of one malformed row can create unnecessary operational delay.

### Consequence

Each row is classified independently as:

```text
created
duplicate
failed
```

Errors include the affected row and field.

---

## DD-008 — Keep Ingestion Processing Outside API Routes

**Decision:** Settlement parsing and batch-processing logic are implemented in services rather than directly inside FastAPI route handlers.

### Rationale

Keeping business logic outside the API layer improves:

* testability
* maintainability
* reuse
* separation of concerns

It also gives the future reconciliation engine a consistent architectural pattern.

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

---

## DD-010 — Complete Core Features Before Advanced Enhancements

**Decision:** Prioritize completion of the planned core phases before spending significant time on advanced production-style enhancements.

### Rationale

The project is being developed for a buildathon with a defined scope.

A polished individual component is less valuable if major capabilities of the overall system remain unfinished.

### Consequence

The development priority is:

```text
Core functionality
       ↓
End-to-end system
       ↓
Verification
       ↓
Advanced improvements
```

Advanced ingestion, controls, architecture refinements, and other enhancements can be revisited after the core phases are complete.

---

## DD-011 — Keep the Architecture Extensible for AI

**Decision:** The deterministic financial layer should not depend on the future AI implementation.

### Rationale

The AI technology may evolve during development.

The financial facts produced by reconciliation should remain usable regardless of the specific AI model or provider.

### Consequence

The architecture is designed so that future AI components consume structured reconciliation/anomaly results rather than directly manipulating raw financial records.

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

This development approach will continue throughout the remaining phases.
