"""Cálculos operativos sobre pull requests. No conoce HTTP ni terminal."""

from datetime import datetime, timezone
from typing import Iterable, Optional, Tuple

from .models import PullRequest, PullRequestRow

SIN_APPROVAL = "Sin approval"
APPROVAL_COMPLETA = "-"
VERSION_NO_IDENTIFICADA = "No identificada"


def compute_age_days(created_at: datetime, now: datetime) -> int:
    return (now - created_at).days


def compute_pending_approval(pr: PullRequest) -> str:
    """"Approval pendiente" = reviewers solicitados que aún no aprobaron.

    - Sin reviewers solicitados y sin ninguna aprobación: "Sin approval".
    - Con aprobación y sin nadie pendiente: "-".
    - En otro caso: los logins de quienes faltan por aprobar.
    """
    approved_by = {review.author for review in pr.reviews if review.state == "APPROVED"}
    pending = [login for login in pr.requested_reviewers if login not in approved_by]

    if not pr.requested_reviewers and not approved_by:
        return SIN_APPROVAL
    if not pending:
        return APPROVAL_COMPLETA
    return ", ".join(pending)


def compute_target_version(pr: PullRequest) -> str:
    return pr.milestone_title or VERSION_NO_IDENTIFICADA


def build_row(pr: PullRequest, now: datetime) -> PullRequestRow:
    return PullRequestRow(
        number=pr.number,
        title=pr.title,
        author=pr.author,
        created_at=pr.created_at,
        age_days=compute_age_days(pr.created_at, now),
        pending_approval=compute_pending_approval(pr),
        target_version=compute_target_version(pr),
        url=pr.url,
    )


def build_rows(
    pull_requests: Iterable[PullRequest], now: Optional[datetime] = None
) -> Tuple[PullRequestRow, ...]:
    """Filas ya calculadas, ordenadas de más antigua a más reciente."""
    now = now or datetime.now(timezone.utc)
    rows = [build_row(pr, now) for pr in pull_requests]
    rows.sort(key=lambda row: row.created_at)
    return tuple(rows)
