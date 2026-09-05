import "./App.css";

import { useEffect, useState } from "react";

import {
  getControlSummary,
  getExceptionDetail,
  getRiskQueue,
  type OperationalControlDetail,
  type OperationalControlSummary,
  type OperationalRiskItem,
} from "./api/client";

function StatusBadge({
  children,
  variant = "neutral",
}: {
  children: React.ReactNode;
  variant?: "critical" | "warning" | "success" | "neutral";
}) {
  return <span className={`status-badge ${variant}`}>{children}</span>;
}

function formatMoney(value: string | null): string {
  if (value === null) {
    return "—";
  }

  return `₹${Number(value).toLocaleString("en-IN", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  })}`;
}

function formatLabel(value: string | null): string {
  if (!value) {
    return "—";
  }

  return value.replaceAll("_", " ");
}

function severityVariant(
  severity: OperationalRiskItem["severity"],
): "critical" | "warning" | "success" | "neutral" {
  if (severity === "HIGH") {
    return "critical";
  }

  if (severity === "MEDIUM") {
    return "warning";
  }

  if (severity === "LOW") {
    return "success";
  }

  return "neutral";
}

function App() {
  const [summary, setSummary] =
    useState<OperationalControlSummary | null>(null);

  const [riskQueue, setRiskQueue] = useState<OperationalRiskItem[]>([]);

  const [selectedPaymentId, setSelectedPaymentId] = useState("2");

  const [detail, setDetail] =
    useState<OperationalControlDetail | null>(null);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState<string | null>(null);

  const [detailLoading, setDetailLoading] = useState(false);

  const [detailError, setDetailError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDashboard() {
      try {
        setLoading(true);
        setError(null);

        const [summaryData, riskQueueData] = await Promise.all([
          getControlSummary(),
          getRiskQueue(),
        ]);

        setSummary(summaryData);
        setRiskQueue(riskQueueData);
      } catch (err) {
        console.error("Failed to load dashboard data:", err);
        setError("Unable to load settlement control data.");
      } finally {
        setLoading(false);
      }
    }

    void loadDashboard();
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadDetail() {
      try {
        setDetailLoading(true);
        setDetailError(null);

        const detailData = await getExceptionDetail(selectedPaymentId);

        if (!cancelled) {
          setDetail(detailData);
        }
      } catch (err) {
        if (!cancelled) {
          console.error(
            `Failed to load exception detail for ${selectedPaymentId}:`,
            err,
          );

          setDetail(null);
          setDetailError("Unable to load exception detail.");
        }
      } finally {
        if (!cancelled) {
          setDetailLoading(false);
        }
      }
    }

    if (!loading && summary) {
      void loadDetail();
    }

    return () => {
      cancelled = true;
    };
  }, [selectedPaymentId, loading, summary]);

  if (loading) {
    return (
      <div className="app-shell">
        <header className="topbar">
          <div className="brand">
            <div className="brand-mark">SC</div>
            <div>
              <div className="brand-name">Settlement Control</div>
              <div className="brand-subtitle">Razorpay Operations</div>
            </div>
          </div>

          <div className="system-state">
            <span className="system-dot" />
            Control plane operational
          </div>
        </header>

        <main className="main-content">
          <div className="state-card">
            Loading settlement control data...
          </div>
        </main>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="app-shell">
        <header className="topbar">
          <div className="brand">
            <div className="brand-mark">SC</div>
            <div>
              <div className="brand-name">Settlement Control</div>
              <div className="brand-subtitle">Razorpay Operations</div>
            </div>
          </div>

          <div className="system-state">
            <span className="system-dot" />
            Control plane operational
          </div>
        </header>

        <main className="main-content">
          <div className="state-card error-state">
            {error ?? "Settlement control data is unavailable."}
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">SC</div>

          <div>
            <div className="brand-name">Settlement Control</div>
            <div className="brand-subtitle">Razorpay Operations</div>
          </div>
        </div>

        <div className="system-state">
          <span className="system-dot" />
          Control plane operational
        </div>
      </header>

      <main className="main-content">
        <section className="page-heading">
          <div>
            <p className="eyebrow">OPERATIONS / SETTLEMENTS</p>

            <h1>Settlement Control Center</h1>

            <p className="page-description">
              Monitor settlement exceptions, controlled remediation, governance,
              and human resolution.
            </p>
          </div>

          <div className="last-updated">
            <span>Read-only operational view</span>
            <strong>Live backend integration</strong>
          </div>
        </section>

        <section className="metric-grid" aria-label="Settlement summary">
          <article className="metric-card">
            <span className="metric-label">Total exceptions</span>

            <strong className="metric-value">
              {summary.total_exceptions}
            </strong>

            <span className="metric-note">
              Current exception population
            </span>
          </article>

          <article className="metric-card">
            <span className="metric-label">Outstanding controls</span>

            <strong className="metric-value">
              {summary.outstanding_control_count}
            </strong>

            <span className="metric-note">
              Require operator attention
            </span>
          </article>

          <article className="metric-card">
            <span className="metric-label">Action required</span>

            <strong className="metric-value accent">
              {summary.action_required_count}
            </strong>

            <span className="metric-note">
              Immediate operational action
            </span>
          </article>

          <article className="metric-card">
            <span className="metric-label">Known financial impact</span>

            <strong className="metric-value">
              {formatMoney(summary.total_known_financial_impact)}
            </strong>

            <span className="metric-note">
              Across known-impact exceptions
            </span>
          </article>
        </section>

        <section className="workspace">
          <div className="panel queue-panel">
            <div className="panel-header">
              <div>
                <p className="panel-kicker">PRIORITIZED WORK</p>
                <h2>Risk Queue</h2>
              </div>

              <span className="panel-count">
                {riskQueue.length} exceptions
              </span>
            </div>

            <div className="queue-list">
              {riskQueue.map((item, index) => (
                <button
                  className={`queue-item ${
                    item.payment_id === selectedPaymentId ? "selected" : ""
                  }`}
                  key={item.payment_id}
                  type="button"
                  onClick={() => setSelectedPaymentId(item.payment_id)}
                >
                  <div className="queue-rank">{index + 1}</div>

                  <div className="queue-main">
                    <div className="queue-title-row">
                      <strong>{item.payment_id}</strong>

                      <StatusBadge variant={severityVariant(item.severity)}>
                        {item.severity}
                      </StatusBadge>
                    </div>

                    <span className="queue-category">
                      {formatLabel(item.category)}
                    </span>

                    <div className="queue-meta">
                      <span>
                        {formatLabel(item.attention_status)}
                      </span>

                      <span>
                        Governance:{" "}
                        {formatLabel(item.governance.governance_level)}
                      </span>
                    </div>
                  </div>

                  <div className="queue-impact">
                    <span>Impact</span>

                    <strong>{formatMoney(item.financial_impact)}</strong>

                    <small>Priority {item.priority_score}</small>
                  </div>
                </button>
              ))}
            </div>
          </div>

          <aside className="panel detail-panel">
            {detailLoading ? (
              <div className="state-card">
                Loading exception detail...
              </div>
            ) : detailError || !detail ? (
              <div className="state-card error-state">
                {detailError ?? "Exception detail is unavailable."}
              </div>
            ) : (
              <>
                <div className="detail-header">
                  <div>
                    <p className="panel-kicker">SELECTED EXCEPTION</p>
                    <h2>Payment {detail.payment_id}</h2>
                  </div>

                  <StatusBadge variant={severityVariant(detail.severity)}>
                    {detail.severity}
                  </StatusBadge>
                </div>

                <div className="exception-title">
                  <span>Exception category</span>
                  <strong>{formatLabel(detail.category)}</strong>
                </div>

                <div className="impact-block">
                  <span>Known financial impact</span>

                  <strong>{formatMoney(detail.financial_impact)}</strong>

                  <small>
                    {detail.financial_impact === null
                      ? "No deterministic financial impact recorded"
                      : "Deterministic exception impact"}
                  </small>
                </div>

                <div className="detail-grid">
                  <div>
                    <span>Priority</span>
                    <strong>{detail.priority_score}</strong>
                  </div>

                  <div>
                    <span>Remediation</span>
                    <strong>
                      {formatLabel(detail.remediation_status)}
                    </strong>
                  </div>

                  <div>
                    <span>Lifecycle</span>
                    <strong>
                      {formatLabel(detail.lifecycle_status)}
                    </strong>
                  </div>

                  <div>
                    <span>Human review</span>
                    <strong>
                      {detail.human_review_required
                        ? "REQUIRED"
                        : "NOT REQUIRED"}
                    </strong>
                  </div>
                </div>

                <div className="control-state">
                  <div className="state-row">
                    <span>Recommended action</span>

                    <StatusBadge variant="neutral">
                      {formatLabel(detail.recommended_action)}
                    </StatusBadge>
                  </div>

                  <div className="state-row">
                    <span>Controlled remediation</span>

                    <StatusBadge
                      variant={
                        detail.remediation_status === "COMPLETED"
                          ? "success"
                          : detail.remediation_status === "IN_PROGRESS"
                            ? "warning"
                            : "neutral"
                      }
                    >
                      {formatLabel(detail.remediation_status)}
                    </StatusBadge>
                  </div>
                </div>

                <div className="evidence-section">
                  <div className="section-title">
                    <span>CONTROL EVIDENCE</span>
                  </div>

                  {detail.controlled_actions.length === 0 ? (
                    <div className="evidence-row">
                      <div className="evidence-icon">01</div>

                      <div>
                        <strong>No controlled actions</strong>

                        <p>
                          No controlled remediation action has been recorded
                          for this exception.
                        </p>
                      </div>
                    </div>
                  ) : (
                    detail.controlled_actions.map((action, index) => (
                      <div className="evidence-row" key={action.id}>
                        <div className="evidence-icon">
                          {String(index + 1).padStart(2, "0")}
                        </div>

                        <div>
                          <strong>
                            Controlled action #{action.id}
                          </strong>

                          <p>
                            {formatLabel(action.action_type)} —{" "}
                            {formatLabel(action.status)}.
                          </p>

                          <p>{action.result ?? action.reason}</p>
                        </div>
                      </div>
                    ))
                  )}

                  <div className="evidence-row">
                    <div className="evidence-icon">
                      {String(detail.controlled_actions.length + 1).padStart(
                        2,
                        "0",
                      )}
                    </div>

                    <div>
                      <strong>Audit events</strong>

                      <p>
                        {detail.audit_events.length} authoritative audit
                        event
                        {detail.audit_events.length === 1 ? "" : "s"} recorded
                        for this exception.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="intelligence-preview">
                  <div className="intelligence-heading">
                    <div>
                      <span className="section-title">INTELLIGENCE</span>
                      <strong>Investigation context</strong>
                    </div>

                    <span className="ai-label">AI-ASSISTED</span>
                  </div>

                  <p>
                    Historical, timing, and population context will appear here
                    without changing deterministic financial truth.
                  </p>
                </div>

                <div className="operator-actions">
                  <button type="button" disabled>
                    Acknowledge
                  </button>

                  <button
                    type="button"
                    className="primary-action"
                    disabled
                  >
                    Resolve Exception
                  </button>
                </div>

                <p className="action-note">
                  Human actions will be connected to the authoritative backend
                  workflow in the next integration step.
                </p>
              </>
            )}
          </aside>
        </section>
      </main>
    </div>
  );
}

export default App;