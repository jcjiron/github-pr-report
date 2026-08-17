from datetime import datetime, timezone

from github_pr_report.models import PullRequest, Review
from github_pr_report.transform import (
    parse_github_datetime,
    pull_request_from_json,
    review_from_json,
    reviews_from_json,
)


def test_parse_github_datetime_returns_utc_aware_datetime():
    result = parse_github_datetime("2024-01-05T09:00:00Z")

    assert result == datetime(2024, 1, 5, 9, 0, 0, tzinfo=timezone.utc)


def test_review_from_json_extracts_author_and_state():
    raw = {"user": {"login": "frank"}, "state": "APPROVED"}

    review = review_from_json(raw)

    assert review == Review(author="frank", state="APPROVED")


def test_reviews_from_json_maps_every_entry():
    raw = [
        {"user": {"login": "frank"}, "state": "APPROVED"},
        {"user": {"login": "grace"}, "state": "CHANGES_REQUESTED"},
    ]

    reviews = reviews_from_json(raw)

    assert reviews == [
        Review(author="frank", state="APPROVED"),
        Review(author="grace", state="CHANGES_REQUESTED"),
    ]


def test_pull_request_from_json_builds_full_pull_request(fixture_loader):
    raw_prs = fixture_loader("pulls_open.json")
    raw_pr = next(pr for pr in raw_prs if pr["number"] == 101)
    raw_reviews = fixture_loader("reviews_101.json")

    pr = pull_request_from_json(raw_pr, raw_reviews)

    assert pr == PullRequest(
        number=101,
        title="Add retry logic to the sync worker",
        author="alice",
        created_at=datetime(2024, 1, 5, 9, 0, 0, tzinfo=timezone.utc),
        url="https://github.com/acme/widgets/pull/101",
        requested_reviewers=("bob", "carol"),
        reviews=(),
        milestone_title="v2.0",
    )


def test_pull_request_from_json_handles_missing_milestone(fixture_loader):
    raw_prs = fixture_loader("pulls_open.json")
    raw_pr = next(pr for pr in raw_prs if pr["number"] == 102)

    pr = pull_request_from_json(raw_pr)

    assert pr.milestone_title is None
    assert pr.requested_reviewers == ()
    assert pr.reviews == ()


def test_pull_request_from_json_defaults_reviews_to_empty_tuple():
    raw_pr = {
        "number": 1,
        "title": "t",
        "user": {"login": "alice"},
        "created_at": "2024-01-01T00:00:00Z",
        "html_url": "https://github.com/acme/widgets/pull/1",
    }

    pr = pull_request_from_json(raw_pr)

    assert pr.reviews == ()
    assert pr.requested_reviewers == ()
    assert pr.milestone_title is None
