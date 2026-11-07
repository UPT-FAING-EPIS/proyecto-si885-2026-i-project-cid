"""Consultas de reporte; todas las cifras proceden del almacén."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from unidad2.database import initialize

SCHEMA = Path(__file__).with_name("schema.sql")


def load_posts(db_path: str | Path) -> pd.DataFrame:
    path = Path(db_path)
    if not path.exists():
        return pd.DataFrame()
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        initialize(conn)
        return pd.read_sql_query("SELECT * FROM report_post_latest ORDER BY date_key DESC, id DESC", conn)


def quality(db_path: str | Path) -> dict:
    path = Path(db_path)
    if not path.exists():
        return {"batches": 0, "posts": 0, "snapshots": 0, "missing_metrics": 0, "fk_errors": 0, "last_import": None}
    with sqlite3.connect(path) as conn:
        batches, last_import = conn.execute("SELECT COUNT(*),MAX(imported_at) FROM import_batch").fetchone()
        posts = conn.execute("SELECT COUNT(*) FROM fact_post").fetchone()[0]
        snapshots = conn.execute("SELECT COUNT(*) FROM fact_metric_snapshot").fetchone()[0]
        missing = conn.execute(
            """SELECT COUNT(*) FROM report_post_latest
            WHERE likes IS NULL OR comments IS NULL OR shares IS NULL OR reach IS NULL OR impressions IS NULL"""
        ).fetchone()[0]
        fk_errors = len(conn.execute("PRAGMA foreign_key_check").fetchall())
    return {"batches": batches, "posts": posts, "snapshots": snapshots,
            "missing_metrics": missing, "fk_errors": fk_errors, "last_import": last_import}


def filtered(df: pd.DataFrame, year: int | None = None, month: int | None = None,
             day: int | None = None, platform: str | None = None,
             date_basis: str = "publication") -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    if date_basis not in ("publication", "capture"):
        raise ValueError("date_basis: publication o capture")
    if date_basis == "capture":
        dates = pd.to_datetime(df["metrics_captured_at"], utc=True).dt.tz_convert("America/Lima")
        df["year"], df["month"], df["day"] = dates.dt.year, dates.dt.month, dates.dt.day
        df["analysis_date"] = dates.dt.strftime("%Y-%m-%d")
    else:
        df["analysis_date"] = df["date_key"]
    mask = pd.Series(True, index=df.index)
    for column, value in (("year", year), ("month", month), ("day", day), ("platform", platform)):
        if value is not None:
            mask &= df[column] == value
    return df.loc[mask].copy()
