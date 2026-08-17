import pytest

from github_pr_report.urls import InvalidRepositoryURLError, parse_repo


@pytest.mark.parametrize(
    "value",
    [
        "https://github.com/acme/widgets",
        "https://github.com/acme/widgets/",
        "https://github.com/acme/widgets.git",
        "http://github.com/acme/widgets",
        "https://www.github.com/acme/widgets",
        "git@github.com:acme/widgets.git",
        "git@github.com:acme/widgets",
        "acme/widgets",
    ],
)
def test_parse_repo_accepts_supported_formats(value):
    assert parse_repo(value) == ("acme", "widgets")


def test_parse_repo_strips_surrounding_whitespace():
    assert parse_repo("  acme/widgets  ") == ("acme", "widgets")


@pytest.mark.parametrize(
    "value",
    [
        "",
        "   ",
        "not-a-repo",
        "https://gitlab.com/acme/widgets",
        "acme/",
        "/widgets",
        "acme/widgets/extra",
    ],
)
def test_parse_repo_rejects_invalid_values(value):
    with pytest.raises(InvalidRepositoryURLError):
        parse_repo(value)
