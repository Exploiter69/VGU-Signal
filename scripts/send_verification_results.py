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
        json={"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    if not payload.get("ok"):
        raise RuntimeError(payload.get("description", "Telegram send failed"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--rows", type=Path, required=True)
    parser.add_argument("--sql", type=Path, required=True)
    args = parser.parse_args()
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    rows = {row["id"]: row for row in unwrap(json.loads(args.rows.read_text(encoding="utf-8")))}
    results = unwrap(json.loads(args.results.read_text(encoding="utf-8")))
    statements: list[str] = []

    for row in results:
        if row.get("response_sent_at"):
            continue
        submission_id = row["id"]
        source_rows = unwrap(
            json.loads(
                subprocess_output(
                    f"SELECT m.score,m.match_reason,i.title,i.summary,i.category,i.primary_source_url "
                    f"FROM verification_matches m JOIN information_items i ON i.id=m.information_item_id "
                    f"WHERE m.submission_id='{submission_id.replace(chr(39), chr(39) * 2)}' "
                    "ORDER BY m.score DESC LIMIT 3"
                )
            )
        )
        status = row["status"]
        if status == "MATCHED":
            body = "<b>Official evidence match</b>\n\n"
            body += "\n\n".join(
                f"<b>{index}. {escape(item['title'])}</b>\n"
                f"{escape(item['summary'])}\n"
                f"<a href="{escape(item['primary_source_url'])}">Official source</a>"
                for index, item in enumerate(source_rows, 1)
            )
        elif status == "CONFLICTING":
            body = "<b>Conflicting official evidence</b>\n\n"
            body += escape(row["result_summary"] or "A documented conflict was found.")
            body += "\n\nA moderator review is required; no winner is selected automatically."
        else:
            body = "<b>Not officially confirmed.</b>\n\n"
            body += escape(row["result_summary"] or "No sufficiently strong official match was found.")
        try:
            telegram_send(token, int(row["telegram_chat_id"]), body)
        except Exception:
            continue
        now = row.get("processed_at") or ""
        statements.append(
            "UPDATE verification_submissions SET response_sent_at="
            + ("NULL" if not now else "'" + now.replace("'", "''") + "'")
            + " WHERE id='"
            + submission_id.replace("'", "''")
            + "';"
        )

    args.sql.write_text("\n".join(statements) + "\n", encoding="utf-8")


def subprocess_output(command: str) -> str:
    import subprocess
    result = subprocess.run(
        ["npx", "wrangler", "d1", "execute", "vgu-signal", "--remote", "--json", "--command", command],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


if __name__ == "__main__":
    main()
