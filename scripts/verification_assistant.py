from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from vgu_signal.extraction import extract_dates, extract_evidence, normalize_text

STOP_WORDS = {
    "a", "an", "and", "are", "be", "by", "for", "from", "in", "is", "of",
    "on", "or", "that", "the", "this", "to", "with", "vgu", "notice", "please",
}
DATE_PATTERN = re.compile(r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}|[A-Za-z]{3,9}\s+\d{1,2},\s+\d{4})\b")


@dataclass(frozen=True)
class Candidate:
    id: str
    title: str
    summary: str
    statement: str
    category: str
    source_url: str
    due_at: str | None
    starts_at: str | None
    published_at: str | None
    claim_state: str


def tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]{2,}", normalize_text(value).lower())
        if token not in STOP_WORDS
    }


def date_tokens(value: str) -> set[str]:
    found: set[str] = set()
    for date in extract_dates(value):
        found.add(date.value.date().isoformat())
    for raw in DATE_PATTERN.findall(value):
        found.add(raw.lower())
    return found


def score_submission(submitted: str, candidate: Candidate) -> tuple[float, str]:
    left = tokens(submitted)
    right = tokens(" ".join((candidate.title, candidate.summary, candidate.statement)))
    if not left or not right:
        return 0.0, "No comparable text tokens."
    overlap = len(left & right)
    union = len(left | right)
    jaccard = overlap / union if union else 0.0
    coverage = overlap / len(left)
    dates_left = date_tokens(submitted)
    dates_right = date_tokens(
        " ".join(
            value for value in
            (candidate.summary, candidate.statement, candidate.due_at, candidate.starts_at)
            if value
        )
    )
    date_bonus = 0.15 if dates_left and dates_left & dates_right else 0.0
    score = min(1.0, 0.55 * jaccard + 0.30 * coverage + date_bonus)
    reasons = [f"{overlap} shared normalized tokens"]
    if date_bonus:
        reasons.append("matching date")
    return score, "; ".join(reasons)


def classify(scores: list[tuple[Candidate, float, str]], conflict_ids: set[str]) -> str:
    if not scores:
        return "UNVERIFIED"
    strong = [item for item in scores if item[1] >= 0.35]
    if not strong:
        return "UNVERIFIED"
    if any(item[0].id in conflict_ids for item in strong):
        return "CONFLICTING"
    return "MATCHED"


def sql(value: object) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def extract_submission_text(path: Path, content_type: str, source_id: str) -> tuple[str, str]:
    body = path.read_bytes()
    if content_type == "application/pdf":
        document = extract_evidence(
            evidence_id=f"submission:{hashlib.sha256(body).hexdigest()}",
            source_id=source_id,
            url=f"submission://{path.name}",
            content_type=content_type,
            body=body,
        )
        return document.body_text, document.extraction_kind.value
    if content_type.startswith("image/"):
        output = path.with_suffix(".txt")
        subprocess.run(
            ["tesseract", str(path), str(output.with_suffix("")), "--psm", "6"],
            check=True,
            timeout=90,
            capture_output=True,
            text=True,
        )
        return output.read_text(encoding="utf-8", errors="replace"), "OCR"
    raise ValueError(f"unsupported verification media type: {content_type}")


def build_sql(
    submission_id: str,
    status: str,
    summary: str,
    extracted_text: str | None,
    extraction_kind: str | None,
    scores: list[tuple[Candidate, float, str]],
    now: str,
    review_reason: str | None,
) -> str:
    statements = [
        f"UPDATE verification_submissions SET status={sql(status)},"
        f"result_summary={sql(summary)},extracted_text={sql(extracted_text)},"
        f"extraction_kind={sql(extraction_kind)},processed_at={sql(now)} "
        f"WHERE id={sql(submission_id)};"
    ]
    statements.extend(
        f"INSERT OR REPLACE INTO verification_matches"
        f"(submission_id,information_item_id,score,match_reason,matched_at)"
        f"VALUES({sql(submission_id)},{sql(candidate.id)},{score:.6f},{sql(reason)},{sql(now)});"
        for candidate, score, reason in scores[:5]
    )
    if review_reason:
        statements.append(
            f"INSERT OR REPLACE INTO moderator_review_queue"
            f"(id,submission_id,reason,status,created_at)"
            f"VALUES({sql('review:' + submission_id)},{sql(submission_id)},"
            f"{sql(review_reason)},'OPEN',{sql(now)});"
        )
    return "\n".join(statements)


def run(input_path: Path, archive_path: Path, out_path: Path, now: str) -> int:
    submissions = json.loads(input_path.read_text(encoding="utf-8"))
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    candidates = [Candidate(**row) for row in archive["items"]]
    conflicts = {tuple(row) for row in archive.get("conflicts", [])}
    conflict_ids = {item for pair in conflicts for item in pair}

    output: list[str] = []
    for row in submissions["submissions"]:
        submission_id = row["id"]
        text = (row.get("submitted_text") or row.get("extracted_text") or "").strip()
        extraction_kind = row.get("extraction_kind")
        if row.get("object_file"):
            try:
                text, extraction_kind = extract_submission_text(
                    Path(row["object_file"]), row["content_type"], "verification-submission"
                )
            except Exception as exc:
                output.append(
                    build_sql(
                        submission_id, "FAILED", f"Extraction failed: {exc}", None,
                        None, [], now, "Automatic extraction failed; manual review required."
                    )
                )
                continue
        scores = []
        for candidate in candidates:
            score, reason = score_submission(text, candidate)
            if score >= 0.15:
                scores.append((candidate, score, reason))
        scores.sort(key=lambda item: (-item[1], item[0].id))
        status = classify(scores, conflict_ids)
        top = scores[0][1] if scores else 0.0
        if status == "MATCHED":
            summary = "Official verified information matched the submission."
            review_reason = None
        elif status == "CONFLICTING":
            summary = "The submission matches official information involved in a documented conflict; a human review is required."
            review_reason = "Conflicting official evidence requires moderator review."
        else:
            summary = "No sufficiently strong official match was found. This does not prove the submission false."
            review_reason = "No strong deterministic official match."
        output.append(
            build_sql(
                submission_id, status, summary, text, extraction_kind, scores, now, review_reason
                if status != "MATCHED" else None,
            )
        )

    out_path.write_text("\n".join(output) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--now", required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.input, args.archive, args.out, args.now))
