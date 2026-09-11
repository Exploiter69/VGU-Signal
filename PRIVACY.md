# Privacy

VGU Signal is designed to provide useful student information without needing access to students' private university records.

## Data minimization

The initial product should need only enough information to personalize public information, such as:

- program;
- branch/discipline where relevant;
- year;
- semester;
- notification preferences.

The exact production schema will be documented before user data is collected.

## What VGU Signal should not collect

The project must not request student ERP passwords, session cookies or other credentials.

It should not scrape private WhatsApp groups or private student dashboards.

Do not collect identity documents or payment information for ordinary bot use.

## Community submissions

If a future verification feature accepts forwarded messages, screenshots or PDFs, submissions should be processed only for the verification purpose and retained no longer than necessary under the final retention policy.

Community material is not automatically published as authoritative information.

## Public-source data

Public VGU documents may contain names, contact details or other information published by the university. The system should avoid unnecessarily reproducing personal information when extracting or presenting such documents.

## Retention

A final production retention schedule must be established before launch. Evidence required for auditability should be separated conceptually from user data so that retaining source history does not require retaining unnecessary personal information.

## Transparency

Users should be able to understand:

- that VGU Signal is independent;
- what data is used for personalization;
- where an information item came from;
- why a notification was sent;
- how to stop notifications.

## Third-party services

Deployment may use free infrastructure and Telegram. The project should document what data crosses each service boundary before production launch.

The zero-cost requirement does not override privacy or security requirements.
