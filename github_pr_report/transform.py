"""Convierte JSON crudo de la API de GitHub en modelos internos del dominio.

Aísla al resto de la aplicación del formato exacto de la API de GitHub.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .models import PullRequest, Review


def parse_github_datetime(value: str) -> datetime:
    """Parsea timestamps de GitHub (``YYYY-MM-DDTHH:MM:SSZ``) a UTC."""
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def review_from_json(raw: Dict[str, Any]) -> Review:
    user = raw.get("user") or {}
    return Review(author=user.get("login", ""), state=raw.get("state", ""))


def reviews_from_json(raw_reviews: List[Dict[str, Any]]) -> List[Review]:
    return [review_from_json(raw) for raw in raw_reviews]


def _requested_reviewer_logins(raw_pr: Dict[str, Any]) -> List[str]:
    return [user.get("login", "") for user in raw_pr.get("requested_reviewers") or []]


def _milestone_title(raw_pr: Dict[str, Any]) -> Optional[str]:
    milestone = raw_pr.get("milestone")
    if not milestone:
        return None
    return milestone.get("title")


def pull_request_from_json(
    raw_pr: Dict[str, Any], raw_reviews: Optional[List[Dict[str, Any]]] = None
) -> PullRequest:
    user = raw_pr.get("user") or {}
    return PullRequest(
        number=raw_pr["number"],
        title=raw_pr.get("title", ""),
        author=user.get("login", ""),
        created_at=parse_github_datetime(raw_pr["created_at"]),
        url=raw_pr.get("html_url", ""),
        requested_reviewers=tuple(_requested_reviewer_logins(raw_pr)),
        reviews=tuple(reviews_from_json(raw_reviews or [])),
        milestone_title=_milestone_title(raw_pr),
    )
