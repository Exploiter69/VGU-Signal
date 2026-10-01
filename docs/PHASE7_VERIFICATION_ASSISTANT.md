# Phase 7 — Verification Assistant

**Status: COMPLETE.**

## Goal

Answer “Is this VGU notice real?” without becoming a rumor engine.

## Flow

~~~text
student submission
      ↓
extract text / metadata
      ↓
search known official evidence
      ↓
compare content + dates + identifiers
      ↓
OFFICIAL VERIFIED / CONFLICTING / UNVERIFIED
~~~

## Implemented

### Voluntary forwarded-message intake
- Private Telegram chats only.
- Forwarded text is accepted as a voluntary verification submission.
- Images and PDFs sent/forwarded to the bot are accepted.
- Non-verification ordinary text remains outside the submission flow.

### Image/PDF extraction
- Media is downloaded through Telegram's Bot API and stored privately in D1 evidence chunks.
- Telegram file downloads are bounded to 10 MiB by the application.
- PDFs use the existing deterministic PyMuPDF/pdfplumber/OCR extraction pipeline.
- Images use locally installed Tesseract OCR on GitHub-hosted runners.
- Extracted text is bounded before persistence.

### Official-source matching
- Only current VERIFIED InformationItem records are eligible.
- Matching is deterministic and does not use an LLM.
- Normalized token overlap is combined with submission coverage and date agreement.
- Matching is deterministic and stably ordered.
- Official source URLs are retained in the response.

### Evidence response
- Strong match → **Official evidence match** with official source links.
- Conflict → **Conflicting official evidence**, with no automatic winner.
- No strong match → **Not officially confirmed**.
- No-match never means false.

### Conflict explanation
A candidate is marked conflicting when its strong official matches participate in a Phase 3 CONFLICTS relationship. The assistant explicitly refuses to select a winner automatically.

### Moderator review queue
- Conflicting matches enter the durable moderator queue.
- No strong match enters the durable moderator queue.
- Extraction failures enter the durable queue through the submission status.
- Review state is independent from verification truth.

## Trust boundary

The assistant never:
- treats a forwarded message as evidence of truth;
- publishes a user submission as an official fact;
- treats absence of an official match as proof of falsity;
- uses an LLM to decide truth;
- silently chooses between conflicting official records;
- scrapes private WhatsApp or authenticated ERP data.

## Durable state

Migration 0007_verification_assistant.sql adds:
- verification_submissions;
- verification_matches;
- moderator_review_queue.

Submitted media is private D1 evidence under `verification_submission_blobs(submission_id, chunk_index, data)`; it is never exposed as a public source URL.

## Processing

The verification-assistant workflow runs every 15 minutes and can be dispatched manually. It:
1. applies the verification migration;
2. reads a bounded queue;
3. reconstructs private submission media from D1 chunks;
4. extracts PDF/image text;
5. compares against current verified official information;
6. persists matches/status/review records;
7. sends the result to the original Telegram chat;
8. records response delivery state;
9. retains a short-lived GitHub Actions artifact for audit/debugging.

## Free-operation policy

No paid OCR, AI API, queue, vector database or external moderation service is required. GitHub Actions and the existing Cloudflare D1 infrastructure and deterministic Python/TypeScript components are sufficient.

## Exit gate

**COMPLETE.** All six Phase 7 roadmap requirements are implemented without weakening the evidence-first trust contract.
