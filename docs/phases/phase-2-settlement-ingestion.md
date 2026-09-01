# Phase 2 — Settlement Ingestion

**Focus:** Settlement representation, validation, and batch ingestion

---

## Objective

Phase 2 introduced the settlement side of the financial data model.

The objective was to make the system capable of receiving settlement records from external sources and persisting them reliably so they can later be reconciled against payment transactions.

A major focus of this phase was **safe ingestion of imperfect financial data**.

---

## What Was Built

### Settlement Data Model

A `Settlement` SQLAlchemy model was introduced.

The model contains:

* `id`
* `settlement_id`
* `payment_id`
* `settled_amount`
* `currency`
* `status`
* `settled_at`

`settlement_id` has a database-level unique constraint.

The settlement record references the same `payment_id` concept used by the transaction layer, allowing the two financial events to be associated during reconciliation.

---

## Settlement API

A direct settlement creation endpoint was implemented:

```text
POST /settlements
```

The endpoint validates and persists an individual settlement record.

Duplicate `settlement_id` values result in:

```text
HTTP 409 Conflict
```

---

## Settlement Validation

Pydantic validation is performed before settlement records reach the database.

The settlement schema validates:

* non-empty `settlement_id`
* non-empty `payment_id`
* positive settlement amount
* monetary precision
* three-character currency code
* valid status
* valid settlement timestamp

For example, negative settlement amounts are rejected.

Invalid timestamps are also rejected before persistence.

---

## CSV Ingestion

A CSV ingestion pipeline was introduced for batch settlement data.

The endpoint is:

```text
POST /ingestion/settlements
```

The ingestion flow is:

```text
CSV File
   ↓
CSV Parser
   ↓
Row Validation
   ↓
SettlementCreate
   ↓
Batch Ingestion
   ↓
PostgreSQL
```

This separates parsing and validation from database persistence.

---

## Row-Level Error Handling

The ingestion pipeline does not treat the entire file as a single all-or-nothing validation operation.

Each row can independently produce:

* a valid settlement
* a duplicate
* a validation failure

Validation failures are represented using:

```text
row
field
message
```

This allows operations teams to identify exactly which input record requires correction.

---

## Partial Success

The ingestion result reports:

```text
received
created
duplicates
failed
errors
```

For example, a mixed input file was successfully processed with:

```json
{
  "received": 3,
  "created": 1,
  "duplicates": 1,
  "failed": 1
}
```

The valid settlement was persisted even though another row failed validation.

This is important for operational ingestion because one malformed settlement record should not unnecessarily prevent unrelated valid records from being processed.

---

## Duplicate Handling

Settlement identifiers are protected at the database level through a unique constraint.

The ingestion service also handles the resulting integrity error and classifies the record as a duplicate rather than allowing the request to fail unexpectedly.

This provides both:

```text
Application-level handling
+
Database-level protection
```

---

## Database Migration

The settlement table was introduced through Alembic.

The schema was subsequently verified against PostgreSQL.

The transaction `paid_at` field was also introduced through migration during this development stage.

The current migration chain is tracked by Alembic.

---

## Verification

The implementation was verified through:

1. Pydantic model validation
2. CSV parser execution
3. Invalid-row testing
4. Duplicate settlement testing
5. Batch ingestion testing
6. FastAPI/OpenAPI route verification
7. API-level CSV ingestion
8. Direct PostgreSQL queries
9. Alembic schema verification

The database was verified to contain successfully ingested settlement records.

---

## Result

Phase 2 established the second major financial event in the system:

```text
Settlement Data
      ↓
CSV / API
      ↓
Validation
      ↓
Batch Processing
      ↓
Duplicate Detection
      ↓
PostgreSQL
```

The system can now reliably maintain both sides of the future reconciliation problem:

```text
Payment Transaction
        +
Settlement Record
```

---

## Why This Matters for the Final System

The core Razorpay-style settlement problem requires comparing what should have happened against what actually happened.

Phase 1 established:

```text
Expected / Payment Event
```

Phase 2 established:

```text
Actual / Settlement Event
```

The next phase can therefore move beyond ingestion and begin answering:

> **Did this payment settle correctly?**

This is the foundation of the reconciliation engine.
