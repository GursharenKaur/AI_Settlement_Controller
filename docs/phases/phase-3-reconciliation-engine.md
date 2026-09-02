# Phase 3 — Reconciliation Engine

## Overview

Phase 3 transforms the AI Settlement Controller from a system that can store transactions and settlements into a system that can **deterministically determine whether expected transaction money was settled correctly**.

The reconciliation layer compares a payment transaction with its corresponding settlement and produces a structured financial reconciliation result.

The design keeps financial correctness deterministic and independent of AI.

---

## Objective

For each `payment_id`, the reconciliation engine determines:

- Whether a settlement exists
- Whether transaction and settlement currencies are compatible
- Whether the settled amount matches the transaction amount
- The amount of financial drift
- The direction of the drift
- Whether the transaction/settlement state combination is invalid

The engine currently supports five reconciliation outcomes:

1. `MATCHED`
2. `AMOUNT_MISMATCH`
3. `MISSING_SETTLEMENT`
4. `CURRENCY_MISMATCH`
5. `INVALID_STATE`

---

## Architecture

The Phase 3 flow is:

```text
Transaction + Settlement
          |
          v
   Reconciliation API
          |
          v
   Reconciliation Service
          |
          v
 Deterministic Reconciliation Logic
          |
          v
   ReconciliationResult
```

The implementation deliberately follows:

```text
Route → Service → Database Query → Reconciliation Logic
```

FastAPI is responsible for HTTP concerns, while the reconciliation service contains the financial decision logic.

---

## Files Added / Changed

### New schema

```text
app/schemas/reconciliation.py
```

Defines:

- `ReconciliationStatus`
- `DriftDirection`
- `ReconciliationResult`

### New service

```text
app/services/reconciliation.py
```

Contains:

- `reconcile_transaction()`
- `reconcile_payment()`

### New API route

```text
app/core/api/routes/reconciliation.py
```

Provides:

```http
GET /reconciliation/{payment_id}
```

### Application registration

```text
app/main.py
```

Registers the reconciliation router.

---

# Reconciliation Schema

The reconciliation result contains:

```text
payment_id
status
expected_amount
actual_settled_amount
drift
drift_direction
transaction_currency
settlement_currency
```

### `ReconciliationStatus`

```python
class ReconciliationStatus(str, Enum):
    MATCHED = "MATCHED"
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH"
    MISSING_SETTLEMENT = "MISSING_SETTLEMENT"
    CURRENCY_MISMATCH = "CURRENCY_MISMATCH"
    INVALID_STATE = "INVALID_STATE"
```

### `DriftDirection`

```python
class DriftDirection(str, Enum):
    NONE = "NONE"
    UNDER_SETTLED = "UNDER_SETTLED"
    OVER_SETTLED = "OVER_SETTLED"
```

---

# Financial Reconciliation Rules

## 1. MATCHED

A transaction is `MATCHED` when:

```text
Transaction amount == Settlement amount
Transaction currency == Settlement currency
```

Example:

```text
Transaction: ₹12,500 INR
Settlement:  ₹12,500 INR
```

Result:

```json
{
  "status": "MATCHED",
  "expected_amount": "12500.00",
  "actual_settled_amount": "12500.00",
  "drift": "0.00",
  "drift_direction": "NONE"
}
```

---

## 2. MISSING_SETTLEMENT

A transaction is `MISSING_SETTLEMENT` when no settlement exists for the `payment_id`.

Example:

```text
Transaction: ₹12,500 INR
Settlement:  None
```

The entire expected amount is treated as under-settled:

```json
{
  "status": "MISSING_SETTLEMENT",
  "expected_amount": "12500.00",
  "actual_settled_amount": null,
  "drift": "12500.00",
  "drift_direction": "UNDER_SETTLED"
}
```

---

## 3. AMOUNT_MISMATCH — UNDER SETTLED

If currencies match but:

```text
Settlement amount < Transaction amount
```

the result is:

```text
AMOUNT_MISMATCH
UNDER_SETTLED
```

Example:

```text
Expected: ₹10,000
Actual:   ₹9,800
Drift:    ₹200
```

Result:

```json
{
  "status": "AMOUNT_MISMATCH",
  "expected_amount": "10000.00",
  "actual_settled_amount": "9800.00",
  "drift": "200.00",
  "drift_direction": "UNDER_SETTLED"
}
```

The drift is calculated as:

```text
expected_amount - actual_settled_amount
```

---

## 4. AMOUNT_MISMATCH — OVER SETTLED

If currencies match but:

```text
Settlement amount > Transaction amount
```

the result is:

```text
AMOUNT_MISMATCH
OVER_SETTLED
```

Example:

```text
Expected: ₹10,000
Actual:   ₹10,300
Drift:    ₹300
```

Result:

```json
{
  "status": "AMOUNT_MISMATCH",
  "expected_amount": "10000.00",
  "actual_settled_amount": "10300.00",
  "drift": "300.00",
  "drift_direction": "OVER_SETTLED"
}
```

The drift is calculated as:

```text
actual_settled_amount - expected_amount
```

---

## 5. CURRENCY_MISMATCH

If the transaction and settlement currencies differ:

```text
Transaction currency != Settlement currency
```

the result is:

```text
CURRENCY_MISMATCH
```

No monetary drift is calculated.

This is intentional because comparing amounts such as:

```text
₹10,000 INR
$100 USD
```

without an explicit exchange-rate conversion would be financially incorrect.

Example:

```json
{
  "status": "CURRENCY_MISMATCH",
  "expected_amount": "10000.00",
  "actual_settled_amount": "100.00",
  "drift": null,
  "drift_direction": "NONE",
  "transaction_currency": "INR",
  "settlement_currency": "USD"
}
```

---

## 6. INVALID_STATE

A settlement can have a financially inconsistent state even when the amounts match.

For the current Phase 3 scope, the following combination is treated as invalid:

```text
Transaction status = created
Settlement status  = settled
```

This represents a payment that has not reached a successful payment state while already being marked as settled.

Result:

```json
{
  "status": "INVALID_STATE",
  "expected_amount": "5000.00",
  "actual_settled_amount": "5000.00",
  "drift": null,
  "drift_direction": "NONE",
  "transaction_currency": "INR",
  "settlement_currency": "INR"
}
```

The state comparison is case-insensitive using `.lower()` because existing database data contains both uppercase and lowercase settlement/payment status values.

---

# API

## Endpoint

```http
GET /reconciliation/{payment_id}
```

Example:

```http
GET /reconciliation/pay_recon_mismatch_001
```

### Successful response

```json
{
  "payment_id": "pay_recon_mismatch_001",
  "status": "AMOUNT_MISMATCH",
  "expected_amount": "10000.00",
  "actual_settled_amount": "9800.00",
  "drift": "200.00",
  "drift_direction": "UNDER_SETTLED",
  "transaction_currency": "INR",
  "settlement_currency": "INR"
}
```

### Transaction not found

If the requested `payment_id` does not exist, the API returns:

```http
404 Not Found
```

with:

```json
{
  "detail": "Transaction with payment_id '...' not found."
}
```

---

# Deterministic Logic Order

The reconciliation service evaluates conditions in this order:

```text
1. Find transaction
       |
       +-- Not found → API returns 404
       |
       v
2. Find settlement
       |
       +-- None → MISSING_SETTLEMENT
       |
       v
3. Check invalid state
       |
       +-- Invalid combination → INVALID_STATE
       |
       v
4. Check currency
       |
       +-- Different → CURRENCY_MISMATCH
       |
       v
5. Compare amounts
       |
       +-- Equal → MATCHED
       |
       +-- Lower → AMOUNT_MISMATCH / UNDER_SETTLED
       |
       +-- Higher → AMOUNT_MISMATCH / OVER_SETTLED
```

---

# Financial Precision

All monetary calculations use Python's `Decimal` type.

The system does **not** use floating-point arithmetic for reconciliation.

This is important for financial systems because monetary calculations must avoid binary floating-point precision issues.

Database monetary fields use:

```text
Numeric(12, 2)
```

The reconciliation schema also uses:

```python
Decimal
```

---

# Separation of Concerns

The reconciliation implementation intentionally separates responsibilities.

### API route

Responsible for:

- Receiving the HTTP request
- Obtaining the database session
- Calling the service
- Returning HTTP errors
- Returning the reconciliation result

### Reconciliation service

Responsible for:

- Loading transaction/settlement data
- Applying deterministic financial rules
- Calculating drift
- Determining reconciliation status

### Pydantic schema

Responsible for:

- Structuring the reconciliation result
- Validating the result shape
- Providing API serialization

This prevents financial logic from being embedded directly inside FastAPI route handlers.

---

# Verification Performed

All major Phase 3 scenarios were verified through the running API.

## MATCHED

```text
Expected: ₹12,500
Actual:   ₹12,500
Result:   MATCHED
Drift:    ₹0
```

## MISSING_SETTLEMENT

```text
Expected: ₹12,500
Actual:   None
Result:   MISSING_SETTLEMENT
Drift:    ₹12,500 UNDER_SETTLED
```

## UNDER_SETTLED

```text
Expected: ₹10,000
Actual:   ₹9,800
Result:   AMOUNT_MISMATCH
Direction: UNDER_SETTLED
Drift:    ₹200
```

## OVER_SETTLED

```text
Expected: ₹10,000
Actual:   ₹10,300
Result:   AMOUNT_MISMATCH
Direction: OVER_SETTLED
Drift:    ₹300
```

## CURRENCY_MISMATCH

```text
Expected: ₹10,000 INR
Actual:   $100 USD
Result:   CURRENCY_MISMATCH
Drift:    None
```

## INVALID_STATE

```text
Transaction: created
Settlement:  SETTLED
Result:      INVALID_STATE
```

---

# Current Design Limitation

`Settlement.payment_id` is currently not unique.

A payment can therefore have multiple settlement records.

The current reconciliation lookup uses the first settlement:

```python
.order_by(Settlement.id)
.first()
```

This is intentionally a minimal Phase 3 implementation.

Real payment systems can support:

- Partial settlements
- Multiple settlement events
- Settlement retries
- Multiple settlement batches

Therefore, aggregation and multi-settlement semantics should be revisited later as a production-style enhancement.

This was deliberately not expanded during Phase 3 so that the project could continue through the planned core phases without premature over-engineering.

---

# Why Reconciliation Is Not Persisted Yet

A separate reconciliation table has not been introduced.

The reconciliation result is currently derived from:

```text
Transaction
+
Settlement
```

This means the result automatically reflects newly ingested settlement information.

For example:

```text
Before settlement:
Transaction → MISSING_SETTLEMENT

Settlement arrives

After settlement:
Transaction + Settlement → MATCHED
```

Persisting reconciliation results at this stage could introduce stale derived records and synchronization concerns.

A persisted reconciliation/audit model can be considered later if required by the final architecture.

---

# Phase 3 Completion Criteria

Phase 3 is considered complete because:

- [x] Reconciliation schema implemented
- [x] Deterministic reconciliation service implemented
- [x] Database lookup integrated
- [x] Reconciliation API implemented
- [x] API router registered
- [x] Decimal-based monetary calculations
- [x] Missing settlement detection
- [x] Exact settlement matching
- [x] Under-settlement detection
- [x] Over-settlement detection
- [x] Currency mismatch detection
- [x] Invalid state detection
- [x] End-to-end API verification completed

---

# Relationship to the Overall AI Settlement Controller

Phase 3 establishes the deterministic financial foundation for the larger system:

```text
Payment / Transaction Data
            +
Settlement Data
            ↓
    Reconciliation Engine
            ↓
   Drift / Anomaly Detection
            ↓
         AI Analysis
            ↓
 Explanation + Risk + Impact
            ↓
 Recommended / Controlled Action
            ↓
 Auditability + Financial Controls
```

The important architectural principle is:

> **AI should interpret and prioritize financial problems after deterministic reconciliation has established what actually happened.**

Phase 3 therefore provides the financial truth layer that future AI components can safely consume.
