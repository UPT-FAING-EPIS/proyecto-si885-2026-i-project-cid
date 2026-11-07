"""Inicialización y migración conservadora del almacén local."""

import sqlite3
from pathlib import Path

SCHEMA = Path(__file__).with_name("schema.sql")


def initialize(conn: sqlite3.Connection) -> None:
    schema = SCHEMA.read_text(encoding="utf-8")
    columns = {row[1] for row in conn.execute("PRAGMA table_info(fact_post)")}
    if columns and "published_label" not in columns:
        # Reconstruir únicamente fact_post: SQLite no permite quitar NOT NULL.
        # Conservar IDs mantiene intactas las referencias de las instantáneas.
        conn.execute("PRAGMA foreign_keys=OFF")
        try:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("DROP VIEW IF EXISTS report_post_latest")
            definition = schema.split("CREATE TABLE IF NOT EXISTS fact_post (", 1)[1].split(";", 1)[0]
            conn.execute("CREATE TABLE fact_post_v2 (" + definition)
            fields = "id,platform_id,account_id,project_id,content_type_id,date_key,external_id,post_url,published_at,topic,first_batch_id"
            conn.execute(f"INSERT INTO fact_post_v2 ({fields}) SELECT {fields} FROM fact_post")
            conn.execute("DROP TABLE fact_post")
            conn.execute("ALTER TABLE fact_post_v2 RENAME TO fact_post")
            if conn.execute("PRAGMA foreign_key_check").fetchall():
                raise ValueError("La migración no conserva la integridad referencial")
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(schema)
