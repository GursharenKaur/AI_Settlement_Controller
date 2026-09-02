# Phase 4 — Exception Intelligence, Financial Impact, AI Analysis & Controller Decision

## 1. Overview

Phase 4 transforms the deterministic reconciliation results from Phase 3 into an operational exception-management layer for the **AI Settlement Controller**.

The phase adds:

- Exception classification
- Severity assessment
- Financial-impact calculation
- Deterministic priority scoring
- Portfolio-level exception summary
- Exception lifecycle tracking
- Trusted AI context generation
- Individual exception AI analysis
- Portfolio AI analysis
- Controller decision recommendations
- Human-review controls

The design keeps **financial correctness deterministic** and uses AI primarily for explanation, prioritization context, and practical recommendations.

The core principle is:

> **AI should explain and assist trusted financial intelligence, not invent or directly execute financial outcomes.**

---

## 2. Phase 4 Architecture

The Phase 4 flow is:

```text
Transactions + Settlements
          ↓
Reconciliation Engine
          ↓
Exception Intelligence
          ↓
Financial Impact + Priority
          ↓
Exception Lifecycle
          ↓
Portfolio Summary
          ↓
Trusted AI Context
          ↓
Gemini Analysis
          ↓
Controller Decision
          ↓
Human Review / Controlled Action
```

This extends the Phase 3 reconciliation foundation without replacing it.

---

## 3. Exception Intelligence

### 3.1 Exception Categories

Implemented categories:

| Category | Meaning |
|---|---|
| `NONE` | No exception |
| `MISSING_SETTLEMENT` | No corresponding settlement exists |
| `UNDER_SETTLEMENT` | Settlement amount is lower than expected |
| `OVER_SETTLEMENT` | Settlement amount is higher than expected |
| `CURRENCY_MISMATCH` | Transaction and settlement currencies differ |
| `INVALID_STATE` | Transaction and settlement states form an invalid operational combination |

### 3.2 Severity

Implemented severity levels:

- `NONE`
- `LOW`
- `MEDIUM`
- `HIGH`

Current deterministic mapping:

| Reconciliation Result | Severity |
|---|---|
| `MATCHED` | `NONE` |
| `MISSING_SETTLEMENT` | `HIGH` |
| `CURRENCY_MISMATCH` | `HIGH` |
| `INVALID_STATE` | `HIGH` |
| `UNDER_SETTLEMENT` | `MEDIUM` |
| `OVER_SETTLEMENT` | `HIGH` |

### 3.3 Financial Impact

Financial impact is derived from trusted reconciliation output.

Examples:

- Missing settlement → expected transaction amount
- Under-settlement → amount difference
- Over-settlement → amount difference
- Currency mismatch → `None`
- Invalid state → `None`

The system deliberately does **not** invent financial impact where a safe monetary value cannot be established.

---

## 4. Deterministic Priority Scoring

Priority scoring is deterministic and occurs before AI analysis.

Base priority:

```text
NONE   = 0
LOW    = 25
MEDIUM = 50
HIGH   = 75
```

Financial-impact bonus:

```text
Impact >= 10,000 → +25
Impact >= 1,000  → +10
Otherwise        → +0
```

The final score is capped at `100`.

This allows a high-value exception to receive greater operational priority while keeping the calculation transparent and reproducible.

Example:

```text
MISSING_SETTLEMENT
Severity = HIGH → 75
Impact = 15,000 → +25
Final priority = 100
```

---

## 5. Exception Overview

The exception overview processes transactions through the established reconciliation engine and then converts non-matching results into exception assessments.

The overview:

1. Loads transactions.
2. Finds the corresponding settlement.
3. Runs deterministic reconciliation.
4. Builds an exception assessment.
5. Attaches lifecycle status when a lifecycle record exists.
6. Filters out non-exceptions.
7. Sorts exceptions by priority score.

The endpoint is:

```text
GET /exceptions
```

The endpoint is intentionally read-oriented and does not automatically create lifecycle records.

A missing lifecycle record means:

```text
lifecycle_status = null
```

It is **not** automatically interpreted as `OPEN`.

---

## 6. Portfolio Exception Summary

The endpoint:

```text
GET /exceptions/summary
```

provides deterministic portfolio-level metrics.

Implemented fields include:

- Total exceptions
- Open exception count
- Acknowledged exception count
- Resolved exception count
- Total transactions
- Exception rate
- Total known financial impact
- Financial impact rate
- Financial impact by category
- Category counts
- Severity counts
- High-priority count
- Highest priority score
- Dominant exception category
- Overall risk band
- Financial risk level

### Verified portfolio state

The current test dataset produced:

```text
Total transactions              = 7
Total exceptions                = 6
Open exceptions                 = 1
Acknowledged exceptions         = 0
Resolved exceptions             = 2
Exception rate                  = 85.71428571428571428571428571%
Known financial impact          = 15,500.00
Financial impact rate           = 20.66666666666666666666666667%
High-priority exceptions        = 5
Highest priority score          = 100
Dominant category               = INVALID_STATE
Risk band                      = CRITICAL
Financial risk level            = HIGH
```

Known financial impact by category:

```text
MISSING_SETTLEMENT = 15,000.00
OVER_SETTLEMENT     =    300.00
UNDER_SETTLEMENT    =    200.00
```

Important distinction:

- `INVALID_STATE` is dominant by **exception count**.
- `MISSING_SETTLEMENT` is the dominant **known financial exposure**.

This distinction is important for operational prioritization.

---

## 7. Exception Lifecycle

Phase 4 introduces persistent exception lifecycle tracking.

### 7.1 Lifecycle States

```text
OPEN
ACKNOWLEDGED
RESOLVED
```

A lifecycle record contains:

- `payment_id`
- `status`
- `created_at`
- `updated_at`

The payment ID is unique within the lifecycle table.

### 7.2 Lifecycle Transitions

Supported transitions:

```text
OPEN
  ↓
ACKNOWLEDGED
  ↓
RESOLVED
```

The implementation is intentionally conservative.

Examples:

- `ACKNOWLEDGE` on `OPEN` → moves to `ACKNOWLEDGED`
- `RESOLVE` on `ACKNOWLEDGED` → moves to `RESOLVED`
- `ACKNOWLEDGE` on `RESOLVED` → remains `RESOLVED`
- `RESOLVE` on `RESOLVED` → remains `RESOLVED`

Resolved exceptions therefore cannot accidentally be reopened through the implemented operations.

### 7.3 Lifecycle API

```text
POST /exceptions/{payment_id}/acknowledge
POST /exceptions/{payment_id}/resolve
GET  /exceptions/{payment_id}/lifecycle
```

Lifecycle persistence was verified with existing test exceptions.

---

## 8. AI Context Layer

AI does not directly receive arbitrary database records.

Instead, deterministic backend logic builds trusted context objects.

### 8.1 Individual AI Context

The individual context contains:

- Payment ID
- Exception category
- Severity
- Financial impact
- Priority score
- Overall risk band
- Overall financial risk level

This separates:

```text
Individual exception risk
```

from:

```text
Portfolio-level risk
```

For example, an individual exception can be `MEDIUM` severity while the overall portfolio can simultaneously be `CRITICAL`.

### 8.2 Portfolio AI Context

Portfolio context contains the deterministic summary:

- Transaction count
- Exception count
- Lifecycle counts
- Exception rate
- Known financial impact
- Financial impact rate
- Impact by category
- Category counts
- Severity counts
- Priority metrics
- Risk metrics

This prevents the LLM from having to independently calculate the core financial metrics.

---

## 9. Gemini Integration

The project uses Google's official `google-genai` SDK.

Configured model:

```text
gemini-2.5-flash
```

The API key is loaded from environment configuration rather than being hardcoded.

Configuration uses:

```text
GEMINI_API_KEY
```

The Gemini client is initialized through the backend configuration layer.

The dependency is recorded in the project's Python requirements.

### Important design decision

Gemini is **not the source of truth for financial calculations**.

The deterministic backend establishes:

- amounts
- differences
- exception categories
- priority
- lifecycle
- portfolio metrics

Gemini receives those trusted values and generates explanatory and operational output.

---

## 10. Individual AI Analysis

Endpoint:

```text
GET /exceptions/{payment_id}/ai-analysis
```

The individual AI response contains:

- Explanation
- Financial-impact explanation
- Risk explanation
- Recommended action

The AI instructions explicitly prohibit:

- Inventing financial amounts
- Reinterpreting deterministic financial impact
- Pretending an unquantified impact is known
- Confusing individual risk with portfolio risk

### Verified example

For:

```text
pay_recon_mismatch_001
```

the deterministic context was:

```text
Category        = UNDER_SETTLEMENT
Severity        = MEDIUM
Financial impact = 200.00
Priority         = 50
```

The generated analysis preserved the known `200.00` financial impact and recommended operational investigation.

### AI limitation observed

Gemini may sometimes use descriptive language such as "pending" or "unconfirmed" when explaining an under-settlement. Such wording is not itself a deterministic database fact.

Therefore:

> AI-generated explanations are advisory and must remain subordinate to the trusted backend assessment.

---

## 11. Portfolio AI Analysis

Endpoint:

```text
GET /exceptions/ai-analysis
```

The response contains:

- Executive summary
- Key risk drivers
- Financial impact explanation
- Priority assessment
- Recommended actions
- Recommended priority
- Focus category
- Recommendation reason
- Human-review requirement

### Verified behavior

The AI correctly recognized:

```text
6 exceptions across 7 transactions
15,500.00 known financial impact
15,000.00 from missing settlements
CRITICAL overall risk
HIGH financial risk
5 HIGH-severity exceptions
1 currently open exception
```

It also correctly distinguished:

```text
INVALID_STATE
```

as the dominant category by count from:

```text
MISSING_SETTLEMENT
```

as the primary known financial exposure.

The portfolio AI selected:

```text
recommended_priority = CRITICAL
focus_category = MISSING_SETTLEMENT
human_review_required = True
```

---

## 12. Controller Decision Layer

The Controller Decision layer converts a trusted exception assessment into a deterministic operational recommendation.

It does **not** execute a financial action.

### 12.1 Supported Controller Actions

```text
INVESTIGATE_MISSING_SETTLEMENT
REVIEW_SETTLEMENT_AMOUNT
REVIEW_CURRENCY_MISMATCH
INVESTIGATE_INVALID_STATE
NO_FURTHER_ACTION
```

### 12.2 Decision Mapping

| Exception | Controller Action |
|---|---|
| Missing settlement | `INVESTIGATE_MISSING_SETTLEMENT` |
| Under-settlement | `REVIEW_SETTLEMENT_AMOUNT` |
| Over-settlement | `REVIEW_SETTLEMENT_AMOUNT` |
| Currency mismatch | `REVIEW_CURRENCY_MISMATCH` |
| Invalid state | `INVESTIGATE_INVALID_STATE` |
| Resolved exception | `NO_FURTHER_ACTION` |
| No exception | `NO_FURTHER_ACTION` |

### 12.3 Human Review

For unresolved financial exceptions, the controller returns:

```text
human_review_required = true
```

For resolved exceptions:

```text
human_review_required = false
```

This explicitly establishes a human-in-the-loop boundary.

---

## 13. Controller Decision API

Endpoint:

```text
GET /exceptions/{payment_id}/decision
```

The route performs:

```text
Payment ID
   ↓
Reconciliation
   ↓
Exception Assessment
   ↓
Lifecycle Lookup
   ↓
Controller Decision
```

### Verified scenarios

#### Under-settlement

```text
Payment: pay_recon_mismatch_001
Category: UNDER_SETTLEMENT
Lifecycle: OPEN
Impact: 200.00
Priority: 50
Action: REVIEW_SETTLEMENT_AMOUNT
Human review: True
```

#### Resolved over-settlement

```text
Payment: pay_recon_over_001
Category: OVER_SETTLEMENT
Lifecycle: RESOLVED
Impact: 300.00
Priority: 75
Action: NO_FURTHER_ACTION
Human review: False
```

#### Missing settlement

```text
Payment: 2
Category: MISSING_SETTLEMENT
Impact: 15,000.00
Priority: 100
Action: INVESTIGATE_MISSING_SETTLEMENT
Human review: True
```

#### Resolved currency mismatch

```text
Payment: pay_recon_currency_001
Category: CURRENCY_MISMATCH
Lifecycle: RESOLVED
Impact: None
Priority: 75
Action: NO_FURTHER_ACTION
Human review: False
```

#### Invalid state

```text
Payment: pay_recon_invalid_001
Category: INVALID_STATE
Impact: None
Priority: 75
Action: INVESTIGATE_INVALID_STATE
Human review: True
```

#### Unknown payment

An unknown payment returns:

```text
HTTP 404
```

with:

```text
Payment payment_does_not_exist not found
```

---

## 14. Financial Control Principles

Phase 4 follows several important financial-system principles.

### 14.1 Deterministic financial truth

The backend calculates financial impact and priority.

The LLM does not calculate the source-of-truth financial values.

### 14.2 No fabricated monetary impact

When a currency mismatch or invalid state cannot safely be expressed as a monetary difference, the system uses:

```text
financial_impact = None
```

rather than inventing a number.

### 14.3 Human-in-the-loop

Controller decisions recommend operational actions but do not automatically:

- move money
- modify settlements
- refund customers
- alter payment records
- execute financial adjustments

### 14.4 Resolved exceptions remain closed

A resolved exception produces:

```text
NO_FURTHER_ACTION
```

and:

```text
human_review_required = false
```

### 14.5 Lifecycle absence is not OPEN

If an exception has no lifecycle record:

```text
lifecycle_status = None
```

The system does not infer that it is `OPEN`.

### 14.6 AI is advisory

AI output can explain and recommend, but the trusted backend remains the source of financial truth.

---

## 15. Verification Summary

Phase 4 was verified through API and service-level testing.

### Deterministic intelligence

- Exception classification verified
- Severity verified
- Financial impact verified
- Priority scoring verified
- Portfolio aggregation verified
- Risk band verified
- Financial risk level verified

### Lifecycle

- Open state verified
- Acknowledgement verified
- Resolution verified
- Resolved no-op behavior verified
- Lifecycle persistence verified

### AI

- Individual AI context verified
- Individual AI analysis verified
- Portfolio AI context verified
- Portfolio AI analysis verified
- Financial grounding verified
- Unknown-payment rejection verified

### Controller

- Missing settlement verified
- Under-settlement verified
- Over-settlement verified
- Currency mismatch verified
- Invalid state verified
- Resolved/no-action behavior verified
- Human-review behavior verified
- Unknown-payment 404 verified

---

## 16. Known Limitations

The following are intentional or currently known limitations.

### Settlement selection

The existing reconciliation implementation selects the first settlement for a payment when multiple settlement records exist.

This was retained from Phase 3 and was not redesigned during Phase 4.

### AI wording

LLM-generated explanations may occasionally contain descriptive assumptions that are not explicitly present in deterministic data.

The system therefore treats AI output as advisory rather than authoritative.

### Gemini SDK warning

The Google GenAI SDK may emit an automatic function-calling warning during `generate_content()` calls.

The current application does not intentionally use application-level tool/function calling. The warning does not prevent the current AI calls from succeeding.

Cleanup of this warning can be considered separately after core functionality is complete.

---

## 17. Phase 4 Completion Status

**PHASE 4 — COMPLETE**

The AI Settlement Controller now moves beyond basic reconciliation into an operational intelligence layer:

```text
Raw Payment / Settlement Data
            ↓
Reconciliation
            ↓
Exception Intelligence
            ↓
Financial Impact
            ↓
Priority
            ↓
Lifecycle
            ↓
Portfolio Risk
            ↓
AI Explanation
            ↓
Controller Recommendation
            ↓
Human Review
```

The key architectural principle established in this phase is:

> **Financial truth remains deterministic; AI adds explanation and operational intelligence; consequential actions remain controlled by explicit human-review boundaries.**

This provides the foundation for the next phase of the AI Settlement Controller without turning the system into an unsafe autonomous financial agent.
