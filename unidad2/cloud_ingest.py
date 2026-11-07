"""Importa lotes reales desde un bucket S3 privado, sin credenciales en código."""

from __future__ import annotations

import argparse
import json
import logging
import os
import tempfile
from pathlib import Path

import boto3

from unidad2.pipeline import import_batch

LOG = logging.getLogger("epis_cloud_ingest")


def run(bucket: str, db: str | Path, prefix: str = "incoming/") -> dict:
    """Cada subcarpeta debe contener manifest.json, posts.csv y la evidencia referida."""
    s3 = boto3.client("s3")
    paginator = s3.get_paginator("list_objects_v2")
    keys = [obj["Key"] for page in paginator.paginate(Bucket=bucket, Prefix=prefix)
            for obj in page.get("Contents", [])]
    batches = sorted({key.rsplit("/", 1)[0] + "/" for key in keys if key.endswith("/manifest.json")})
    results = {"found": len(batches), "imported": 0, "already_imported": 0, "failed": []}
    for batch in batches:
        batch_keys = [key for key in keys if key.startswith(batch) and not key.endswith("/")]
        if batch + "posts.csv" not in batch_keys:
            results["failed"].append({"batch": batch, "error": "Falta posts.csv"})
            continue
        try:
            with tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                for key in batch_keys:
                    relative = Path(key.removeprefix(batch))
                    if relative.is_absolute() or ".." in relative.parts:
                        raise ValueError("Ruta insegura en bucket")
                    destination = directory / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    s3.download_file(bucket, key, str(destination))
                manifest = directory / "manifest.json"
                metadata = json.loads(manifest.read_text(encoding="utf-8"))
                evidence = Path(metadata.get("source_evidence_path", ""))
                if evidence.is_absolute() or ".." in evidence.parts:
                    raise ValueError("La evidencia debe estar dentro del lote S3")
                result = import_batch(manifest, directory / "posts.csv", db)
                results[result["status"]] += 1
        except Exception as exc:
            LOG.exception("Falló el lote %s", batch)
            results["failed"].append({"batch": batch, "error": str(exc)})
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bucket", default=os.environ.get("EPIS_SOURCE_BUCKET"), required=False)
    parser.add_argument("--db", default=os.environ.get("EPIS_DB_PATH", "/app/unidad2/data/observatorio.db"))
    args = parser.parse_args()
    if not args.bucket:
        parser.error("Falta --bucket o EPIS_SOURCE_BUCKET")
    logging.basicConfig(level=logging.INFO)
    result = run(args.bucket, args.db)
    print(json.dumps(result, ensure_ascii=False))
    if result["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
