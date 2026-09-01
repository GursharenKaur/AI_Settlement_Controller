# Phase 1 — Transaction Foundation

**Focus:** Transaction ingestion and persistence

---

## Objective

The first phase established the transaction foundation of the AI Settlement Controller.

The goal was to create a reliable representation of payment transactions that can later be reconciled against settlement records.

This phase intentionally focused on the **financial data foundation** rather than AI or anomaly detection.

---

## What Was Built

### Transaction Data Model

A `Transaction` model was introduced using SQLAlchemy.

The model currently contains:

* `id`
* `payment_id`
* `amount`
* `currency`
* `status`
* `paid_at`
* `created_at`

The `payment_id` field is unique and non-nullable.

Monetary values are stored using PostgreSQL `NUMERIC(12,2)` and represented as Python `Decimal` values.

---

## API

The following transaction endpoints were implemented:

### Create Transaction

```text
POST /transactions
```

Creates and persists a payment transaction.

### List Transactions

```text
GET /transactions
```

Supports pagination using `skip` and `limit`.

### Get Transaction

```text
GET /transactions/{transaction_id}
```

Retrieves an individual transaction by its database ID.

---

## Validation

Pydantic schemas are used at the API boundary.

The transaction creation schema validates:

* non-empty `payment_id`
* maximum identifier length
* positive transaction amount
* two-decimal monetary precision
* three-character currency code
* valid transaction status
* payment event timestamp

Invalid requests are rejected before being persisted.

---

## Database

PostgreSQL was selected as the persistence layer.

The transaction table is managed through Alembic migrations rather than manually maintained database changes.

The `paid_at` field was introduced through a dedicated migration so that the model can distinguish:

```text
created_at
    ↓
time the record entered the system

paid_at
    ↓
time the payment event occurred
```

This distinction is important for future settlement timing and delay analysis.

---

## Duplicate Protection

`payment_id` has a database-level unique constraint.

Attempts to create a transaction with an existing `payment_id` return:

```text
HTTP 409 Conflict
```

This prevents accidental duplicate payment records from entering the transaction dataset.

---

## Verification

The implementation was verified at multiple levels:

1. Python model imports
2. Pydantic validation
3. FastAPI route registration
4. PostgreSQL schema inspection
5. Alembic migration state
6. API request/response behavior
7. Database persistence

The final transaction schema was verified directly against PostgreSQL.

---

## Result

Phase 1 established the first reliable financial event in the system:

```text
Payment Transaction
        ↓
Validation
        ↓
FastAPI
        ↓
SQLAlchemy
        ↓
PostgreSQL
```

This provides the expected-payment side of the future reconciliation process.

---

## Why This Matters for the Final System

A settlement controller cannot determine whether money settled correctly without first knowing what payment event and amount were expected.

Phase 1 therefore establishes the foundation for the later question:

> **Was the amount associated with this payment eventually settled correctly?**

The transaction layer is intentionally deterministic and independent of future AI functionality.