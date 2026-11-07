import csv
import json
import sqlite3
import shutil
from pathlib import Path

import pytest

from unidad2.pipeline import COLUMNS, import_batch
from unidad2.cloud_ingest import run as run_cloud_ingest
from unidad2.reports import filtered, load_posts, quality


def _fixture(tmp_path: Path, *, captured: str = "2026-10-10T15:00:00-05:00", likes: str = "5"):
    # Datos sintéticos solo en directorios temporales de prueba; nunca en el dashboard entregado.
    evidence = tmp_path / "exportacion-original.txt"
    evidence.write_text("exportación de prueba", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({
        "platform": "linkedin", "account_id": "cuenta-prueba", "account_label": "Equipo de prueba",
        "student_affiliation_evidence": "acta-prueba", "authorization_reference": "permiso-prueba",
        "source_kind": "official_export", "source_evidence_path": str(evidence),
        "exported_at": "2026-10-10T16:00:00-05:00",
    }), encoding="utf-8")
    data = tmp_path / "posts.csv"
    with data.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerow({
            "post_id": "post-1", "post_url": "https://www.linkedin.com/posts/cuenta-prueba_post-1",
            "published_at": "2026-10-09T15:00:00-05:00", "content_type": "Texto",
            "topic": "Proyecto", "project": "Proyecto de prueba", "likes": likes,
            "comments": "2", "shares": "", "reach": "", "impressions": "",
            "metrics_captured_at": captured,
        })
    return manifest, data


def test_import_is_idempotent_and_preserves_missing_metrics(tmp_path):
    manifest, data = _fixture(tmp_path)
    db = tmp_path / "warehouse.db"
    assert import_batch(manifest, data, db)["new_posts"] == 1
    assert import_batch(manifest, data, db)["status"] == "already_imported"
    posts = load_posts(db)
    assert len(posts) == 1
    assert int(posts.iloc[0]["likes"]) == 5
    assert posts.iloc[0]["shares"] is None or str(posts.iloc[0]["shares"]) == "None"
    assert quality(db)["snapshots"] == 1
    assert quality(db)["fk_errors"] == 0


def test_new_snapshot_replaces_report_value_without_double_counting(tmp_path):
    manifest, data = _fixture(tmp_path)
    db = tmp_path / "warehouse.db"
    import_batch(manifest, data, db)
    manifest, data = _fixture(tmp_path, captured="2026-10-11T15:00:00-05:00", likes="9")
    import_batch(manifest, data, db)
    posts = load_posts(db)
    assert len(posts) == 1
    assert int(posts.iloc[0]["likes"]) == 9
    assert quality(db)["snapshots"] == 2
    assert len(filtered(posts, year=2026, month=10, day=9)) == 1
    assert len(filtered(posts, year=2026, month=10, day=10)) == 0


def test_rejects_untraceable_or_contradictory_data(tmp_path):
    manifest, data = _fixture(tmp_path)
    db = tmp_path / "warehouse.db"
    import_batch(manifest, data, db)
    manifest, data = _fixture(tmp_path, likes="99")
    with pytest.raises(ValueError, match="contradictorias"):
        import_batch(manifest, data, db)
    assert quality(db)["batches"] == 1
    manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
    manifest_data["source_evidence_path"] = str(tmp_path / "ausente.csv")
    manifest.write_text(json.dumps(manifest_data), encoding="utf-8")
    with pytest.raises(ValueError, match="evidencia original"):
        import_batch(manifest, data, db)


def test_rejects_fake_platform_url(tmp_path):
    manifest, data = _fixture(tmp_path)
    content = data.read_text(encoding="utf-8").replace("www.linkedin.com", "www.example.com")
    data.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError, match="post_url"):
        import_batch(manifest, data, tmp_path / "warehouse.db")


def test_cloud_worker_imports_complete_batch_and_reports_missing_file(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    manifest, data = _fixture(source)
    store = {
        "incoming/valid/manifest.json": manifest,
        "incoming/valid/posts.csv": data,
        "incoming/valid/evidence.txt": source / "exportacion-original.txt",
        "incoming/incomplete/manifest.json": manifest,
    }
    metadata = json.loads(manifest.read_text(encoding="utf-8"))
    metadata["source_evidence_path"] = "evidence.txt"
    manifest.write_text(json.dumps(metadata), encoding="utf-8")

    class Paginator:
        def paginate(self, **kwargs):
            return [{"Contents": [{"Key": key} for key in store]}]

    class S3:
        def get_paginator(self, name):
            assert name == "list_objects_v2"
            return Paginator()

        def download_file(self, bucket, key, destination):
            shutil.copyfile(store[key], destination)

    monkeypatch.setattr("unidad2.cloud_ingest.boto3.client", lambda name: S3())
    result = run_cloud_ingest("bucket-de-prueba", tmp_path / "warehouse.db")
    assert result["imported"] == 1
    assert len(result["failed"]) == 1
    assert quality(tmp_path / "warehouse.db")["posts"] == 1


def test_public_capture_needs_no_account_permission_but_keeps_public_evidence(tmp_path):
    manifest, data = _fixture(tmp_path)
    metadata = json.loads(manifest.read_text(encoding="utf-8"))
    metadata["source_kind"] = "public_web_capture"
    metadata.pop("authorization_reference")
    metadata["public_source_url"] = "https://www.linkedin.com/posts/cuenta-prueba_post-1"
    metadata["student_affiliation_evidence"] = "https://www.example.edu/epis/equipo"
    manifest.write_text(json.dumps(metadata), encoding="utf-8")
    db = tmp_path / "warehouse.db"
    assert import_batch(manifest, data, db)["status"] == "imported"
    post = load_posts(db).iloc[0]
    assert post["source_kind"] == "public_web_capture"
    assert post["public_source_url"] == metadata["public_source_url"]


def test_relative_dates_remain_unknown_and_capture_filters_are_explicit(tmp_path):
    manifest, data = _fixture(tmp_path)
    with data.open(encoding="utf-8", newline="") as file:
        row = next(csv.DictReader(file))
    row.update(published_at="", published_label="3 sem")
    with data.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=[*COLUMNS, "published_label"])
        writer.writeheader()
        writer.writerow(row)
    db = tmp_path / "warehouse.db"
    import_batch(manifest, data, db)
    posts = load_posts(db)
    assert posts.iloc[0]["published_at"] is None
    assert posts.iloc[0]["date_key"] is None
    assert posts.iloc[0]["published_label"] == "3 sem"
    assert filtered(posts, year=2026).empty
    assert len(filtered(posts, year=2026, month=10, day=10, date_basis="capture")) == 1
    # Una evidencia posterior con fecha exacta puede completar el dato sin duplicar el post.
    manifest, data = _fixture(tmp_path, captured="2026-10-11T15:00:00-05:00")
    import_batch(manifest, data, db)
    posts = load_posts(db)
    assert len(posts) == 1
    assert posts.iloc[0]["date_key"] == "2026-10-09"
    assert quality(db)["snapshots"] == 2


def test_snapshot_order_uses_instant_not_original_timezone_text(tmp_path):
    manifest, data = _fixture(tmp_path, captured="2026-10-10T23:30:00+09:00", likes="5")
    db = tmp_path / "warehouse.db"
    import_batch(manifest, data, db)
    manifest, data = _fixture(tmp_path, captured="2026-10-10T10:00:00-05:00", likes="8")
    import_batch(manifest, data, db)
    assert load_posts(db).iloc[0]["likes"] == 8
    manifest, data = _fixture(tmp_path, captured="2026-10-10T15:00:00Z", likes="9")
    with pytest.raises(ValueError, match="contradictorias"):
        import_batch(manifest, data, db)


def test_schema_migration_preserves_existing_posts_and_snapshots(tmp_path):
    from unidad2.database import SCHEMA, initialize
    manifest, data = _fixture(tmp_path)
    db = tmp_path / "warehouse.db"
    # Recrear la versión anterior sin la columna de fecha relativa.
    schema = SCHEMA.read_text(encoding="utf-8").replace("    published_label TEXT,\n", "")
    schema = schema.replace("p.published_at, p.published_label,", "p.published_at,")
    schema = schema.replace("date_key TEXT REFERENCES", "date_key TEXT NOT NULL REFERENCES")
    schema = schema.replace("published_at TEXT,", "published_at TEXT NOT NULL,")
    with sqlite3.connect(db) as conn:
        conn.executescript(schema)
        # Primera migración sin datos y posterior carga prueba la compatibilidad del importador.
        initialize(conn)
    import_batch(manifest, data, db)
    with sqlite3.connect(db) as conn:
        conn.execute("DROP VIEW report_post_latest")
        conn.execute("ALTER TABLE fact_post DROP COLUMN published_label")
    posts = load_posts(db)
    assert len(posts) == 1
    assert posts.iloc[0]["likes"] == 5
    assert quality(db)["snapshots"] == 1
    assert quality(db)["fk_errors"] == 0


def test_structured_observation_rejects_metrics_changed_in_csv(tmp_path):
    manifest, data = _fixture(tmp_path)
    metadata = json.loads(manifest.read_text(encoding="utf-8"))
    metadata["evidence_format"] = "epis_observation_v1"
    evidence = {"account_id": metadata["account_id"], "captured_at": "2026-10-10T15:00:00-05:00",
                "observations": [{"post_id": "post-1", "post_url": "https://www.linkedin.com/posts/cuenta-prueba_post-1", "likes": 4}]}
    Path(metadata["source_evidence_path"]).write_text(json.dumps(evidence), encoding="utf-8")
    manifest.write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(ValueError, match="likes no coincide"):
        import_batch(manifest, data, tmp_path / "warehouse.db")


def test_vps_inbox_imports_real_format_without_aws_and_reports_incomplete_batch(tmp_path):
    from unidad2.inbox_ingest import run
    inbox = tmp_path / "inbox"
    valid = inbox / "valid"
    valid.mkdir(parents=True)
    _fixture(valid)
    incomplete = inbox / "incomplete"
    incomplete.mkdir()
    shutil.copyfile(valid / "manifest.json", incomplete / "manifest.json")
    db = tmp_path / "warehouse.db"
    result = run(inbox, db)
    assert result["imported"] == 1
    assert len(result["failed"]) == 1
    assert run(inbox, db)["already_imported"] == 1
