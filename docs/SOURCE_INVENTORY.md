# Phase 1 Source Inventory

This inventory records the public VGU sources admitted to the Phase 1 acquisition layer. It is intentionally small. Discovery is not universal crawling.

## Authority rule

Only public VGU material is admitted as authoritative evidence. A source being listed here means VGU Signal may acquire it; it does not mean every extracted statement is automatically a verified student-facing claim.

## Registered sources

| ID | Source | URL | Expected media |
| --- | --- | --- | --- |
| `vgu-resources` | Official resources / handbooks / academic-calendar index | `https://vgu.ac.in/resources/handbook-brochures` | HTML/XHTML/PDF/XML/text |
| `vgu-academic-calendar-2026-27-first-year` | Academic Calendar 2026-27 for first-year students | `https://vgu.ac.in/assets/documents/footer/AcademicCalendar2026-27%28ForFirstYrStudents%29.pdf` | PDF |
| `vgu-examination-rules` | Examination Rules 2.0 | `https://vgu.ac.in/assets/documents/footer/ExamRules.pdf` | PDF |
| `vgu-public-notice` | Public Notice CDOE | `https://vgu.ac.in/assets/documents/footer/PUBLIC-NOTICE-FOR-CDOE.pdf` | PDF |
| `vgu-fees` | Public fee structure | `https://vgu.ac.in/admission/fee-structure` | HTML/XHTML |
| `vgu-events` | Public campus events | `https://vgu.ac.in/campus-life/events` | HTML/XHTML |

## Why the resources index is important

The official resources page exposes links for academic calendars, examination rules, handbooks and other student-facing documents. It currently lists the 2026-27 first-year calendar, an annual-scheme calendar, Examination Rules 2.0 and Public Notice CDOE. The acquisition layer therefore keeps the index as a discovery anchor while also admitting the stable direct documents that were verified during Phase 1.

## Discovery boundaries

Phase 1 deliberately does not register:

- Student ERP pages;
- authenticated exam/registration dashboards;
- private WhatsApp groups;
- student credentials or session cookies;
- arbitrary third-party copies of VGU documents.

Department and CDOE expansion remains a later roadmap phase unless a public source is required to complete a specific verified vertical slice.

## Evidence policy

Each successful fetch produces an immutable evidence metadata record keyed by source ID and SHA-256 of the exact response bytes. Identical content is deduplicated without deleting prior history. A failed fetch leaves the previous last-known-good evidence untouched.

## Revalidation policy

The acquisition layer uses ETag and Last-Modified when available, but never treats missing validators as an error. SHA-256 remains the fallback change detector.

Robots policy is evaluated before the source fetch. Sitemap declarations are parsed for discovery but never used to override robots restrictions.

## External confirmation

The source URLs above were checked against the current public VGU site during Phase 1 implementation. The official resources page currently exposes the calendar, examination rules and public-notice entries; the fee and events pages are public VGU pages. Live availability is not part of CI, so fixture tests remain the release gate.
