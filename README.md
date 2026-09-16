# VGU Signal

**Know what's changed. Know what's official.**

VGU Signal is an independent student-information tool for Vivekananda Global University (VGU), Jaipur. It monitors public VGU sources, detects meaningful changes, structures information such as notices, calendars, exams, fees and deadlines, and delivers relevant updates to students.

> **Trust principle:** The official VGU source remains the authority. VGU Signal only discovers, structures, verifies and delivers information.

VGU Signal is **not affiliated with or endorsed by VGU** unless explicitly stated otherwise.

## Why VGU Signal exists

Important university information is often distributed across pages, PDFs, notices, calendars, event pages and separate portals. Students should not have to repeatedly hunt through fragmented sources or rely on forwarded rumors.

VGU Signal aims to provide one reliable information layer while preserving a direct link back to the authoritative VGU source.

## Core loop

```text
DISCOVER
   ↓
FETCH
   ↓
EVIDENCE
   ↓
EXTRACT
   ↓
VERIFY / DEDUPE / SUPERSEDE
   ↓
PERSONALIZE
   ↓
DELIVER
   ↓
VERIFY AGAIN
```

## Initial capabilities

- Monitor authoritative public VGU pages and documents.
- Detect new and changed notices/documents.
- Extract dates, deadlines, events and useful metadata.
- Preserve evidence and provenance for every published fact.
- Deduplicate repeated publications and track superseded information.
- Personalize updates by program, branch, year, semester and category.
- Deliver alerts and digests through Telegram.
- Let students verify whether a forwarded notice is officially confirmed.

## Trust states

VGU Signal uses explicit states rather than pretending every discovered item is equally reliable:

`DISCOVERED` → `FETCHED` → `PARSED` → `VERIFIED` → `CHANGED` / `SUPERSEDED` / `EXPIRED` / `CONFLICTING` / `REMOVED`

Community submissions are treated as `COMMUNITY_SIGNAL` and are never authoritative by themselves.

## Documentation

- [Roadmap](ROADMAP.md) — implementation phases and priorities.
- [Architecture](docs/ARCHITECTURE.md) — system boundaries and data flow.
- [Trust Model](docs/TRUST_MODEL.md) — evidence, provenance, verification and correction rules.
- [Source Strategy](docs/SOURCE_STRATEGY.md) — authoritative source hierarchy and acquisition strategy.
- [Product Specification](docs/PRODUCT.md) — product scope, UX and non-goals.
- [Development Guide](docs/DEVELOPMENT.md) — local development and engineering workflow.
- [Security Policy](SECURITY.md) — security boundaries and responsible disclosure.
- [Privacy](PRIVACY.md) — privacy principles and data minimization.
- [Contributing](CONTRIBUTING.md) — contribution rules.

## Zero-cost principle

The project is designed around a strict **₹0 / $0 operating-cost target**. Paid APIs, paid AI inference, paid hosting and pay-as-you-go dependencies are not requirements of the architecture.

Free infrastructure may be used where it is appropriate, but no critical component should quietly depend on a paid tier.

## Status

**Phase 0 — Repository foundation and contracts: COMPLETE.**

The deterministic repository bootstrap is implemented and the full Phase 0 CI gate is green. The project is now ready to begin **Phase 1 — Source Discovery & Evidence Engine**. Phase 1 starts with real official-source inventory and acquisition/evidence behavior; it does not reopen the core architecture or trust model.

The roadmap remains reliability-first: deterministic source monitoring and evidence handling come before AI-heavy or community-heavy features.

## License

License will be selected before the first public implementation release.
