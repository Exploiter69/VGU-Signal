from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import httpx


def unwrap(value: object) -> list[dict]:
    if isinstance(value, list):
        return value[0].get("results", []) if value else []
    if isinstance(value, dict):
        return value.get("results", [])
    return []


def escape(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def telegram_send(token: str, chat_id: int, text: str) -> None:
    response = httpx.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    if not payload.get("ok"):
        raise RuntimeError(payload.get("description", "Telegram send failed"))


def sql(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=Path, required=True)
    parser.add_argument("--sql", type=Path, required=True)
    args = parser.parse_args()

    token = os.environ["TELEGRAM_BOT_TOKEN"]
    rows = unwrap(json.loads(args.rows.read_text(encoding="utf-8")))
    grouped: dict[str, list[dict]] = {}
    submissions: dict[str, dict] = {}

    for row in rows:
        submissions[row["id"]] = row
        if row.get("information_item_id"):
            grouped.setdefault(row["id"], []).append(row)

    statements: list[str] = []
    for submission_id, row in submissions.items():
        status = row["status"]
        matches = sorted(grouped.get(submission_id, []), key=lambda item: -float(item["score"]))
        if status == "MATCHED":
            body = "<b>Official evidence match</b>\n\n"
            body += "\n\n".join(
                f"<b>{index}. {escape(item['title'])}</b>\n"
                f"{escape(item['summary'])}\n"
                f'<a href="{escape(item["primary_source_url"])}">Official source</a>'
                for index, item in enumerate(matches[:3], 1)
            )
        elif status == "CONFLICTING":
            body = "<b>Conflicting official evidence</b>\n\n"
            body += escape(row["result_summary"] or "A documented conflict was found.")
            body += "\n\nA moderator review is required; no winner is selected automatically."
        elif status == "UNVERIFIED":
            body = "<b>Not officially confirmed.</b>\n\n"
            body += escape(
                row["result_summary"] or "No sufficiently strong official match was found."
            )
        else:
            body = "<b>Verification could not be completed automatically.</b>\n\n"
            body += "A moderator review is required."

        try:
            telegram_send(token, int(row["telegram_chat_id"]), body)
        except Exception:
            continue
        processed_at = row.get("processed_at") or ""
        statements.append(
            f"UPDATE verification_submissions SET response_sent_at={sql(processed_at)} "
            f"WHERE id={sql(submission_id)};"
        )

    args.sql.write_text("\n".join(statements) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
