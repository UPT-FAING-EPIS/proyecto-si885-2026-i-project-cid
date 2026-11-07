"""ETL de lotes depositados en una carpeta; utilizable en un VPS sin AWS."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from unidad2.pipeline import import_batch


def run(inbox: str | Path, db: str | Path) -> dict:
    root = Path(inbox)
    if not root.is_dir():
        raise ValueError("No existe la carpeta de entrada")
    manifests = sorted(root.rglob("manifest.json"))
    result = {"found": len(manifests), "imported": 0, "already_imported": 0, "failed": []}
    for manifest in manifests:
        try:
            outcome = import_batch(manifest, manifest.with_name("posts.csv"), db)
            result[outcome["status"]] += 1
        except Exception as exc:
            result["failed"].append({"batch": str(manifest.parent.relative_to(root)), "error": str(exc)})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inbox", required=True)
    parser.add_argument("--db", required=True)
    args = parser.parse_args()
    result = run(args.inbox, args.db)
    print(json.dumps(result, ensure_ascii=False))
    if result["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
