import pytest

from conftest import FakeTransport, make_result
from github_pr_report.client import (
    GitHubAPIError,
    GitHubClient,
    RateLimitError,
    RepositoryNotFoundError,
)

PULLS_URL = "https://api.github.com/repos/acme/widgets/pulls?state=open&per_page=100&sort=created&direction=asc"


def test_list_open_pull_requests_follows_pagination():
    page2_url = "https://api.github.com/repos/acme/widgets/pulls?page=2"
    transport = FakeTransport(
        {
            PULLS_URL: make_result(200, [{"number": 1}], headers={"Link": f'<{page2_url}>; rel="next"'}),
            page2_url: make_result(200, [{"number": 2}]),
        }
    )
    client = GitHubClient(transport=transport)

    result = client.list_open_pull_requests("acme", "widgets")

    assert [pr["number"] for pr in result] == [1, 2]
    assert len(transport.requests) == 2


def test_stops_paginating_when_no_next_link():
    transport = FakeTransport({PULLS_URL: make_result(200, [{"number": 1}])})
    client = GitHubClient(transport=transport)

    result = client.list_open_pull_requests("acme", "widgets")

    assert [pr["number"] for pr in result] == [1]
    assert len(transport.requests) == 1


def test_includes_authorization_header_when_token_set():
    transport = FakeTransport({PULLS_URL: make_result(200, [])})
    client = GitHubClient(token="secret", transport=transport)

    client.list_open_pull_requests("acme", "widgets")

    _, _, headers = transport.requests[0]
    assert headers["Authorization"] == "Bearer secret"


def test_omits_authorization_header_without_token():
    transport = FakeTransport({PULLS_URL: make_result(200, [])})
    client = GitHubClient(transport=transport)

    client.list_open_pull_requests("acme", "widgets")

    _, _, headers = transport.requests[0]
    assert "Authorization" not in headers


def test_404_raises_repository_not_found():
    transport = FakeTransport({PULLS_URL: make_result(404, {"message": "Not Found"})})
    client = GitHubClient(transport=transport)

    with pytest.raises(RepositoryNotFoundError):
        client.list_open_pull_requests("acme", "widgets")


def test_rate_limit_raises_rate_limit_error():
    transport = FakeTransport(
        {
            PULLS_URL: make_result(
                403,
                {"message": "API rate limit exceeded"},
                headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1700000000"},
            )
        }
    )
    client = GitHubClient(transport=transport)

    with pytest.raises(RateLimitError) as exc_info:
        client.list_open_pull_requests("acme", "widgets")

    assert exc_info.value.reset_at == "1700000000"


def test_forbidden_without_rate_limit_headers_raises_generic_api_error():
    transport = FakeTransport({PULLS_URL: make_result(403, {"message": "Forbidden"})})
    client = GitHubClient(transport=transport)

    with pytest.raises(GitHubAPIError) as exc_info:
        client.list_open_pull_requests("acme", "widgets")

    assert not isinstance(exc_info.value, RateLimitError)


def test_generic_error_raises_github_api_error_with_message():
    transport = FakeTransport({PULLS_URL: make_result(500, {"message": "Server error"})})
    client = GitHubClient(transport=transport)

    with pytest.raises(GitHubAPIError) as exc_info:
        client.list_open_pull_requests("acme", "widgets")

    assert exc_info.value.status == 500
    assert exc_info.value.message == "Server error"


def test_list_pull_request_reviews_builds_expected_url():
    url = "https://api.github.com/repos/acme/widgets/pulls/42/reviews?per_page=100"
    transport = FakeTransport({url: make_result(200, [{"id": 1}])})
    client = GitHubClient(transport=transport)

    result = client.list_pull_request_reviews("acme", "widgets", 42)

    assert result == [{"id": 1}]
