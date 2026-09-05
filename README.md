# AI Settlement Controller

### AI-assisted settlement intelligence and operational control

AI Settlement Controller is a payment settlement control system that detects settlement discrepancies, quantifies financial exposure, prioritizes operational risk, provides AI-assisted investigation, and manages controlled remediation with human oversight.

> **AI explains. Rules decide. Controls execute. Humans resolve. Audit remembers.**

---

## What It Does

The system takes payment transactions and settlement records and turns settlement discrepancies into actionable operational intelligence.

```text
Transactions + Settlements
            ↓
     Reconciliation
            ↓
   Exception Intelligence
            ↓
 Financial Impact + Priority
            ↓
 Historical Intelligence
            ↓
   AI-Assisted Investigation
            ↓
 Deterministic Controller
            ↓
 Controlled Remediation
            ↓
    Human Resolution
            ↓
       Audit Trail
```

---

## Key Features

- **Transaction & Settlement Ingestion** — REST APIs and CSV batch ingestion with validation and duplicate detection.
- **Deterministic Reconciliation** — Detects matched settlements, missing settlements, amount mismatches, currency mismatches, and invalid states.
- **Exception Intelligence** — Classifies missing, under-settled, over-settled, currency mismatch, and invalid-state exceptions.
- **Financial Impact & Risk Prioritization** — Calculates known financial exposure and deterministic priority scores.
- **Historical Intelligence** — Identifies recurrence patterns, related historical exceptions, and settlement timing patterns.
- **AI-Assisted Investigation** — Uses Google Gemini to explain exceptions and provide investigation context from trusted application-generated evidence.
- **Deterministic Controller** — Maps each exception to a predefined operational action. AI recommendations cannot authorize actions.
- **Controlled Remediation** — Validates bounded remediation actions before simulated execution.
- **Human Resolution & Auditability** — Uses an explicit `OPEN → ACKNOWLEDGED → RESOLVED` lifecycle with recorded resolution details and operational actions.

---

## Why It's Different

### AI is not the decision-maker

The system deliberately separates **AI reasoning from financial control**.

| AI Can | AI Cannot |
|---|---|
| Explain an exception | Reconcile transactions |
| Summarize evidence | Calculate authoritative financial impact |
| Provide investigation context | Change priority or governance |
| Suggest operational focus | Authorize remediation |
| Identify possible patterns | Resolve exceptions |

Financial truth, classification, priority, governance, and action authorization remain **deterministic and auditable**.

The core settlement-control workflow remains useful even when the AI service is unavailable.

---

## Architecture Highlight

```text
┌──────────────────────────────────────────────┐
│              Input & Ingestion               │
│       Transactions • Settlements • CSV       │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│         Deterministic Control Plane          │
│ Reconciliation • Exceptions • Impact • Risk │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────┴───────────────────────┐
│                                              │
│  Historical Intelligence       AI Advisory   │
│  Recurrence • Timing           Gemini        │
│  Historical Context            Investigation │
│                                              │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│           Deterministic Controller           │
│          Action Mapping & Validation         │
└──────────────────────┬───────────────────────┘
                       ↓
┌──────────────────────────────────────────────┐
│        Controlled Remediation + Human        │
│              Resolution & Audit              │
└──────────────────────────────────────────────┘
```

### Technology

**Backend:** FastAPI · Python · PostgreSQL · SQLAlchemy · Alembic · Pydantic  
**AI:** Google Gemini · `google-genai`  
**Frontend:** React · TypeScript · Vite  
**Deployment:** Render · Vercel · Neon PostgreSQL

---

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd AI_Settlement_Controller
```

### 2. Backend

```bash
cd backend
python -m venv .venv
```

**Windows:**

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file using `.env.example`:

```env
DATABASE_URL=your_postgresql_url
GEMINI_API_KEY=your_gemini_api_key
CORS_ORIGINS=http://localhost:5173
```

Run migrations:

```bash
alembic upgrade head
```

Start the API:

```bash
uvicorn app.main:app --reload
```

### 3. Frontend

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

---

## Production Demo

**Frontend:** https://ai-settlement-controller-ui.vercel.app/

**Backend:** https://ai-settlement-controller.onrender.com/

The deployed demonstration environment contains multiple settlement failure scenarios, including missing settlements, under-settlements, over-settlements, currency mismatches, and invalid states.

---

## Documentation

For deeper engineering details:

- [`docs/architecture.md`](docs/architecture.md)
- [`docs/design-decisions.md`](docs/design-decisions.md)

---

## Scope

This project demonstrates a production-oriented settlement control architecture.

Controlled remediation is **simulated** and does not move or correct real financial funds. AI remains advisory, while deterministic business logic and human resolution retain control over financial operations.

---

### Core Principle

> **AI explains. Rules decide. Controls execute. Humans resolve. Audit remembers.**
