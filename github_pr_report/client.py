"""Capa de acceso a la API REST de GitHub.

Responsable de HTTP, autenticación, paginación, rate limits y errores.
El transporte es inyectable (``transport``) para poder probar sin red.
No conoce nada del dominio ni de la presentación.
"""

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

API_VERSION = "2022-11-28"
USER_AGENT = "github-pr-report"


class GitHubAPIError(Exception):
    def __init__(self, status: int, message: str, url: str = ""):
        super().__init__(f"GitHub API respondió {status}: {message}")
        self.status = status
        self.message = message
        self.url = url


class RepositoryNotFoundError(GitHubAPIError):
    def __init__(self, url: str):
        super().__init__(404, "repositorio no encontrado o sin acceso", url)


class RateLimitError(GitHubAPIError):
    def __init__(self, url: str, reset_at: Optional[str] = None):
        message = "límite de peticiones de la API de GitHub alcanzado"
        if reset_at:
            message += f" (se reinicia en {reset_at})"
        super().__init__(403, message, url)
        self.reset_at = reset_at


@dataclass
class HTTPResult:
    status: int
    body: bytes
    headers: Dict[str, str]


class UrllibTransport:
    """Transporte real usando únicamente la librería estándar."""

    def request(self, method: str, url: str, headers: Dict[str, str]) -> HTTPResult:
        req = urllib.request.Request(url, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as response:
                return HTTPResult(
                    status=response.status,
                    body=response.read(),
                    headers={k.lower(): v for k, v in response.headers.items()},
                )
        except urllib.error.HTTPError as error:
            return HTTPResult(
                status=error.code,
                body=error.read(),
                headers={k.lower(): v for k, v in error.headers.items()},
            )


def _extract_message(body: bytes) -> str:
    try:
        payload = json.loads(body)
        if isinstance(payload, dict) and "message" in payload:
            return str(payload["message"])
    except (json.JSONDecodeError, TypeError):
        pass
    return body.decode("utf-8", errors="replace")[:200]


def _next_link(link_header: Optional[str]) -> Optional[str]:
    if not link_header:
        return None
    for part in link_header.split(","):
        segment = part.strip()
        if segment.endswith('rel="next"'):
            start = segment.find("<")
            end = segment.find(">")
            if start != -1 and end != -1:
                return segment[start + 1 : end]
    return None


class GitHubClient:
    def __init__(
        self,
        token: Optional[str] = None,
        transport: Optional[Any] = None,
        base_url: str = "https://api.github.com",
        per_page: int = 100,
    ):
        self.token = token
        self.transport = transport or UrllibTransport()
        self.base_url = base_url.rstrip("/")
        self.per_page = per_page

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": USER_AGENT,
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _build_url(self, path: str, params: Optional[Dict[str, str]] = None) -> str:
        url = f"{self.base_url}{path}"
        if params:
            url = f"{url}?{urlencode(params)}"
        return url

    def _raise_for_status(self, result: HTTPResult, url: str) -> None:
        if 200 <= result.status < 300:
            return
        if result.status == 404:
            raise RepositoryNotFoundError(url)
        if result.status == 403 and result.headers.get("x-ratelimit-remaining") == "0":
            raise RateLimitError(url, result.headers.get("x-ratelimit-reset"))
        raise GitHubAPIError(result.status, _extract_message(result.body), url)

    def _get_paginated(self, path: str, params: Optional[Dict[str, str]] = None) -> List[Any]:
        url = self._build_url(path, params)
        items: List[Any] = []
        while url:
            result = self.transport.request("GET", url, self._headers())
            self._raise_for_status(result, url)
            payload = json.loads(result.body or b"[]")
            items.extend(payload)
            url = _next_link(result.headers.get("link"))
        return items

    def list_open_pull_requests(self, owner: str, repo: str) -> List[Any]:
        return self._get_paginated(
            f"/repos/{owner}/{repo}/pulls",
            {"state": "open", "per_page": str(self.per_page), "sort": "created", "direction": "asc"},
        )

    def list_pull_request_reviews(self, owner: str, repo: str, number: int) -> List[Any]:
        return self._get_paginated(
            f"/repos/{owner}/{repo}/pulls/{number}/reviews",
            {"per_page": str(self.per_page)},
        )
