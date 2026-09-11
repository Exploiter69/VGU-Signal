# VGU Signal Product Specification

## Product statement

**VGU Signal helps VGU students know what changed, what matters to them, and what is officially confirmed.**

It is an independent information layer over public VGU sources.

## Primary users

VGU students who need timely information about:

- academic calendars;
- exams and exam forms;
- fees and payment deadlines;
- registration and re-registration;
- holidays;
- notices and circulars;
- events;
- important university documents.

## Core user questions

The product should answer these quickly:

1. What is new?
2. What changed?
3. What is due soon?
4. Does this apply to me?
5. Is this officially confirmed?
6. What is the original source?

## MVP experience

Telegram is the first delivery channel.

### `/start`

Onboarding captures only the minimum needed for relevance:

- program;
- branch/discipline where applicable;
- year;
- semester;
- notification categories.

### `/latest`

Shows recent verified information relevant to the student.

### `/upcoming`

Shows upcoming deadlines and important events, ordered by urgency.

### `/search`

Searches the verified information archive.

### `/verify`

Accepts a future student-forwarded message/document and checks it against known official evidence.

### `/settings`

Changes preferences and notification behavior.

## Notification principles

Notifications should be:

- relevant;
- concise;
- source-linked;
- state-aware;
- deduplicated;
- respectful of user preferences.

A notification should make it obvious whether the item is new, changed or superseded.

## Importance model

Importance should be derived from deterministic signals before AI is considered.

Potential signals:

- deadline proximity;
- exam relevance;
- fee/payment consequence;
- registration consequence;
- audience scope;
- explicit urgency in the official notice;
- whether an existing deadline changed.

Importance is not the same thing as truth. Verification and importance are separate dimensions.

## Personalization

The system should filter information based on declared student preferences rather than requiring access to private academic records.

A student's branch/year preference does not prove that a notice applies to them; applicability must still be inferred from the official material and presented conservatively.

## Trust UI

Every important item should expose:

- title;
- concise summary;
- effective/published date where known;
- deadline where applicable;
- verification state;
- original source link;
- indication when it supersedes or changes an earlier item.

## Future verification assistant

A student may forward a screenshot, message or PDF.

The assistant should return one of:

- **Officially verified** — authoritative evidence matches.
- **Official source changed/superseded** — related authoritative information differs.
- **Conflicting** — authoritative sources disagree.
- **Not officially confirmed** — sufficient official evidence was not found.

It must not call a message fake merely because no match was found.

## Future feature set

### V1

- personalized deadlines;
- weekly digest;
- change history;
- `.ics` calendar export;
- richer search;
- important document shortcuts.

### V2

- grounded natural-language search;
- local AI summaries;
- semantic retrieval;
- document explanation;
- stronger community verification workflow.

## Non-goals

VGU Signal is not:

- an official VGU administration system;
- an ERP replacement;
- a private student-data aggregator;
- a WhatsApp group scraper;
- a rumor feed;
- a substitute for reading the original source when the source matters.

## Positioning

Recommended public positioning:

> **VGU Signal — Know what's changed. Know what's official.**
>
> An independent student information tool powered by public VGU sources.

Avoid names or language that imply endorsement, official university ownership or privileged access.
