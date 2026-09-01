# Architecture — AI Settlement Controller

## 1. System Overview

The AI Settlement Controller is being developed as a payment-settlement control system for a Razorpay-like environment.

Its purpose is to detect and explain discrepancies between payment transactions and settlement outcomes.

The system is being developed incrementally, with deterministic financial processing forming the foundation for later anomaly detection and AI-assisted analysis.

---

## 2. Current Architecture

The current system consists of:

```text
                    ┌─────────────────────┐
                    │      FastAPI        │
                    │       API Layer     │
                    └──────────┬──────────┘
                               │
              ┌────────────────┴────────────────┐
              │                                 │
              ▼                                 ▼
     Transaction APIs                    Settlement APIs
              │                                 │
              │                         CSV Ingestion
              │                                 │
              └──────────────┬──────────────────┘
                             ▼
                    ┌─────────────────────┐
                    │      Services       │
                    │                     │
                    │ Settlement Parsing  │
                    │ Batch Ingestion     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │     SQLAlchemy      │
                    │       Models        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │     PostgreSQL      │
                    │                     │
                    │  transactions       │
                    │  settlements        │
                    └─────────────────────┘
```

---

## 3. Major Components

### API Layer

FastAPI exposes the application's HTTP interface.

Current endpoints include:

```text
GET  /health

POST /transactions
GET  /transactions
GET  /transactions/{transaction_id}

POST /settlements

POST /ingestion/settlements
```

The API layer is responsible for request handling and validation boundaries.

---

### Schema Layer

Pydantic schemas define the structure and validation rules for incoming and outgoing API data.

Important properties include:

* positive monetary values
* bounded identifiers
* currency validation
* timestamp validation
* structured ingestion errors

The schema layer prevents malformed financial data from reaching core processing unnecessarily.

---

### Service Layer

Business processing is kept outside the API routes where possible.

Current services include:

```text
settlement_csv.py
settlement_ingestion.py
settlement_batch.py
```

These services handle:

* CSV parsing
* row validation
* settlement creation
* duplicate handling
* batch ingestion

This separation will allow the reconciliation engine to be introduced without putting financial logic directly into FastAPI routes.

---

### Model Layer

SQLAlchemy models represent persistent financial entities.

Current entities:

```text
Transaction
Settlement
```

They represent two different financial events and are intentionally stored separately.

---

### Database Layer

PostgreSQL is the system's persistence layer.

The database currently contains:

```text
transactions
settlements
```

Financial amounts use fixed-precision numeric storage rather than floating-point types.

---

### Migration Layer

Alembic manages database schema evolution.

Schema changes are introduced through migration files and verified against the running PostgreSQL database.

This prevents the application model and database schema from silently diverging.

---

## 4. Financial Data Flow

The intended financial flow begins with two independent event streams:

```text
Payment Event
     │
     ▼
Transaction
     │
     │
     │              Settlement Event
     │                    │
     │                    ▼
     │               Settlement
     │                    │
     └──────────┬─────────┘
                ▼
        Reconciliation Engine
```

The common `payment_id` provides the initial association between the payment and settlement events.

---

## 5. Reconciliation Architecture

The next architectural component is the deterministic reconciliation engine.

The planned flow is:

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
     ↓
Drift / Anomaly Layer
```

The reconciliation logic will remain separate from the HTTP layer.

This is intentional because financial rules should be independently testable and reusable by future APIs, scheduled jobs, or batch processes.

---

## 6. Future Architecture

The final system is expected to evolve toward:

```text
                 Payment Events
                       │
                       ▼
                Transaction Store
                       │
                       │
Settlement Files ──────┤
                       ▼
              Reconciliation Engine
                       │
                       ▼
               Drift Detection
                       │
                       ▼
              Anomaly Detection
                       │
                       ▼
                AI Analysis
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
      Explanation    Risk       Root Cause
                       │
                       ▼
                Recommended Action
                       │
                       ▼
             Financial Controls
                       │
                       ▼
                  Audit Trail
```

The exact design of the later AI and control layers will be determined as those phases are implemented.

---

## 7. Architectural Principles

### Deterministic Financial Core

Financial correctness must not depend on probabilistic AI output.

The reconciliation engine will establish the factual financial state first.

AI will operate on top of those deterministic results.

---

### Separation of Concerns

The architecture separates:

```text
API
Schema / Validation
Business Services
Persistence Models
Database
```

This makes the system easier to test and extend.

---

### Financial Precision

Monetary calculations use `Decimal` and PostgreSQL fixed-precision numeric fields.

Floating-point arithmetic is avoided for financial values.

---

### Incremental Evolution

The architecture is intentionally being developed in phases.

Each phase adds a meaningful capability without prematurely implementing the entire final system.
