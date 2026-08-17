from datetime import datetime, timezone

from github_pr_report.logic import (
    build_row,
    build_rows,
    compute_age_days,
    compute_pending_approval,
    compute_target_version,
)
from github_pr_report.models import PullRequest, Review

NOW = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)


def make_pr(**overrides):
    defaults = dict(
        number=1,
        title="t",
        author="alice",
        created_at=datetime(2024, 1, 5, 9, 0, 0, tzinfo=timezone.utc),
        url="https://github.com/acme/widgets/pull/1",
        requested_reviewers=(),
        reviews=(),
        milestone_title=None,
    )
    defaults.update(overrides)
    return PullRequest(**defaults)


def test_compute_age_days():
    created_at = datetime(2024, 1, 5, 9, 0, 0, tzinfo=timezone.utc)

    assert compute_age_days(created_at, NOW) == 10


def test_compute_pending_approval_no_reviewers_no_approvals_means_sin_approval():
    pr = make_pr(requested_reviewers=(), reviews=())

    assert compute_pending_approval(pr) == "Sin approval"


def test_compute_pending_approval_all_requested_approved_means_dash():
    pr = make_pr(requested_reviewers=(), reviews=(Review(author="frank", state="APPROVED"),))

    assert compute_pending_approval(pr) == "-"


def test_compute_pending_approval_lists_missing_reviewers():
    pr = make_pr(requested_reviewers=("bob", "carol"), reviews=())

    assert compute_pending_approval(pr) == "bob, carol"


def test_compute_pending_approval_excludes_already_approved_reviewers():
    pr = make_pr(
        requested_reviewers=("heidi", "ivan"),
        reviews=(Review(author="heidi", state="APPROVED"),),
    )

    assert compute_pending_approval(pr) == "ivan"


def test_compute_pending_approval_ignores_non_approved_reviews():
    pr = make_pr(
        requested_reviewers=("ivan",),
        reviews=(Review(author="ivan", state="CHANGES_REQUESTED"),),
    )

    assert compute_pending_approval(pr) == "ivan"


def test_compute_target_version_uses_milestone_title():
    pr = make_pr(milestone_title="v2.0")

    assert compute_target_version(pr) == "v2.0"


def test_compute_target_version_defaults_when_no_milestone():
    pr = make_pr(milestone_title=None)

    assert compute_target_version(pr) == "No identificada"


def test_build_row_combines_all_computed_fields():
    pr = make_pr(
        number=101,
        requested_reviewers=("bob",),
        reviews=(),
        milestone_title="v2.0",
    )

    row = build_row(pr, NOW)

    assert row.number == 101
    assert row.age_days == 10
    assert row.pending_approval == "bob"
    assert row.target_version == "v2.0"


def test_build_rows_sorts_oldest_first():
    older = make_pr(number=1, created_at=datetime(2024, 1, 5, tzinfo=timezone.utc))
    newer = make_pr(number=2, created_at=datetime(2024, 1, 10, tzinfo=timezone.utc))
    newest = make_pr(number=3, created_at=datetime(2024, 1, 12, tzinfo=timezone.utc))

    rows = build_rows([newest, older, newer], now=NOW)

    assert [row.number for row in rows] == [1, 2, 3]


def test_build_rows_defaults_now_to_current_time_when_omitted():
    pr = make_pr(created_at=datetime(2024, 1, 1, tzinfo=timezone.utc))

    rows = build_rows([pr])

    assert rows[0].age_days >= 0
