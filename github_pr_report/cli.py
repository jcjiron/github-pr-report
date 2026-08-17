"""Capa externa: argumentos de línea de comandos, lectura del token,
impresión del reporte y código de salida del proceso.
"""

import argparse
import os
import sys
from typing import Optional, Sequence

from .client import GitHubClient
from .presentation import render_reports
from .service import build_reports

TOKEN_ENV_VAR = "GITHUB_TOKEN"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="github-pr-report",
        description="Reporte operativo de pull requests abiertos de GitHub.",
    )
    parser.add_argument(
        "--repo",
        action="append",
        required=True,
        dest="repos",
        metavar="URL",
        help="URL o slug owner/repo del repositorio. Repetir la opción para varios repos.",
    )
    return parser


def _read_token() -> Optional[str]:
    return os.environ.get(TOKEN_ENV_VAR)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    client = GitHubClient(token=_read_token())
    reports = build_reports(client, args.repos)

    print(render_reports(reports))

    return 1 if any(report.error for report in reports) else 0


if __name__ == "__main__":
    sys.exit(main())
