from dataclasses import dataclass


@dataclass(frozen=True)
class GovernanceClassification:
    governance_level: str
    escalation_required: bool
    governance_reason: str


def classify_governance(
    *,
    lifecycle_status,
    remediation_status: str,
    aging_band: str | None,
    priority_score: int,
    human_review_required: bool,
) -> GovernanceClassification:
    """
    Deterministically classify governance and escalation state.

    Governance is derived from trusted operational-control state.

    This function does not:
    - modify financial records,
    - modify exception lifecycle state,
    - execute controlled actions,
    - call AI,
    - create audit events,
    - or persist governance state.
    """

    if lifecycle_status == "RESOLVED":
        return GovernanceClassification(
            governance_level="NORMAL",
            escalation_required=False,
            governance_reason=(
                "Exception is resolved and requires no further "
                "operational escalation."
            ),
        )

    if remediation_status == "IN_PROGRESS":
        return GovernanceClassification(
            governance_level="ELEVATED",
            escalation_required=False,
            governance_reason=(
                "Controlled remediation is currently in progress."
            ),
        )

    if (
        remediation_status == "COMPLETED"
        and lifecycle_status != "RESOLVED"
    ):
        if priority_score >= 75:
            return GovernanceClassification(
                governance_level="HIGH",
                escalation_required=True,
                governance_reason=(
                    "Controlled remediation completed, but human "
                    "resolution is still required for a high-priority "
                    "exception."
                ),
            )

        return GovernanceClassification(
            governance_level="ELEVATED",
            escalation_required=True,
            governance_reason=(
                "Controlled remediation completed, but human "
                "resolution is still required."
            ),
        )

    if (
        aging_band == "OVERDUE"
        and priority_score >= 75
    ):
        return GovernanceClassification(
            governance_level="CRITICAL",
            escalation_required=True,
            governance_reason=(
                "Unresolved exception is overdue and has high "
                "operational priority."
            ),
        )

    if aging_band == "OVERDUE":
        return GovernanceClassification(
            governance_level="HIGH",
            escalation_required=True,
            governance_reason=(
                "Unresolved exception has exceeded the operational "
                "aging threshold."
            ),
        )

    if human_review_required:
        if priority_score >= 75:
            return GovernanceClassification(
                governance_level="HIGH",
                escalation_required=True,
                governance_reason=(
                    "Immediate operational action is required for a "
                    "high-priority exception."
                ),
            )

        return GovernanceClassification(
            governance_level="ELEVATED",
            escalation_required=True,
            governance_reason=(
                "Immediate operational action is required."
            ),
        )

    return GovernanceClassification(
        governance_level="NORMAL",
        escalation_required=False,
        governance_reason=(
            "No elevated governance condition is currently present."
        ),
    )