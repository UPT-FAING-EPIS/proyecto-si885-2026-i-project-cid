"""Carga transaccional de exportaciones autorizadas al almacén dimensional."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlparse

from unidad2.database import initialize

PERU = timezone(timedelta(hours=-5))

ROOT = Path(__file__).resolve().parent
COLUMNS = (
    "post_id", "post_url", "published_at", "content_type", "topic", "project",
    "likes", "comments", "shares", "reach", "impressions", "metrics_captured_at",
)
METRICS = ("likes", "comments", "shares", "reach", "impressions")
HOSTS = {
    "facebook": ("facebook.com", "fb.com"),
    "instagram": ("instagram.com",),
    "linkedin": ("linkedin.com",),
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _timestamp(value: str, field: str) -> datetime:
    try:
        result = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"{field}: fecha ISO 8601 inválida") from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError(f"{field}: falta zona horaria")
    return result.astimezone(PERU)


def _required(value: object, field: str) -> str:
    result = str(value or "").strip()
    if not result or result.upper().startswith("REEMPLAZAR"):
        raise ValueError(f"{field}: valor obligatorio y verificable")
    return result


def _metric(value: str | None, field: str) -> int | None:
    if value is None or not value.strip():
        return None
    try:
        number = int(value)
    except ValueError as exc:
        raise ValueError(f"{field}: se esperaba entero no negativo o vacío") from exc
    if number < 0:
        raise ValueError(f"{field}: no puede ser negativo")
    return number


def _valid_url(value: str, platform: str) -> str:
    url = _required(value, "post_url")
    parts = urlparse(url)
    host = (parts.hostname or "").lower()
    if parts.scheme != "https" or not any(host == domain or host.endswith("." + domain) for domain in HOSTS[platform]):
        raise ValueError(f"post_url: debe ser HTTPS de {platform}")
    if not parts.path or parts.path == "/":
        raise ValueError("post_url: falta ruta de publicación")
    return url


def _read_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("Manifiesto: se esperaba un objeto JSON")
    platform = _required(manifest.get("platform"), "platform").lower()
    if platform not in HOSTS:
        raise ValueError("platform: usar facebook, instagram o linkedin")
    manifest["platform"] = platform
    for field in ("account_id", "account_label", "student_affiliation_evidence", "source_kind", "source_evidence_path", "exported_at"):
        manifest[field] = _required(manifest.get(field), field)
    if manifest["source_kind"] not in ("official_export", "authorized_api", "public_web_capture"):
        raise ValueError("source_kind: usar official_export, authorized_api o public_web_capture")
    if manifest["source_kind"] == "public_web_capture":
        manifest["public_source_url"] = _valid_url(_required(manifest.get("public_source_url"), "public_source_url"), platform)
        affiliation = urlparse(manifest["student_affiliation_evidence"])
        if affiliation.scheme != "https" or not affiliation.hostname:
            raise ValueError("student_affiliation_evidence: se requiere URL pública verificable")
        manifest["authorization_reference"] = None
    else:
        manifest["authorization_reference"] = _required(manifest.get("authorization_reference"), "authorization_reference")
        manifest["public_source_url"] = None
    manifest["exported_at"] = _timestamp(manifest["exported_at"], "exported_at").isoformat()
    evidence = Path(manifest["source_evidence_path"])
    if not evidence.is_absolute():
        evidence = (path.parent / evidence).resolve()
    if not evidence.is_file():
        raise ValueError(f"No existe la evidencia original: {evidence}")
    manifest["evidence_sha256"] = _sha256(evidence)
    manifest["evidence_path"] = evidence
    return manifest


def _validate_observation(manifest: dict, rows: list[dict]) -> None:
    """Conciliar transcripciones estructuradas con el CSV; el hash no prueba veracidad."""
    if manifest.get("evidence_format") != "epis_observation_v1":
        return
    evidence = json.loads(manifest["evidence_path"].read_text(encoding="utf-8"))
    if evidence.get("account_id") != manifest["account_id"]:
        raise ValueError("Evidencia: cuenta contradictoria")
    observations = {item["post_id"]: item for item in evidence["observations"]}
    for row in rows:
        item = observations.get(row["post_id"])
        if item is None or item["post_url"] != row["post_url"]:
            raise ValueError("Evidencia: publicación o URL no conciliada")
        if _timestamp(evidence["captured_at"], "captured_at").isoformat() != row["captured_at"]:
            raise ValueError("Evidencia: fecha de captura no conciliada")
        for metric in METRICS:
            if item.get(metric) != row[metric]:
                raise ValueError(f"Evidencia: {metric} no coincide con la observación")
        observed_date = item.get("published_at")
        normalized = _timestamp(observed_date, "published_at").isoformat() if observed_date else None
        if normalized != row["published_at"] or item.get("published_label") != row["published_label"]:
            raise ValueError("Evidencia: fecha de publicación no conciliada")


def _read_rows(path: Path, platform: str) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames or set(COLUMNS) - set(reader.fieldnames):
            raise ValueError("CSV: faltan columnas: " + ", ".join(sorted(set(COLUMNS) - set(reader.fieldnames or []))))
        rows = []
        seen = set()
        for line, raw in enumerate(reader, start=2):
            post_id = _required(raw.get("post_id"), f"línea {line} post_id")
            captured = _timestamp(_required(raw.get("metrics_captured_at"), f"línea {line} metrics_captured_at"), "metrics_captured_at")
            published_raw = (raw.get("published_at") or "").strip()
            published = _timestamp(published_raw, "published_at") if published_raw else None
            label = (raw.get("published_label") or "").strip()
            if published is None and not label:
                raise ValueError(f"línea {line}: falta published_at o published_label observado")
            if published is not None and captured < published:
                raise ValueError(f"línea {line}: captura anterior a publicación")
            key = (post_id, captured.isoformat())
            if key in seen:
                raise ValueError(f"línea {line}: instantánea duplicada")
            seen.add(key)
            item = {
                "post_id": post_id,
                "post_url": _valid_url(raw.get("post_url") or "", platform),
                "published_at": published.isoformat() if published else None,
                "published_label": label or None,
                "date_key": published.date().isoformat() if published else None,
                "captured_at": captured.isoformat(),
                "content_type": (raw.get("content_type") or "").strip(),
                "topic": (raw.get("topic") or "").strip(),
                "project": (raw.get("project") or "").strip(),
            }
            item.update({field: _metric(raw.get(field), f"línea {line} {field}") for field in METRICS})
            rows.append(item)
    if not rows:
        raise ValueError("CSV: no contiene publicaciones; no se cargarán datos de ejemplo")
    return rows


def _dimension(conn: sqlite3.Connection, table: str, name: str) -> int:
    conn.execute(f"INSERT OR IGNORE INTO {table}(name) VALUES (?)", (name,))
    return conn.execute(f"SELECT id FROM {table} WHERE name = ?", (name,)).fetchone()[0]


def import_batch(manifest_path: str | Path, csv_path: str | Path, db_path: str | Path) -> dict:
    manifest_path, csv_path, db_path = map(Path, (manifest_path, csv_path, db_path))
    manifest = _read_manifest(manifest_path)
    rows = _read_rows(csv_path, manifest["platform"])
    _validate_observation(manifest, rows)
    source_sha = _sha256(csv_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        initialize(conn)
        existing = conn.execute(
            "SELECT id,evidence_sha256 FROM import_batch WHERE source_sha256=? AND platform=? AND account_id=?",
            (source_sha, manifest["platform"], manifest["account_id"]),
        ).fetchone()
        if existing:
            if existing[1] != manifest["evidence_sha256"]:
                raise ValueError("El CSV ya existe pero cambió su evidencia original")
            return {"status": "already_imported", "batch_id": existing[0], "rows": len(rows)}
        with conn:
            cur = conn.execute(
                """INSERT INTO import_batch
                (source_sha256,evidence_sha256,platform,account_id,account_label,source_kind,
                 authorization_reference,public_source_url,affiliation_evidence,exported_at,imported_at,row_count)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (source_sha, manifest["evidence_sha256"], manifest["platform"], manifest["account_id"],
                 manifest["account_label"], manifest["source_kind"], manifest["authorization_reference"],
                 manifest["public_source_url"],
                 manifest["student_affiliation_evidence"], manifest["exported_at"],
                 datetime.now(timezone.utc).isoformat(), len(rows)),
            )
            batch_id = cur.lastrowid
            platform_id = _dimension(conn, "dim_platform", manifest["platform"])
            conn.execute(
                "INSERT OR IGNORE INTO dim_account(platform_id,external_id,label) VALUES (?,?,?)",
                (platform_id, manifest["account_id"], manifest["account_label"]),
            )
            account_id = conn.execute(
                "SELECT id FROM dim_account WHERE platform_id=? AND external_id=?",
                (platform_id, manifest["account_id"]),
            ).fetchone()[0]
            inserted_posts = inserted_snapshots = 0
            for row in rows:
                if row["published_at"]:
                    date = datetime.fromisoformat(row["published_at"])
                    conn.execute(
                        "INSERT OR IGNORE INTO dim_date(date_key,year,month,day) VALUES (?,?,?,?)",
                        (row["date_key"], date.year, date.month, date.day),
                    )
                project_id = _dimension(conn, "dim_project", row["project"]) if row["project"] else None
                content_id = _dimension(conn, "dim_content_type", row["content_type"]) if row["content_type"] else None
                cur = conn.execute(
                    """INSERT OR IGNORE INTO fact_post
                    (platform_id,account_id,project_id,content_type_id,date_key,external_id,post_url,published_at,published_label,topic,first_batch_id)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (platform_id, account_id, project_id, content_id, row["date_key"], row["post_id"],
                     row["post_url"], row["published_at"], row["published_label"], row["topic"], batch_id),
                )
                inserted_posts += cur.rowcount
                post = conn.execute(
                    "SELECT id,account_id,post_url,published_at FROM fact_post WHERE platform_id=? AND external_id=?",
                    (platform_id, row["post_id"]),
                ).fetchone()
                if post[1:3] != (account_id, row["post_url"]):
                    raise ValueError(f"Post {row['post_id']}: identidad o URL contradictoria")
                if post[3] and row["published_at"] and _timestamp(post[3], "published_at").isoformat() != row["published_at"]:
                    raise ValueError(f"Post {row['post_id']}: fecha de publicación contradictoria")
                if post[3] is None and row["published_at"]:
                    conn.execute("UPDATE fact_post SET published_at=?,date_key=? WHERE id=?",
                                 (row["published_at"], row["date_key"], post[0]))
                old = conn.execute(
                    """SELECT likes,comments,shares,reach,impressions FROM fact_metric_snapshot
                    WHERE post_id=? AND captured_at=?""", (post[0], row["captured_at"]),
                ).fetchone()
                metrics = tuple(row[field] for field in METRICS)
                if old is not None and old != metrics:
                    raise ValueError(f"Post {row['post_id']}: métricas contradictorias para la misma captura")
                if old is None:
                    conn.execute(
                        """INSERT INTO fact_metric_snapshot
                        (post_id,captured_at,likes,comments,shares,reach,impressions,batch_id)
                        VALUES (?,?,?,?,?,?,?,?)""",
                        (post[0], row["captured_at"], *metrics, batch_id),
                    )
                    inserted_snapshots += 1
        return {"status": "imported", "batch_id": batch_id, "rows": len(rows),
                "new_posts": inserted_posts, "new_snapshots": inserted_snapshots}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--csv", required=True)
    parser.add_argument("--db", default=str(ROOT / "data" / "observatorio.db"))
    args = parser.parse_args()
    print(json.dumps(import_batch(args.manifest, args.csv, args.db), ensure_ascii=False))


if __name__ == "__main__":
    main()
