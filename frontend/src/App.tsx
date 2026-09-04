import './App.css'

type RiskRow = {
  paymentId: string
  category: string
  severity: string
  impact: string
  priority: number
  attention: string
  governance: string
}

const riskQueue: RiskRow[] = [
  {
    paymentId: 'pay_test_001',
    category: 'UNDER_SETTLEMENT',
    severity: 'HIGH',
    impact: '₹500.00',
    priority: 100,
    attention: 'ACTION REQUIRED',
    governance: 'CRITICAL',
  },
  {
    paymentId: '2',
    category: 'MISSING_SETTLEMENT',
    severity: 'HIGH',
    impact: '₹15,000.00',
    priority: 100,
    attention: 'HUMAN RESOLUTION REQUIRED',
    governance: 'HIGH',
  },
  {
    paymentId: 'pay_recon_over_001',
    category: 'OVER_SETTLEMENT',
    severity: 'MEDIUM',
    impact: '₹100.00',
    priority: 50,
    attention: 'MONITOR',
    governance: 'NORMAL',
  },
  {
    paymentId: 'pay_recon_currency_001',
    category: 'CURRENCY_MISMATCH',
    severity: 'MEDIUM',
    impact: '—',
    priority: 50,
    attention: 'MONITOR',
    governance: 'NORMAL',
  },
]

function StatusBadge({
  children,
  variant = 'neutral',
}: {
  children: React.ReactNode
  variant?: 'critical' | 'warning' | 'success' | 'neutral'
}) {
  return <span className={`status-badge ${variant}`}>{children}</span>
}

function App() {
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
            <strong>Live backend integration next</strong>
          </div>
        </section>

        <section className="metric-grid" aria-label="Settlement summary">
          <article className="metric-card">
            <span className="metric-label">Total exceptions</span>
            <strong className="metric-value">6</strong>
            <span className="metric-note">Current exception population</span>
          </article>

          <article className="metric-card">
            <span className="metric-label">Outstanding controls</span>
            <strong className="metric-value">2</strong>
            <span className="metric-note">Require operator attention</span>
          </article>

          <article className="metric-card">
            <span className="metric-label">Action required</span>
            <strong className="metric-value accent">1</strong>
            <span className="metric-note">Immediate operational action</span>
          </article>

          <article className="metric-card">
            <span className="metric-label">Known financial impact</span>
            <strong className="metric-value">₹15,500</strong>
            <span className="metric-note">Across known-impact exceptions</span>
          </article>
        </section>

        <section className="workspace">
          <div className="panel queue-panel">
            <div className="panel-header">
              <div>
                <p className="panel-kicker">PRIORITIZED WORK</p>
                <h2>Risk Queue</h2>
              </div>

              <span className="panel-count">6 exceptions</span>
            </div>

            <div className="queue-list">
              {riskQueue.map((item, index) => (
                <article
                  className={`queue-item ${
                    item.paymentId === '2' ? 'selected' : ''
                  }`}
                  key={item.paymentId}
                >
                  <div className="queue-rank">{index + 1}</div>

                  <div className="queue-main">
                    <div className="queue-title-row">
                      <strong>{item.paymentId}</strong>
                      <StatusBadge
                        variant={
                          item.severity === 'HIGH'
                            ? 'critical'
                            : item.severity === 'MEDIUM'
                              ? 'warning'
                              : 'neutral'
                        }
                      >
                        {item.severity}
                      </StatusBadge>
                    </div>

                    <span className="queue-category">{item.category}</span>

                    <div className="queue-meta">
                      <span>{item.attention}</span>
                      <span>Governance: {item.governance}</span>
                    </div>
                  </div>

                  <div className="queue-impact">
                    <span>Impact</span>
                    <strong>{item.impact}</strong>
                    <small>Priority {item.priority}</small>
                  </div>
                </article>
              ))}
            </div>
          </div>

          <aside className="panel detail-panel">
            <div className="detail-header">
              <div>
                <p className="panel-kicker">SELECTED EXCEPTION</p>
                <h2>Payment 2</h2>
              </div>

              <StatusBadge variant="critical">HIGH</StatusBadge>
            </div>

            <div className="exception-title">
              <span>Exception category</span>
              <strong>MISSING_SETTLEMENT</strong>
            </div>

            <div className="impact-block">
              <span>Known financial impact</span>
              <strong>₹15,000.00</strong>
              <small>Expected settlement amount</small>
            </div>

            <div className="detail-grid">
              <div>
                <span>Priority</span>
                <strong>100</strong>
              </div>

              <div>
                <span>Governance</span>
                <strong>HIGH</strong>
              </div>

              <div>
                <span>Escalation</span>
                <strong>REQUIRED</strong>
              </div>

              <div>
                <span>Human review</span>
                <strong>REQUIRED</strong>
              </div>
            </div>

            <div className="control-state">
              <div className="state-row">
                <span>Controlled remediation</span>
                <StatusBadge variant="success">COMPLETED</StatusBadge>
              </div>

              <div className="state-row">
                <span>Exception lifecycle</span>
                <StatusBadge variant="warning">OPEN</StatusBadge>
              </div>
            </div>

            <div className="evidence-section">
              <div className="section-title">
                <span>CONTROL EVIDENCE</span>
              </div>

              <div className="evidence-row">
                <div className="evidence-icon">01</div>
                <div>
                  <strong>Deterministic reconciliation</strong>
                  <p>
                    No corresponding settlement was found for the transaction.
                  </p>
                </div>
              </div>

              <div className="evidence-row">
                <div className="evidence-icon">02</div>
                <div>
                  <strong>Controlled action</strong>
                  <p>
                    Investigation action completed without changing financial
                    state.
                  </p>
                </div>
              </div>

              <div className="evidence-row">
                <div className="evidence-icon">03</div>
                <div>
                  <strong>Human resolution</strong>
                  <p>
                    Operator decision is still required before the exception
                    can be resolved.
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
              <button type="button" className="primary-action" disabled>
                Resolve Exception
              </button>
            </div>

            <p className="action-note">
              Human actions will be connected to the authoritative backend
              workflow in the next integration step.
            </p>
          </aside>
        </section>
      </main>
    </div>
  )
}

export default App