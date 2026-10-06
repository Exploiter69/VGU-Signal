from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from vgu_signal.acquisition import AcquisitionEngine, HttpFetcher, InMemoryEvidenceStore
from vgu_signal.extraction import extract_evidence
from vgu_signal.information import (
    InformationCategory,
    build_information_item,
    information_item_id,
)
from vgu_signal.sources.registry import SOURCES
from vgu_signal.verification import claims_from_document, verify_claim
from vgu_signal.verification.models import VerificationState

MAX_DOCUMENT_TEXT = 1_500_000
MAX_SQL_BYTES = 80_000

_DISABLED_INFORMATION_SOURCE_URLS = (
    "https://vgu.ac.in/resources/handbook-brochures",
    "https://vgu.ac.in/admission/fee-structure",
    "https://vgu.ac.in/campus-life/events",
)


def sql(value: object) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def iso(value: datetime | None) -> str | None:
    return value.astimezone(UTC).isoformat() if value else None


def insert(table: str, columns: tuple[str, ...], values: tuple[object, ...]) -> str:
    rendered = ",".join(sql(value) for value in values)
    return f"INSERT OR REPLACE INTO {table}({','.join(columns)}) VALUES({rendered});"


def info_category(value: str) -> InformationCategory:
    return {
        "ACADEMIC": InformationCategory.CALENDAR,
        "EXAMINATION": InformationCategory.EXAM,
        "FEES": InformationCategory.FEES,
        "REGISTRATION": InformationCategory.REGISTRATION,
        "EVENT": InformationCategory.EVENT,
        "HOLIDAY": InformationCategory.HOLIDAY,
        "GENERAL": InformationCategory.NOTICE,
        "UNKNOWN": InformationCategory.NOTICE,
    }[value.upper()]


def write_sql(statements: list[str], root: Path) -> None:
    sql_dir = root / "sql"
    sql_dir.mkdir(parents=True, exist_ok=True)
    chunk: list[str] = []
    size = 0
    number = 1

    for statement in statements:
        cost = len(statement.encode("utf-8")) + 1
        if chunk and size + cost > MAX_SQL_BYTES:
            (sql_dir / f"{number:04d}.sql").write_text("\n".join(chunk) + "\n", encoding="utf-8")
            number += 1
            chunk, size = [], 0
        chunk.append(statement)
        size += cost

    if chunk:
        (sql_dir / f"{number:04d}.sql").write_text("\n".join(chunk) + "\n", encoding="utf-8")


def run(root: Path) -> int:
    root.mkdir(parents=True, exist_ok=True)
    evidence_dir = root / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    started = datetime.now(UTC)
    enabled = [source for source in SOURCES.values() if source.enabled]
    fetcher = HttpFetcher(
        timeout_seconds=20,
        max_bytes=10 * 1024 * 1024,
        max_retries=2,
        retry_base_seconds=1.0,
        min_interval_seconds=1.0,
    )
    engine = AcquisitionEngine(fetcher, InMemoryEvidenceStore())
    statements: list[str] = []
    manifest: list[dict[str, object]] = []
    failed = fetched = changed = 0

    for source in enabled:
        result = engine.acquire(source)
        now = datetime.now(UTC)
        if result.status.value == "FAILED" or result.evidence is None:
            failed += 1
            manifest.append({"source_id": source.id, "status": "FAILED", "error": result.error})
            continue

        fetched += 1
        if result.status.value == "CHANGED":
            changed += 1
        evidence = result.evidence
        body = result.raw_body or b""
        object_key = f"d1://evidence/{evidence.id}"
        (evidence_dir / f"{source.id}-{evidence.raw_content_hash}.bin").write_bytes(body)

        chunk_size = 32 * 1024
        evidence_blob_statements: list[str] = []
        for chunk_index, start in enumerate(range(0, len(body), chunk_size)):
            chunk = body[start : start + chunk_size]
            evidence_blob_statements.append(
                f"INSERT OR REPLACE INTO evidence_blobs(evidence_id,chunk_index,data) "
                f"VALUES({sql(evidence.id)},{chunk_index},X'{chunk.hex()}');"
            )

        statements.append(
            insert(
                "sources",
                (
                    "id",
                    "name",
                    "url",
                    "source_class",
                    "enabled",
                    "created_at",
                    "updated_at",
                ),
                (
                    source.id,
                    source.name,
                    str(source.url),
                    source.source_class.value,
                    1,
                    iso(now),
                    iso(now),
                ),
            ).replace(";", "")
            + " ON CONFLICT(id) DO UPDATE SET name=excluded.name,"
            "url=excluded.url,source_class=excluded.source_class,"
            "enabled=excluded.enabled,updated_at=excluded.updated_at;"
        )
        statements.append(
            insert(
                "evidence",
                (
                    "id",
                    "source_id",
                    "source_url",
                    "fetched_at",
                    "http_status",
                    "content_type",
                    "raw_content_hash",
                    "raw_content_ref",
                    "http_last_modified",
                    "http_etag",
                ),
                (
                    evidence.id,
                    evidence.source_id,
                    str(evidence.source_url),
                    iso(evidence.fetched_at),
                    evidence.http_status,
                    evidence.content_type,
                    evidence.raw_content_hash,
                    object_key,
                    evidence.http_last_modified,
                    evidence.http_etag,
                ),
            ).replace("INSERT OR REPLACE", "INSERT OR IGNORE")
        )
        statements.extend(evidence_blob_statements)

        document = extract_evidence(
            evidence_id=evidence.id,
            source_id=source.id,
            url=str(source.url),
            content_type=evidence.content_type,
            body=body,
        )
        document = document.model_copy(update={"body_text": document.body_text[:MAX_DOCUMENT_TEXT]})
        statements.append(
            insert(
                "documents",
                (
                    "id",
                    "evidence_id",
                    "source_id",
                    "canonical_url",
                    "title",
                    "published_at",
                    "body_text",
                    "parser_version",
                    "state",
                    "created_at",
                    "updated_at",
                ),
                (
                    document.id,
                    document.evidence_id,
                    document.source_id,
                    str(document.canonical_url),
                    document.title,
                    iso(document.published_at),
                    document.body_text,
                    document.parser_version,
                    "PARSED",
                    iso(now),
                    iso(now),
                ),
            )
        )

        for claim in claims_from_document(document, evidence.raw_content_hash, evidence.fetched_at):
            decision = verify_claim(claim, [evidence.id], evidence.fetched_at)
            verified = claim.model_copy(update={"state": VerificationState.VERIFIED})
            statements.append(
                insert(
                    "claims",
                    (
                        "id",
                        "document_id",
                        "evidence_id",
                        "source_id",
                        "statement",
                        "normalized_statement",
                        "fingerprint",
                        "state",
                        "first_seen_at",
                        "last_seen_at",
                        "effective_from",
                        "effective_until",
                    ),
                    (
                        verified.id,
                        verified.document_id,
                        verified.evidence_id,
                        verified.source_id,
                        verified.statement,
                        verified.normalized_statement,
                        verified.fingerprint,
                        decision.state.value,
                        iso(verified.first_seen_at),
                        iso(verified.last_seen_at),
                        iso(verified.effective_from),
                        iso(verified.effective_until),
                    ),
                )
            )
            statements.append(
                insert(
                    "claim_evidence",
                    ("claim_id", "evidence_id", "role"),
                    (claim.id, evidence.id, "DIRECT"),
                )
            )
            statements.append(
                insert(
                    "verification_decisions",
                    ("claim_id", "state", "reason", "decided_at"),
                    (claim.id, decision.state.value, decision.reason, iso(decision.decided_at)),
                )
            )

            cat = info_category(document.notice_category.value)
            target = claim.effective_from
            item = build_information_item(
                item_id=information_item_id(claim.id, cat),
                claim_id=claim.id,
                title=document.title,
                summary=claim.statement[:2000],
                category=cat,
                source_url=str(document.canonical_url),
                published_at=document.published_at,
                effective_from=claim.effective_from,
                effective_until=claim.effective_until,
                due_at=target if cat == InformationCategory.DEADLINE else None,
                starts_at=target if cat == InformationCategory.EVENT else None,
                now=evidence.fetched_at,
            )
            statements.append(
                insert(
                    "information_items",
                    (
                        "id",
                        "claim_id",
                        "title",
                        "summary",
                        "category",
                        "program",
                        "branch",
                        "year",
                        "semester",
                        "importance",
                        "urgency",
                        "published_at",
                        "effective_from",
                        "effective_until",
                        "due_at",
                        "starts_at",
                        "ends_at",
                        "primary_source_url",
                        "created_at",
                        "updated_at",
                    ),
                    (
                        item.id,
                        item.claim_id,
                        item.title,
                        item.summary,
                        item.category.value,
                        item.audience.program,
                        item.audience.branch,
                        item.audience.year,
                        item.audience.semester,
                        item.importance.value,
                        item.urgency.value,
                        iso(item.published_at),
                        iso(item.effective_from),
                        iso(item.effective_until),
                        iso(item.due_at),
                        iso(item.starts_at),
                        iso(item.ends_at),
                        str(item.primary_source_url),
                        iso(now),
                        iso(now),
                    ),
                )
            )
            statements.append(
                insert(
                    "information_source_links",
                    ("item_id", "source_url", "is_primary"),
                    (item.id, str(item.primary_source_url), 1),
                )
            )

        manifest.append(
            {
                "source_id": source.id,
                "status": result.status.value,
                "evidence_id": evidence.id,
                "raw_content_hash": evidence.raw_content_hash,
                "evidence_ref": object_key,
                "fetched_at": iso(evidence.fetched_at),
            }
        )

    for source_url in _DISABLED_INFORMATION_SOURCE_URLS:
        target_items = (
            "SELECT id FROM information_items "
            f"WHERE primary_source_url={sql(source_url)}"
        )
        statements.extend(
            [
                "DELETE FROM information_relationships "
                f"WHERE old_item_id IN ({target_items}) "
                f"OR new_item_id IN ({target_items});",
                "DELETE FROM information_source_links "
                f"WHERE item_id IN ({target_items});",
                "DELETE FROM verification_matches "
                f"WHERE information_item_id IN ({target_items});",
                "UPDATE information_items SET "
                "supersedes_item_id=NULL,changed_from_item_id=NULL,corrected_item_id=NULL "
                f"WHERE supersedes_item_id IN ({target_items}) "
                f"OR changed_from_item_id IN ({target_items}) "
                f"OR corrected_item_id IN ({target_items});",
                f"DELETE FROM information_items WHERE primary_source_url={sql(source_url)};",
            ]
        )

    write_sql(statements, root)
    status = "FAILED" if failed == len(enabled) else "PARTIAL" if failed else "SUCCEEDED"
    payload = {
        "started_at": started.isoformat(),
        "finished_at": datetime.now(UTC).isoformat(),
        "source_count": len(enabled),
        "fetched_count": fetched,
        "changed_count": changed,
        "failed_count": failed,
        "status": status,
        "evidence": manifest,
    }
    manifest_path = root / "manifest.json"
    manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    manifest_hash = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    operations = [
        insert(
            "backup_manifests",
            ("id", "created_at", "manifest_hash", "object_count", "byte_count", "artifact_prefix"),
            (
                f"run:{started.isoformat()}",
                payload["finished_at"],
                manifest_hash,
                len([item for item in manifest if item.get("r2_object")]),
                sum(
                    (evidence_dir / f"{item['source_id']}-{item['raw_content_hash']}.bin")
                    .stat()
                    .st_size
                    for item in manifest
                    if item.get("raw_content_hash")
                ),
                "d1://evidence/",
            ),
        )
    ]
    for item in manifest:
        source_id = str(item["source_id"])
        status_value = str(item["status"])
        operations.append(
            insert(
                "source_health",
                (
                    "source_id",
                    "last_attempt_at",
                    "last_success_at",
                    "last_status",
                    "consecutive_failures",
                    "last_error",
                ),
                (
                    source_id,
                    payload["finished_at"],
                    payload["finished_at"] if status_value != "FAILED" else None,
                    status_value,
                    1 if status_value == "FAILED" else 0,
                    item.get("error"),
                ),
            )
        )
    (root / "sql" / "9999_operations.sql").write_text(
        "\n".join(operations) + "\n", encoding="utf-8"
    )
    return 1 if status == "FAILED" else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("artifacts/production"))
    raise SystemExit(run(parser.parse_args().out))
