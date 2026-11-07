"""Genera documentación del modelo físico a partir de schema.sql."""

from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLES = (
    "import_batch", "dim_platform", "dim_account", "dim_project", "dim_content_type",
    "dim_date", "fact_post", "fact_metric_snapshot",
)


def generate() -> str:
    conn = sqlite3.connect(":memory:")
    conn.executescript((ROOT / "schema.sql").read_text(encoding="utf-8"))
    lines = ["# Modelo físico generado desde `schema.sql`", "", "```mermaid", "erDiagram"]
    for table in TABLES:
        lines.append(f"  {table} {{")
        for column in conn.execute(f"PRAGMA table_info({table})"):
            _, name, data_type, not_null, _, primary_key = column
            label = " PK" if primary_key else ""
            lines.append(f"    {data_type or 'TEXT'} {name}{label}")
        lines.append("  }")
    for table in TABLES:
        for fk in conn.execute(f"PRAGMA foreign_key_list({table})"):
            _, _, parent, source, _, *_ = fk
            lines.append(f"  {parent} ||--o{{ {table} : {source}")
    lines += ["```", "", "## Granularidad", "", "- `fact_post`: una fila por plataforma e ID de publicación.",
              "- `fact_metric_snapshot`: una fila por publicación y momento de captura.", ""]
    conn.close()
    return "\n".join(lines)


if __name__ == "__main__":
    target = ROOT / "docs" / "modelo_generado.md"
    target.write_text(generate(), encoding="utf-8")
    print(target)
