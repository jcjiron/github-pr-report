from conftest import FakeTransport, make_result
from github_pr_report.client import GitHubClient
from github_pr_report.presentation import render_report, render_reports
from github_pr_report.service import build_reports

BASE = "https://api.github.com"


def _pulls_url(owner, repo):
    return f"{BASE}/repos/{owner}/{repo}/pulls?state=open&per_page=100&sort=created&direction=asc"


def _reviews_url(owner, repo, number):
    return f"{BASE}/repos/{owner}/{repo}/pulls/{number}/reviews?per_page=100"


def _widgets_transport(fixture_loader):
    responses = {
        _pulls_url("acme", "widgets"): make_result(200, fixture_loader("pulls_open.json")),
        _pulls_url("acme", "empty"): make_result(200, fixture_loader("pulls_empty.json")),
        _pulls_url("acme", "ghost"): make_result(404, {"message": "Not Found"}),
    }
    for number in (101, 102, 103, 104):
        responses[_reviews_url("acme", "widgets", number)] = make_result(
            200, fixture_loader(f"reviews_{number}.json")
        )
    return FakeTransport(responses)


def test_build_reports_success_orders_and_computes_rows(fixture_loader):
    transport = _widgets_transport(fixture_loader)
    client = GitHubClient(transport=transport)

    reports = build_reports(client, ["acme/widgets"])

    assert len(reports) == 1
    report = reports[0]
    assert report.repository == "acme/widgets"
    assert report.error is None
    assert [row.number for row in report.rows] == [101, 103, 102, 104]

    by_number = {row.number: row for row in report.rows}
    assert by_number[101].pending_approval == "bob, carol"
    assert by_number[102].pending_approval == "Sin approval"
    assert by_number[103].pending_approval == "-"
    assert by_number[104].pending_approval == "ivan"
    assert by_number[101].target_version == "v2.0"
    assert by_number[102].target_version == "No identificada"


def test_build_reports_repo_with_no_open_prs(fixture_loader):
    transport = _widgets_transport(fixture_loader)
    client = GitHubClient(transport=transport)

    reports = build_reports(client, ["acme/empty"])

    assert reports[0].repository == "acme/empty"
    assert reports[0].rows == ()
    assert reports[0].error is None


def test_build_reports_invalid_url_does_not_hit_client(fixture_loader):
    transport = _widgets_transport(fixture_loader)
    client = GitHubClient(transport=transport)

    reports = build_reports(client, ["not a valid url"])

    assert reports[0].repository == "not a valid url"
    assert reports[0].error is not None
    assert transport.requests == []


def test_build_reports_repository_not_found_is_captured_as_error(fixture_loader):
    transport = _widgets_transport(fixture_loader)
    client = GitHubClient(transport=transport)

    reports = build_reports(client, ["acme/ghost"])

    assert reports[0].repository == "acme/ghost"
    assert reports[0].error is not None
    assert reports[0].rows == ()


def test_build_reports_handles_multiple_repos_independently(fixture_loader):
    transport = _widgets_transport(fixture_loader)
    client = GitHubClient(transport=transport)

    reports = build_reports(client, ["acme/widgets", "acme/ghost", "acme/empty"])

    assert [r.repository for r in reports] == ["acme/widgets", "acme/ghost", "acme/empty"]
    assert reports[0].error is None and reports[0].rows
    assert reports[1].error is not None
    assert reports[2].error is None and reports[2].rows == ()


def test_render_report_success_includes_header_and_rows(fixture_loader):
    transport = _widgets_transport(fixture_loader)
    client = GitHubClient(transport=transport)
    report = build_reports(client, ["acme/widgets"])[0]

    output = render_report(report)

    assert "## acme/widgets" in output
    assert "bob, carol" in output
    assert "Add retry logic to the sync worker" in output


def test_render_report_with_error():
    from github_pr_report.models import RepositoryReport

    report = RepositoryReport(repository="acme/ghost", rows=(), error="boom")

    output = render_report(report)

    assert "## acme/ghost" in output
    assert "ERROR: boom" in output


def test_render_report_with_no_open_prs():
    from github_pr_report.models import RepositoryReport

    report = RepositoryReport(repository="acme/empty", rows=())

    output = render_report(report)

    assert "Sin PRs abiertos." in output


def test_render_reports_joins_every_report_separated_by_blank_line(fixture_loader):
    transport = _widgets_transport(fixture_loader)
    client = GitHubClient(transport=transport)
    reports = build_reports(client, ["acme/widgets", "acme/ghost"])

    output = render_reports(reports)

    assert output.count("## acme/") == 2
    assert "\n\n" in output
