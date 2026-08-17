"""Orquestación reutilizable: cliente + transformación + lógica.

Punto de entrada único tanto para el CLI como para una futura web:
``build_reports(client, repo_urls)`` devuelve ``RepositoryReport`` listos
para renderizar, sin que el llamador tenga que conocer nada de HTTP.
"""

from typing import Iterable, List

from .client import GitHubAPIError, GitHubClient
from .logic import build_rows
from .models import RepositoryReport
from .transform import pull_request_from_json
from .urls import InvalidRepositoryURLError, parse_repo


def _build_single_report(client: GitHubClient, repo_url: str) -> RepositoryReport:
    try:
        owner, repo = parse_repo(repo_url)
    except InvalidRepositoryURLError as error:
        return RepositoryReport(repository=repo_url, rows=(), error=str(error))

    repository = f"{owner}/{repo}"
    try:
        raw_prs = client.list_open_pull_requests(owner, repo)
        pull_requests = []
        for raw_pr in raw_prs:
            raw_reviews = client.list_pull_request_reviews(owner, repo, raw_pr["number"])
            pull_requests.append(pull_request_from_json(raw_pr, raw_reviews))
        rows = build_rows(pull_requests)
        return RepositoryReport(repository=repository, rows=rows)
    except GitHubAPIError as error:
        return RepositoryReport(repository=repository, rows=(), error=str(error))


def build_reports(client: GitHubClient, repo_urls: Iterable[str]) -> List[RepositoryReport]:
    return [_build_single_report(client, repo_url) for repo_url in repo_urls]
