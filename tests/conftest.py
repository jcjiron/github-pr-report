"""Utilidades compartidas por la suite: carga de fixtures y transporte falso.

Ningún test de este proyecto usa la red, un token real ni un repositorio real.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

import pytest

from github_pr_report.client import HTTPResult

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> Any:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def make_result(status: int, payload: Any, headers: Optional[Dict[str, str]] = None) -> HTTPResult:
    body = payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")
    return HTTPResult(status=status, body=body, headers={k.lower(): v for k, v in (headers or {}).items()})


class FakeTransport:
    """Responde según un diccionario ``url -> HTTPResult`` fijado de antemano."""

    def __init__(self, responses: Dict[str, HTTPResult]):
        self._responses = responses
        self.requests = []

    def request(self, method: str, url: str, headers: Dict[str, str]) -> HTTPResult:
        self.requests.append((method, url, headers))
        try:
            return self._responses[url]
        except KeyError:
            raise AssertionError(f"Petición inesperada a {url}")


@pytest.fixture
def fixture_loader():
    return load_fixture
