# Phase 5 — Telegram MVP

**Status: COMPLETE on the Phase 5 verification revision.**

## Objective

Deliver the verified Phase 4 information model to students through Telegram without moving trust decisions into the delivery layer.

## Delivery boundary

The Cloudflare Worker is a thin Telegram/D1 adapter:

~~~text
Telegram
   ↓ webhook
Cloudflare Worker
   ↓
D1 users/preferences/notifications
   ↓
verified InformationItem + Claim
~~~

The Worker does not fetch VGU sources, parse documents, verify claims, or invent information.

## Telegram foundation

- Telegram Bot API calls use fetch from the Worker.
- Incoming webhook requests may be protected by TELEGRAM_WEBHOOK_SECRET.
- Bot credentials are Worker secrets; no token is committed.
- Group chats are rejected for personalized operations; the MVP is private-chat only.
- GET remains a health response.
- Scheduled execution runs every 15 minutes.

## Onboarding

/start collects program, branch/discipline, year, semester and notification categories. Onboarding state is durable in telegram_sessions, so a Worker restart does not lose the current step. /cancel stops onboarding and /settings displays configuration.

## Preferences

Supported commands include /set program B.Tech, /set branch CSE, /set year 2, /set semester 4, /categories EXAM,FEES,REGISTRATION, /categories ALL, /reminders on|off, /digest on|off, /mute, /unmute, /quiet HH:MM HH:MM and /quiet off.

Quiet-hour values are stored as UTC to avoid a timezone database dependency.

## Information commands

### /latest

Returns recent current, verified information filtered by declared scope and selected categories.

### /upcoming

Returns verified deadlines/events in the next 30 days, ordered by date.

### /search

Searches title, summary and verified claim statements and remains limited to current verified information relevant to preferences.

### /verify

Performs a conservative text lookup against the current verified archive. Verification searches the current verified archive independently of the user's notification-category and student-scope feed filters, so feed preferences cannot hide an official match. A match is presented as official evidence with its source. No match returns "Not officially confirmed" and explicitly does not claim that the submitted statement is false.

## Provenance and state display

Each result contains title, summary, category, importance and urgency, timing when available, an explicit officially verified state, the original official source URL, and current/changed/superseding/correcting indication.

The Worker renders InformationItem fields; it does not recalculate truth.

## Notifications

Deadline reminders run every 15 minutes for verified upcoming items with a deadline within 24 hours. They honor category/scope preferences, reminder toggle, mute and quiet hours.

Weekly digest runs Monday at 03:00 UTC and contains upcoming seven-day verified items. It respects digest toggle, scope/category filters, mute and quiet hours.

Durable notification identities prevent duplicate delivery. Failed sends can be retried; successful sends are not resent for the same key.

## Durable schema

Migration 0005_telegram_mvp.sql adds users, user_preferences, telegram_sessions and notifications.

## Trust boundary

Phase 5 never publishes an unverified claim, treats absence of an official match as proof of falsity, scrapes private WhatsApp/authenticated ERP, asks for ERP credentials, uses an LLM to decide truth, or stores bot secrets in source control.

## Deployment prerequisites

1. Apply the D1 migrations.
2. Configure TELEGRAM_BOT_TOKEN as a Worker secret.
3. Optionally configure TELEGRAM_WEBHOOK_SECRET.
4. Deploy the Worker.
5. Configure the Telegram webhook to the deployed Worker URL.
6. Verify /start, onboarding, /latest, /upcoming, /search, /verify and /settings.
7. Verify reminders and weekly digest against seeded verified D1 data.

Production resource provisioning remains Phase 6.
