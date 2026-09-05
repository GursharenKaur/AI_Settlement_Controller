const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export type ExceptionCategory =
  | "NONE"
  | "MISSING_SETTLEMENT"
  | "UNDER_SETTLEMENT"
  | "OVER_SETTLEMENT"
  | "CURRENCY_MISMATCH"
  | "INVALID_STATE";

export type ExceptionSeverity =
  | "NONE"
  | "LOW"
  | "MEDIUM"
  | "HIGH";

export type ExceptionLifecycleStatus =
  | "OPEN"
  | "ACKNOWLEDGED"
  | "RESOLVED";

export type ControllerAction =
  | "INVESTIGATE_MISSING_SETTLEMENT"
  | "REVIEW_SETTLEMENT_AMOUNT"
  | "REVIEW_CURRENCY_MISMATCH"
  | "INVESTIGATE_INVALID_STATE"
  | "NO_FURTHER_ACTION";

export type GovernanceLevel =
  | "NORMAL"
  | "ELEVATED"
  | "HIGH"
  | "CRITICAL";

export type RemediationStatus =
  | "NOT_STARTED"
  | "REQUESTED"
  | "IN_PROGRESS"
  | "COMPLETED"
  | "FAILED"
  | "REJECTED";

export type AttentionStatus =
  | "NO_ACTION_REQUIRED"
  | "IN_PROGRESS"
  | "HUMAN_RESOLUTION_REQUIRED"
  | "ACTION_REQUIRED"
  | "MONITOR";

export interface GovernanceClassification {
  governance_level: GovernanceLevel;
  escalation_required: boolean;
  governance_reason: string;
}

export interface GovernanceResponse {
  value: GovernanceItem[];
  Count: number;
}

export interface GovernanceItem {
  payment_id: string;
  category: ExceptionCategory;
  severity: ExceptionSeverity;
  financial_impact: string | null;
  priority_score: number;
  age_minutes: number | null;
  age_hours: number | null;
  aging_band: string | null;
  lifecycle_status: ExceptionLifecycleStatus | null;
  recommended_action: ControllerAction;
  human_review_required: boolean;
  controlled_actions: OperationalControlAction[];
  remediation_status: RemediationStatus;
  governance: GovernanceClassification;
}



export interface OperationalRiskItem {
  payment_id: string;
  category: ExceptionCategory;
  severity: ExceptionSeverity;
  financial_impact: string | null;
  priority_score: number;
  age_minutes: number | null;
  age_hours: number | null;
  aging_band: string | null;
  lifecycle_status: ExceptionLifecycleStatus | null;
  recommended_action: ControllerAction;
  human_review_required: boolean;
  remediation_status: RemediationStatus;
  attention_status: AttentionStatus;
  governance: GovernanceClassification;
}

export type OperationalRiskResponse = OperationalRiskItem[];

export interface OperationalControlSummary {
  total_exceptions: number;
  action_required_count: number;
  in_progress_count: number;
  human_resolution_required_count: number;
  monitor_count: number;
  no_action_required_count: number;
  total_known_financial_impact: string;
  highest_priority_payment_id: string | null;
  highest_priority_score: number | null;
  highest_priority_financial_impact: string | null;
  outstanding_control_count: number;
}

export interface OperationalControlAction {
  id: number;
  action_type: ControllerAction;
  status: RemediationStatus;
  reason: string;
  result: string | null;
  created_at: string;
  updated_at: string;
  executed_at: string | null;
}

export interface OperationalControlAuditEvent {
  id: number;
  payment_id: string;
  controlled_action_id: number | null;
  event_type: string;
  message: string;
  previous_status: string | null;
  new_status: string | null;
  created_at: string;
}

export interface OperationalControlDetail {
  payment_id: string;
  category: ExceptionCategory;
  severity: ExceptionSeverity;
  financial_impact: string | null;
  priority_score: number;
  age_minutes: number | null;
  age_hours: number | null;
  aging_band: string | null;
  lifecycle_status: ExceptionLifecycleStatus | null;
  recommended_action: ControllerAction;
  human_review_required: boolean;
  remediation_status: RemediationStatus;
  controlled_actions: OperationalControlAction[];
  audit_events: OperationalControlAuditEvent[];
}

export interface CurrentExceptionContext {
  category: ExceptionCategory;
  severity: ExceptionSeverity;
  financial_impact: string | null;
  priority_score: number;
}

export interface HistoricalExceptionContext {
  historical_transaction_count: number;
  historical_exception_count: number;
  same_category_exception_count: number;
  same_currency_exception_count: number;
  same_category_and_currency_exception_count: number;
  recurrence_detected: boolean;
  timing_available: boolean;
  settlement_delay_hours: number | null;
  historical_settlement_count: number;
  historical_average_delay_hours: number | null;
  timing_deviation_hours: number | null;
}

export interface HistoricalExceptionIntelligenceResponse {
  payment_id: string;
  current_exception: CurrentExceptionContext;
  historical_context: HistoricalExceptionContext;
}

export interface ExceptionLifecycleResponse {
  payment_id: string;
  status: ExceptionLifecycleStatus;
  created_at: string;
  updated_at: string;
  resolution_reason: string | null;
  resolution_note: string | null;
  resolved_at: string | null;
  controlled_actions: OperationalControlAction[];
}

export interface ExceptionPattern {
  category: ExceptionCategory;
  exception_count: number;
  high_severity_count: number;
  known_financial_impact_by_currency: Record<string, string>;
}

export interface PatternIntelligenceResponse {
  total_transactions: number;
  total_exceptions: number;
  categories: ExceptionPattern[];
  recurring_categories: ExceptionCategory[];
}

export interface AIInvestigationAnalysis {
  payment_id: string;
  investigation_summary: string;
  historical_context_explanation: string;
  timing_context_explanation: string;
  evidence_gaps: string[];
  investigation_guidance: string[];
}

class ApiError extends Error {
  status: number;

  constructor(status: number, statusText: string) {
    super(`API request failed: ${status} ${statusText}`);
    this.name = "ApiError";
    this.status = status;
  }
}

async function apiRequest<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {}),
    },
  });

  if (!response.ok) {
    throw new ApiError(response.status, response.statusText);
  }

  return response.json() as Promise<T>;
}


export function getControlSummary(): Promise<OperationalControlSummary> {
  return apiRequest<OperationalControlSummary>("/control/summary");
}

export function getRiskQueue(): Promise<OperationalRiskResponse> {
  return apiRequest<OperationalRiskResponse>("/risk/queue");
}

export function getExceptionDetail(
  paymentId: string,
): Promise<OperationalControlDetail> {
  return apiRequest<OperationalControlDetail>(
    `/control/exceptions/${encodeURIComponent(paymentId)}/detail`,
  );
}

export function getHistoricalIntelligence(
  paymentId: string,
): Promise<HistoricalExceptionIntelligenceResponse> {
  return apiRequest<HistoricalExceptionIntelligenceResponse>(
    `/intelligence/exceptions/${encodeURIComponent(paymentId)}`,
  );
}

export function getPatternIntelligence(): Promise<PatternIntelligenceResponse> {
  return apiRequest<PatternIntelligenceResponse>("/intelligence/patterns");
}

export function getAIInvestigation(
  paymentId: string,
): Promise<AIInvestigationAnalysis> {
  return apiRequest<AIInvestigationAnalysis>(
    `/intelligence/exceptions/${encodeURIComponent(paymentId)}/investigation`,
  );
}

export async function getExceptionLifecycle(
  paymentId: string,
): Promise<ExceptionLifecycleResponse | null> {
  try {
    return await apiRequest<ExceptionLifecycleResponse>(
      `/exceptions/${encodeURIComponent(paymentId)}/lifecycle`,
    );
  } catch (error) {
    if (
      error instanceof Error &&
      error.message.startsWith("API request failed: 404")
    ) {
      return null;
    }

    throw error;
  }
}

export async function getGovernance(): Promise<GovernanceItem[]> {
  const response = await apiRequest<
    GovernanceItem[] | GovernanceResponse
  >("/control/governance");

  if (Array.isArray(response)) {
    return response;
  }

  return response.value;
}