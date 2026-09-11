# Security Policy

Security and trust are core requirements of VGU Signal.

## Security boundaries

VGU Signal is intended to process public university information and minimal user preferences.

It must not require or collect:

- VGU ERP passwords;
- student session cookies;
- private ERP dashboard data;
- private WhatsApp group content;
- unnecessary identity documents;
- payment-card information.

## Secrets

Never commit credentials, tokens, API keys, cookies or deployment secrets.

Rotate any secret that is accidentally exposed.

## Data minimization

Only collect information required for the product feature being implemented. Prefer preference-based personalization over access to private academic records.

## Source safety

A source adapter must not bypass authentication or access controls. Public availability does not imply permission to access unrelated private areas of the same domain.

## Reporting a vulnerability

If you discover a security vulnerability, please report it privately to the repository owner rather than publishing exploit details in a public issue.

Include enough information to reproduce the issue safely, its potential impact and any suggested mitigation.

## Scope

This policy covers the VGU Signal codebase, its documented deployment architecture and project-controlled data handling. It does not claim authority over the security of VGU systems or third-party services.
