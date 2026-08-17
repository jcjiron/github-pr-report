"""Dataclasses del dominio. No dependen de HTTP ni de formato de terminal."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple


@dataclass(frozen=True)
class Review:
    author: str
    state: str


@dataclass(frozen=True)
class PullRequest:
    number: int
    title: str
    author: str
    created_at: datetime
    url: str
    requested_reviewers: Tuple[str, ...]
    reviews: Tuple[Review, ...]
    milestone_title: Optional[str]


@dataclass(frozen=True)
class PullRequestRow:
    number: int
    title: str
    author: str
    created_at: datetime
    age_days: int
    pending_approval: str
    target_version: str
    url: str


@dataclass(frozen=True)
class RepositoryReport:
    repository: str
    rows: Tuple[PullRequestRow, ...] = ()
    error: Optional[str] = None
