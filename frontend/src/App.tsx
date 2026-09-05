import "./App.css";

import { useEffect, useState } from "react";

import {
  acknowledgeException,
  getAIInvestigation,
  getControlSummary,
  getExceptionDetail,
  getExceptionLifecycle,
  getGovernance,
  getHistoricalIntelligence,
  getRiskQueue,
  resolveException,
  type AIInvestigationAnalysis,
  type ExceptionLifecycleResponse,
  type GovernanceItem,
  type HistoricalExceptionIntelligenceResponse,
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

function governanceVariant(
  level: GovernanceItem["governance"]["governance_level"],
): "critical" | "warning" | "success" | "neutral" {
  if (level === "CRITICAL" || level === "HIGH") {
    return "critical";
  }

  if (level === "ELEVATED") {
    return "warning";
  }

  if (level === "NORMAL") {
    return "success";
  }

  return "neutral";
}

function App() {
  const [summary, setSummary] =
    useState<OperationalControlSummary | null>(null);

  const [riskQueue, setRiskQueue] = useState<OperationalRiskItem[]>([]);

  const [governance, setGovernance] = useState<GovernanceItem[]>([]);
  const [governanceLoading, setGovernanceLoading] = useState(true);
  const [governanceError, setGovernanceError] = useState<string | null>(null);

  const [selectedPaymentId, setSelectedPaymentId] = useState("2");

  const [detail, setDetail] =
    useState<OperationalControlDetail | null>(null);

  const [lifecycle, setLifecycle] =
    useState<ExceptionLifecycleResponse | null>(null);

  const [lifecycleLoading, setLifecycleLoading] = useState(false);

  const [lifecycleError, setLifecycleError] = useState<string | null>(null);

  const [historicalIntelligence, setHistoricalIntelligence] =
    useState<HistoricalExceptionIntelligenceResponse | null>(null);

  const [historicalIntelligenceLoading, setHistoricalIntelligenceLoading] =
    useState(false);

  const [historicalIntelligenceError, setHistoricalIntelligenceError] =
    useState<string | null>(null);

  const [aiInvestigation, setAiInvestigation] =
    useState<AIInvestigationAnalysis | null>(null);

  const [aiInvestigationLoading, setAiInvestigationLoading] =
    useState(false);

  const [aiInvestigationError, setAiInvestigationError] =
    useState<string | null>(null);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState<string | null>(null);

  const [detailLoading, setDetailLoading] = useState(false);

  const [detailError, setDetailError] = useState<string | null>(null);

  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [showResolveForm, setShowResolveForm] = useState(false);
  const [resolutionReason, setResolutionReason] =
    useState("MANUAL_RECONCILIATION");
  const [resolutionNote, setResolutionNote] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadDashboard() {
      try {
        setLoading(true);
        setError(null);

        const [summaryResult, riskQueueResult] = await Promise.all([
          getControlSummary(),
          getRiskQueue(),
        ]);

        if (!cancelled) {
          setSummary(summaryResult);
          setRiskQueue(riskQueueResult);
        }
      } catch (err) {
        if (!cancelled) {
          console.error("Failed to load dashboard data:", err);
          setError("Unable to load settlement control data.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadDashboard();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadGovernance() {
      try {
        setGovernanceLoading(true);
        setGovernanceError(null);

        const governanceData = await getGovernance();

        if (!cancelled) {
          setGovernance(governanceData);
        }
      } catch (err) {
        if (!cancelled) {
          console.error("Failed to load governance data:", err);
          setGovernance([]);
          setGovernanceError("Unable to load governance data.");
        }
      } finally {
        if (!cancelled) {
          setGovernanceLoading(false);
        }
      }
    }

    void loadGovernance();

    return () => {
      cancelled = true;
    };
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

  useEffect(() => {
    let cancelled = false;

    async function loadLifecycle() {
      try {
        setLifecycleLoading(true);
        setLifecycleError(null);
        setLifecycle(null);

        const lifecycleData =
          await getExceptionLifecycle(selectedPaymentId);

        if (!cancelled) {
          setLifecycle(lifecycleData);
        }
      } catch (err) {
        if (!cancelled) {
          console.error(
            `Failed to load lifecycle for ${selectedPaymentId}:`,
            err,
          );

          setLifecycle(null);

          if (
            err instanceof Error &&
            "status" in err &&
            err.status === 404
          ) {
            setLifecycleError(null);
          } else {
            setLifecycleError("Unable to load exception lifecycle.");
          }
        }
      } finally {
        if (!cancelled) {
          setLifecycleLoading(false);
        }
      }
    }

    if (!loading && summary) {
      void loadLifecycle();
    }

    return () => {
      cancelled = true;
    };
  }, [selectedPaymentId, loading, summary]);

  useEffect(() => {
    let cancelled = false;

    async function loadHistoricalIntelligence() {
      try {
        setHistoricalIntelligenceLoading(true);
        setHistoricalIntelligenceError(null);
        setHistoricalIntelligence(null);

        const intelligenceData =
          await getHistoricalIntelligence(selectedPaymentId);

        if (!cancelled) {
          setHistoricalIntelligence(intelligenceData);
        }
      } catch (err) {
        if (!cancelled) {
          console.error(
            `Failed to load historical intelligence for ${selectedPaymentId}:`,
            err,
          );

          setHistoricalIntelligence(null);
          setHistoricalIntelligenceError(
            "Unable to load historical intelligence.",
          );
        }
      } finally {
        if (!cancelled) {
          setHistoricalIntelligenceLoading(false);
        }
      }
    }

    if (!loading && summary) {
      void loadHistoricalIntelligence();
    }

    return () => {
      cancelled = true;
    };
  }, [selectedPaymentId, loading, summary]);

  useEffect(() => {
    let cancelled = false;

    async function loadAIInvestigation() {
      try {
        setAiInvestigationLoading(true);
        setAiInvestigationError(null);
        setAiInvestigation(null);

        const investigationData =
          await getAIInvestigation(selectedPaymentId);

        if (!cancelled) {
          setAiInvestigation(investigationData);
        }
      } catch (err) {
        if (!cancelled) {
          console.error(
            `Failed to load AI investigation for ${selectedPaymentId}:`,
            err,
          );

          setAiInvestigation(null);
          setAiInvestigationError(
            "AI investigation is currently unavailable.",
          );
        }
      } finally {
        if (!cancelled) {
          setAiInvestigationLoading(false);
        }
      }
    }

    if (!loading && summary) {
      void loadAIInvestigation();
    }

    return () => {
      cancelled = true;
    };
  }, [selectedPaymentId, loading, summary]);

  const selectedGovernance =
    governance.find(
      (item) => item.payment_id === selectedPaymentId,
    ) ?? null;

  async function refreshSelectedException() {
    const [detailData, lifecycleData, summaryData, riskQueueData] =
      await Promise.all([
        getExceptionDetail(selectedPaymentId),
        getExceptionLifecycle(selectedPaymentId),
        getControlSummary(),
        getRiskQueue(),
      ]);

    setDetail(detailData);
    setLifecycle(lifecycleData);
    setSummary(summaryData);
    setRiskQueue(riskQueueData);
  }

  async function handleAcknowledge() {
    try {
      setActionLoading(true);
      setActionError(null);

      await acknowledgeException(selectedPaymentId);
      await refreshSelectedException();
    } catch (err) {
      console.error("Failed to acknowledge exception:", err);
      setActionError(
        err instanceof Error
          ? err.message
          : "Unable to acknowledge exception.",
      );
    } finally {
      setActionLoading(false);
    }
  }

  async function handleResolve() {
    if (!resolutionNote.trim()) {
      setActionError("Resolution note is required.");
      return;
    }

    try {
      setActionLoading(true);
      setActionError(null);

      await resolveException(selectedPaymentId, {
        resolution_reason: resolutionReason,
        resolution_note: resolutionNote.trim(),
      });

      setShowResolveForm(false);
      setResolutionNote("");

      await refreshSelectedException();
    } catch (err) {
      console.error("Failed to resolve exception:", err);
      setActionError(
        err instanceof Error
          ? err.message
          : "Unable to resolve exception.",
      );
    } finally {
      setActionLoading(false);
    }
  }

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
              Monitor settlement exceptions, controlled remediation,
              governance, and human resolution.
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
                  className={`queue-item ${item.payment_id === selectedPaymentId ? "selected" : ""
                    }`}
                  key={item.payment_id}
                  type="button"
                  onClick={() => {
                    setSelectedPaymentId(item.payment_id);
                    setShowResolveForm(false);
                    setActionError(null);
                  }}
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
                      {lifecycleLoading
                        ? "LOADING"
                        : lifecycle?.status
                          ? formatLabel(lifecycle.status)
                          : lifecycleError
                            ? "UNAVAILABLE"
                            : "—"}
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


                <div className="operator-actions">
                  <button
                    type="button"
                    disabled={
                      actionLoading ||
                      lifecycle?.status !== "OPEN"
                    }
                    onClick={() => void handleAcknowledge()}
                  >
                    {actionLoading ? "Processing..." : "Acknowledge"}
                  </button>

                  <button
                    type="button"
                    className="primary-action"
                    disabled={
                      actionLoading ||
                      lifecycle?.status !== "ACKNOWLEDGED"
                    }
                    onClick={() => {
                      setActionError(null);
                      setShowResolveForm(true);
                    }}
                  >
                    Resolve Exception
                  </button>
                </div>

                {showResolveForm && lifecycle?.status === "ACKNOWLEDGED" && (
                  <div className="resolution-form">
                    <div className="section-title">
                      <span>HUMAN RESOLUTION</span>
                    </div>

                    <label>
                      Resolution reason
                      <select
                        value={resolutionReason}
                        onChange={(event) =>
                          setResolutionReason(event.target.value)
                        }
                        disabled={actionLoading}
                      >
                        <option value="MANUAL_RECONCILIATION">
                          Manual reconciliation
                        </option>
                        <option value="SETTLEMENT_CONFIRMED">
                          Settlement confirmed
                        </option>
                        <option value="DUPLICATE_EXCEPTION">
                          Duplicate exception
                        </option>
                        <option value="FALSE_POSITIVE">
                          False positive
                        </option>
                        <option value="OTHER">
                          Other
                        </option>
                      </select>
                    </label>

                    <label>
                      Resolution note
                      <textarea
                        value={resolutionNote}
                        onChange={(event) =>
                          setResolutionNote(event.target.value)
                        }
                        placeholder="Describe how the exception was resolved."
                        rows={4}
                        disabled={actionLoading}
                      />
                    </label>

                    <div className="operator-actions">
                      <button
                        type="button"
                        onClick={() => {
                          setShowResolveForm(false);
                          setActionError(null);
                          setResolutionReason("MANUAL_RECONCILIATION");
                        }}
                        disabled={actionLoading}
                      >
                        Cancel
                      </button>

                      <button
                        type="button"
                        className="primary-action"
                        onClick={() => void handleResolve()}
                        disabled={actionLoading || !resolutionNote.trim()}
                      >
                        {actionLoading ? "Resolving..." : "Confirm Resolution"}
                      </button>
                    </div>
                  </div>
                )}

                {actionError && (
                  <p className="action-error">
                    {actionError}
                  </p>
                )}

                <p className="action-note">
                  Human actions are executed through the authoritative exception
                  lifecycle and recorded in the audit trail.
                </p>
              </>
            )}
          </aside>
        </section>

        <section className="panel intelligence-panel">
          <div className="panel-header intelligence-panel-header">
            <div>
              <p className="panel-kicker">EXCEPTION INTELLIGENCE</p>
              <h2>Historical &amp; AI Investigation</h2>
              <p className="panel-subtitle">
                Deterministic historical evidence first, followed by AI-assisted investigation context.
              </p>
            </div>
          </div>

          <div className="intelligence-body">
            <section className="intelligence-block historical-block">
              <div className="block-heading">
                <div>
                  <span className="section-title">HISTORICAL CONTEXT</span>
                  <h3>Population-level evidence</h3>
                </div>
                <span className="ai-label">DETERMINISTIC</span>
              </div>

              {historicalIntelligenceLoading ? (
                <div className="state-card compact-state">
                  Loading historical intelligence...
                </div>
              ) : historicalIntelligenceError ? (
                <div className="state-card error-state compact-state">
                  {historicalIntelligenceError}
                </div>
              ) : historicalIntelligence ? (
                <>
                  <div className="history-metrics">
                    <div className="history-metric">
                      <span>Historical transactions</span>
                      <strong>
                        {historicalIntelligence.historical_context
                          .historical_transaction_count}
                      </strong>
                    </div>
                    <div className="history-metric">
                      <span>Historical exceptions</span>
                      <strong>
                        {historicalIntelligence.historical_context
                          .historical_exception_count}
                      </strong>
                    </div>
                    <div className="history-metric">
                      <span>Same category</span>
                      <strong>
                        {historicalIntelligence.historical_context
                          .same_category_exception_count}
                      </strong>
                    </div>
                    <div className="history-metric">
                      <span>Same currency</span>
                      <strong>
                        {historicalIntelligence.historical_context
                          .same_currency_exception_count}
                      </strong>
                    </div>
                  </div>

                  <div className="history-state-grid">
                    <div className="history-state-item">
                      <span>Category + currency recurrence</span>
                      <strong>
                        {historicalIntelligence.historical_context
                          .same_category_and_currency_exception_count}
                      </strong>
                    </div>
                    <div className="history-state-item">
                      <span>Recurrence detected</span>
                      <strong
                        className={
                          historicalIntelligence.historical_context
                            .recurrence_detected
                            ? "positive"
                            : ""
                        }
                      >
                        {historicalIntelligence.historical_context.recurrence_detected
                          ? "YES"
                          : "NO"}
                      </strong>
                    </div>
                    <div className="history-state-item">
                      <span>Settlement timing</span>
                      <strong>
                        {historicalIntelligence.historical_context.timing_available
                          ? "AVAILABLE"
                          : "UNAVAILABLE"}
                      </strong>
                    </div>
                    <div className="history-state-item">
                      <span>Historical average delay</span>
                      <strong>
                        {historicalIntelligence.historical_context
                          .historical_average_delay_hours !== null
                          ? `${historicalIntelligence.historical_context.historical_average_delay_hours.toFixed(
                            2,
                          )}h`
                          : "—"}
                      </strong>
                    </div>
                    <div className="history-state-item">
                      <span>Timing deviation</span>
                      <strong>
                        {historicalIntelligence.historical_context
                          .timing_deviation_hours !== null
                          ? `${historicalIntelligence.historical_context.timing_deviation_hours.toFixed(
                            2,
                          )}h`
                          : "—"}
                      </strong>
                    </div>
                  </div>

                  <p className="intelligence-note">
                    Historical context is population-level evidence and does not modify
                    deterministic exception classification, financial impact, priority,
                    governance, or human resolution authority.
                  </p>
                </>
              ) : (
                <div className="state-card compact-state">
                  Historical intelligence is unavailable for this exception.
                </div>
              )}
            </section>

            <div className="intelligence-divider" />

            <section className="intelligence-block ai-block">
              <div className="block-heading">
                <div>
                  <span className="section-title">AI-ASSISTED INVESTIGATION</span>
                  <h3>Investigation context</h3>
                </div>
                <span className="ai-label ai-label-prominent">AI-ASSISTED</span>
              </div>

              <p className="block-description">
                Advisory reasoning grounded in the selected exception and available historical evidence.
              </p>

              {aiInvestigationLoading ? (
                <div className="state-card">Generating investigation context...</div>
              ) : aiInvestigationError ? (
                <div className="state-card error-state">{aiInvestigationError}</div>
              ) : aiInvestigation ? (
                <>
                  <div className="ai-summary-card">
                    <div className="ai-summary-marker">01</div>
                    <div>
                      <span className="ai-investigation-label">Investigation summary</span>
                      <p className="ai-investigation-text">
                        {aiInvestigation.investigation_summary}
                      </p>
                    </div>
                  </div>

                  <div className="ai-investigation-grid">
                    <div className="ai-investigation-item">
                      <span className="ai-investigation-label">Historical context</span>
                      <p className="ai-investigation-text">
                        {aiInvestigation.historical_context_explanation}
                      </p>
                    </div>
                    <div className="ai-investigation-item">
                      <span className="ai-investigation-label">Timing context</span>
                      <p className="ai-investigation-text">
                        {aiInvestigation.timing_context_explanation}
                      </p>
                    </div>
                    <div className="ai-investigation-item">
                      <span className="ai-investigation-label">Evidence gaps</span>
                      <p className="ai-investigation-text">
                        {aiInvestigation.evidence_gaps}
                      </p>
                    </div>
                    <div className="ai-investigation-item">
                      <span className="ai-investigation-label">Investigation guidance</span>
                      <p className="ai-investigation-text">
                        {aiInvestigation.investigation_guidance}
                      </p>
                    </div>
                  </div>

                  <div className="ai-advisory-note">
                    <span>Advisory only</span>
                    <p>
                      AI-generated investigation context does not determine financial truth,
                      exception classification, priority, governance, remediation, or human resolution.
                    </p>
                  </div>
                </>
              ) : (
                <div className="state-card">
                  AI investigation is unavailable for this exception.
                </div>
              )}
            </section>
          </div>
        </section>

        <section className="panel governance-panel">
          <div className="panel-header">
            <div>
              <p className="panel-kicker">CONTROL GOVERNANCE</p>
              <h2>Operational Governance</h2>
            </div>

            {selectedGovernance && (
              <StatusBadge
                variant={governanceVariant(
                  selectedGovernance.governance.governance_level,
                )}
              >
                {formatLabel(
                  selectedGovernance.governance.governance_level,
                )}
              </StatusBadge>
            )}
          </div>

          {governanceLoading ? (
            <div className="state-card">
              Loading governance...
            </div>
          ) : governanceError ? (
            <div className="state-card error-state">
              {governanceError}
            </div>
          ) : selectedGovernance ? (
            <>
              <div className="detail-grid">
                <div>
                  <span>Governance level</span>

                  <strong>
                    {formatLabel(
                      selectedGovernance.governance.governance_level,
                    )}
                  </strong>
                </div>

                <div>
                  <span>Escalation</span>

                  <strong>
                    {selectedGovernance.governance.escalation_required
                      ? "REQUIRED"
                      : "NOT REQUIRED"}
                  </strong>
                </div>

                <div>
                  <span>Human review</span>

                  <strong>
                    {selectedGovernance.human_review_required
                      ? "REQUIRED"
                      : "NOT REQUIRED"}
                  </strong>
                </div>

                <div>
                  <span>Priority</span>

                  <strong>
                    {selectedGovernance.priority_score}
                  </strong>
                </div>
              </div>

              <div className="control-state">
                <div className="state-row">
                  <span>Governance reason</span>

                  <strong>
                    {selectedGovernance.governance.governance_reason}
                  </strong>
                </div>
              </div>
            </>
          ) : (
            <div className="state-card">
              No governance record available for this exception.
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;