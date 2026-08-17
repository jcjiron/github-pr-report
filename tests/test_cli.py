import pytest

from github_pr_report import cli
from github_pr_report.models import RepositoryReport


def test_build_arg_parser_allows_repeated_repo():
    parser = cli.build_arg_parser()

    args = parser.parse_args(["--repo", "acme/a", "--repo", "acme/b"])

    assert args.repos == ["acme/a", "acme/b"]


def test_build_arg_parser_requires_at_least_one_repo():
    parser = cli.build_arg_parser()

    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_read_token_returns_env_var_value(monkeypatch):
    monkeypatch.setenv(cli.TOKEN_ENV_VAR, "secret-token")

    assert cli._read_token() == "secret-token"


def test_read_token_returns_none_when_absent(monkeypatch):
    monkeypatch.delenv(cli.TOKEN_ENV_VAR, raising=False)

    assert cli._read_token() is None


def test_main_prints_report_and_returns_zero_on_success(monkeypatch, capsys):
    captured = {}

    def fake_build_reports(client, repos):
        captured["client"] = client
        captured["repos"] = repos
        return [RepositoryReport(repository="acme/widgets", rows=())]

    monkeypatch.setattr(cli, "build_reports", fake_build_reports)
    monkeypatch.setenv(cli.TOKEN_ENV_VAR, "secret-token")

    exit_code = cli.main(["--repo", "acme/widgets"])

    assert exit_code == 0
    assert captured["repos"] == ["acme/widgets"]
    assert captured["client"].token == "secret-token"
    assert "acme/widgets" in capsys.readouterr().out


def test_main_returns_one_when_any_report_has_error(monkeypatch, capsys):
    def fake_build_reports(client, repos):
        return [
            RepositoryReport(repository="acme/widgets", rows=()),
            RepositoryReport(repository="acme/ghost", rows=(), error="no encontrado"),
        ]

    monkeypatch.setattr(cli, "build_reports", fake_build_reports)

    exit_code = cli.main(["--repo", "acme/widgets", "--repo", "acme/ghost"])

    assert exit_code == 1
    assert "no encontrado" in capsys.readouterr().out


def test_main_does_not_require_token(monkeypatch, capsys):
    monkeypatch.delenv(cli.TOKEN_ENV_VAR, raising=False)
    captured = {}

    def fake_build_reports(client, repos):
        captured["client"] = client
        return [RepositoryReport(repository="acme/widgets", rows=())]

    monkeypatch.setattr(cli, "build_reports", fake_build_reports)

    exit_code = cli.main(["--repo", "acme/widgets"])

    assert exit_code == 0
    assert captured["client"].token is None
