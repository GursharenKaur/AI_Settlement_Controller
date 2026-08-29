# AI Settlement Controller

> AI Settlement Controller is a finance-operations control system that continuously compares expected and observed settlement behavior, detects financial drift, investigates its root cause using deterministic evidence tools and AI reasoning, calculates financial exposure, and routes each case toward an appropriate controlled resolution.

## Razorpay Buildathon 2026

This project is being built for **Track 04 — AI Finance Controller** of the Razorpay Buildathon 2026.

The challenge is to build an agent that closes a finance-operations loop across synthetic financial data while demonstrating throughput, measured accuracy, and honest exception handling.

---

## Problem

Finance teams often discover settlement problems as **unexplained discrepancies**:

- Money settled late
- Money never settled
- Settlement amount differs from expected amount
- Fee suddenly changes
- Duplicate settlement appears
- Refund is not reflected correctly
- Partial settlement occurs
- Payment behavior changes unexpectedly

The difficult part is not merely identifying that two numbers differ.

The difficult part is answering:

> **What changed? Why did it change? How much money is affected? Is the explanation supported by evidence? And should the finance team resolve it automatically or review it?**

Current reconciliation workflows often require manual investigation across multiple financial sources.

The AI Settlement Controller closes this investigation loop by combining deterministic financial controls with AI-assisted evidence analysis.

---

## Solution

The AI Finance Controller continuously analyzes synthetic financial data to:

1. Establish expected financial behavior
2. Detect financial drift and anomalies
3. Identify affected transactions
4. Investigate possible root causes
5. Gather supporting evidence
6. Quantify financial impact
7. Recommend bounded actions
8. Escalate uncertain cases for human review
9. Maintain an auditable decision trail

### Core workflow

```text
Observe
   ↓
Detect Drift
   ↓
Investigate
   ↓
Explain
   ↓
Quantify Impact
   ↓
Recommend Action
   ↓
Human Approval
   ↓
Audit
