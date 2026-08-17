"""Render de tablas en terminal. Solo formato: recibe ``RepositoryReport``
ya calculados y devuelve strings. No hace cálculos de negocio.
"""

from typing import Iterable, List, Sequence, Tuple

from .models import PullRequestRow, RepositoryReport

_HEADERS: Tuple[str, ...] = ("#", "Título", "Autor", "Antigüedad", "Approval pendiente", "Versión destino")


def _row_values(row: PullRequestRow) -> Tuple[str, ...]:
    return (
        str(row.number),
        row.title,
        row.author,
        f"{row.age_days}d",
        row.pending_approval,
        row.target_version,
    )


def _format_table(rows: Sequence[PullRequestRow]) -> str:
    data_rows = [_row_values(row) for row in rows]
    all_rows = [_HEADERS] + data_rows
    widths = [max(len(str(row[i])) for row in all_rows) for i in range(len(_HEADERS))]

    def format_row(values: Sequence[str]) -> str:
        return "  ".join(str(value).ljust(widths[i]) for i, value in enumerate(values))

    lines = [format_row(_HEADERS), "  ".join("-" * width for width in widths)]
    lines.extend(format_row(values) for values in data_rows)
    return "\n".join(lines)


def render_report(report: RepositoryReport) -> str:
    lines = [f"## {report.repository}"]
    if report.error:
        lines.append(f"ERROR: {report.error}")
    elif not report.rows:
        lines.append("Sin PRs abiertos.")
    else:
        lines.append(_format_table(report.rows))
    return "\n".join(lines)


def render_reports(reports: Iterable[RepositoryReport]) -> str:
    return "\n\n".join(render_report(report) for report in reports)
