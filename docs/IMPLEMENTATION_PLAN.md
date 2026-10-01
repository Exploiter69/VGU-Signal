# VGU Signal Implementation Plan

This document records the execution plan by phase. Phase 0–4 are complete as documented in the existing sections.

## Phase 5 — Telegram MVP

**Status: COMPLETE.** See docs/PHASE5_TELEGRAM_MVP.md.

### Step 1 — Telegram foundation
- [x] Worker Telegram webhook handler.
- [x] Telegram API adapter.
- [x] Private-chat boundary.
- [x] Secret-token webhook validation.
- [x] Worker health endpoint.

### Step 2 — Onboarding and preferences
- [x] Durable /start flow.
- [x] Program/branch/year/semester capture.
- [x] Category capture.
- [x] Durable session state.
- [x] /settings display.
- [x] Preference mutation commands.

### Step 3 — Student query commands
- [x] /latest.
- [x] /upcoming.
- [x] /search.
- [x] Conservative /verify.
- [x] Source/provenance display.
- [x] Changed/superseding/correcting state display.

### Step 4 — Notifications
- [x] Deadline reminders.
- [x] Weekly digest.
- [x] Durable notification identity.
- [x] Retry of failed sends.
- [x] Quiet-hour filtering.
- [x] Global mute/unmute.
- [x] Per-channel reminder/digest toggles.

### Step 5 — Durable delivery schema
- [x] Users.
- [x] Preferences.
- [x] Onboarding sessions.
- [x] Notification history/deduplication.

### Step 6 — Quality and trust
- [x] No delivery path publishes unverified claims.
- [x] No-match verification response is explicitly non-falsifying.
- [x] No private/ERP ingestion.
- [x] No bot secret committed.
- [x] Python quality gate retained.
- [x] Worker typecheck retained.

### Phase 5 exit gate

**COMPLETE.**

A student can subscribe, configure relevance preferences, receive a relevant verified update, inspect its official source, and distinguish a changed/superseded/corrected item from a current one. Notification delivery is durable and respects mute/quiet/category preferences.

## Phase 6 and later

Phase 6 owns production-free infrastructure provisioning, scheduled acquisition, D1/R2 deployment policy, operational health checks, backups/recovery and production secret management. Phase 7 owns the richer forwarded-document verification assistant. Phase 8 owns advanced search/calendar UX. Phase 9 owns AI augmentation. Phase 10 owns expansion.
