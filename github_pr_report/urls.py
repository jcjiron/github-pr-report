"""Parseo y validación local de URLs/slugs de repositorio de GitHub.

No hace llamadas de red: solo extrae ``(owner, repo)`` del texto que llega
por ``--repo``.
"""

import re
from typing import Tuple

_SLUG_RE = re.compile(r"^(?P<owner>[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)/(?P<repo>[A-Za-z0-9_.-]+)$")

_HTTPS_RE = re.compile(
    r"^https?://(www\.)?github\.com/"
    r"(?P<owner>[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)/"
    r"(?P<repo>[A-Za-z0-9_.-]+?)"
    r"(\.git)?/?$"
)

_SSH_RE = re.compile(
    r"^git@github\.com:"
    r"(?P<owner>[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)/"
    r"(?P<repo>[A-Za-z0-9_.-]+?)"
    r"(\.git)?$"
)


class InvalidRepositoryURLError(ValueError):
    def __init__(self, value: str):
        super().__init__(f"URL de repositorio inválida: {value!r}")
        self.value = value


def parse_repo(value: str) -> Tuple[str, str]:
    """Devuelve ``(owner, repo)`` a partir de una URL de GitHub o de un slug
    ``owner/repo``. Lanza :class:`InvalidRepositoryURLError` si el texto no
    coincide con ninguno de los formatos soportados.
    """
    text = value.strip()
    if not text:
        raise InvalidRepositoryURLError(value)

    for pattern in (_HTTPS_RE, _SSH_RE, _SLUG_RE):
        match = pattern.match(text)
        if match:
            owner = match.group("owner")
            repo = match.group("repo")
            if repo.endswith(".git"):
                repo = repo[: -len(".git")]
            return owner, repo

    raise InvalidRepositoryURLError(value)
