from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def unwrap(value: object) -> list[dict]:
    if isinstance(value, list):
        return value[0].get("results", []) if value else []
    if isinstance(value, dict):
        return value.get("results", [])
    return []


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--submissions", type=Path, required=True)
    parser.add_argument("--objects", type=Path, required=True)
    args = parser.parse_args()

    rows = unwrap(json.loads(args.submissions.read_text(encoding="utf-8")))
    ids = [str(row["id"]) for row in rows if row.get("object_key")]
    if not ids:
        return

    quoted = ",".join("'" + value.replace("'", "''") + "'" for value in ids)
    command = (
        "SELECT submission_id, chunk_index, hex(data) AS data_hex "
        f"FROM verification_submission_blobs WHERE submission_id IN ({quoted}) "
        "ORDER BY submission_id, chunk_index"
    )
    result = subprocess.run(
        [
            "npx",
            "wrangler",
            "--config",
            "worker/wrangler.toml",
            "d1",
            "execute",
            "vgu-signal",
            "--remote",
            "--json",
            "--command",
            command,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    chunks = unwrap(json.loads(result.stdout))
    handles: dict[str, object] = {}
    try:
        for row in chunks:
            submission_id = str(row["submission_id"])
            path = args.objects / submission_id
            path.parent.mkdir(parents=True, exist_ok=True)
            handle = handles.get(submission_id)
            if handle is None:
                handle = path.open("wb")
                handles[submission_id] = handle
            handle.write(bytes.fromhex(str(row["data_hex"])))
    finally:
        for handle in handles.values():
            handle.close()


if __name__ == "__main__":
    main()
