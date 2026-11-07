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
