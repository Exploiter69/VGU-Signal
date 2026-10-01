from __future__ import annotations

import argparse
import json
from pathlib import Path


def unwrap(value: dict) -> list[dict]:
    if isinstance(value, list):
        return value[0].get("results", []) if value else []
    return value.get("results", [])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--submissions", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--objects", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    raw_submissions = json.loads(args.submissions.read_text(encoding="utf-8"))
    raw_archive = json.loads(args.archive.read_text(encoding="utf-8"))
    submissions = unwrap(raw_submissions)
    archive = unwrap(raw_archive)
    conflicts = []
    if isinstance(raw_archive, list) and len(raw_archive) > 1:
        conflicts = raw_archive[1].get("results", [])
    output = {"submissions": [], "archive": {"items": archive, "conflicts": conflicts}}

    for row in submissions:
        item = dict(row)
        if item.get("object_key"):
            object_path = args.objects / item["id"]
            item["object_file"] = str(object_path)
        output["submissions"].append(item)

    args.out.write_text(json.dumps(output, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
