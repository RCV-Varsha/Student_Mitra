# Verification and known limitations

## Verified so far

- Production React/TypeScript build passed.
- 25 deterministic Django regression tests passed on local SQLite. Generated model responses are mocked in these tests; this is not a claim of live model accuracy.
- Live Gemini successfully processed the 3-page demo PDF into page-aware chunks and six concepts.
- First live evaluation: 4/6 passed. Grounded Tutor/page citation, retrieval, MCQ and recommendation checks passed. A transient provider failure and concurrent SQLite lock affected two cases; follow-up parsing and transaction handling were repaired.
- Initial unmocked Chrome workflow passed registration, Space/Project creation, PDF processing, grounded Tutor/source access, unsupported question and MCQ feedback. Open-question generation encountered provider HTTP 429; the app displayed the error without fabricating a question or score.
- Desktop screenshots inspected; secondary text contrast improved. A final browser run and serialized live evaluation are in progress, not yet claimed complete.

See the JSON result files for exact, timestamped outputs. Failed evaluation history remains visible in the admin dashboard.

## Deployment status

The local app and worker use SQLite for verification. PostgreSQL with pgvector is configured in Docker Compose and GitHub CI; Docker is not installed locally, and the installed PostgreSQL service requires credentials that were not supplied. No local PostgreSQL runtime test is claimed at this point.

Public application deployment requires a hosting account capable of running Django, PostgreSQL/pgvector, a persistent worker and shared private media storage. No hosting access has been supplied. GitHub publication is being prepared for the user-specified repository; no public application URL is claimed.

## Known limitations

- Text-based PDFs only; no OCR, image/diagram interpretation or robust table layout reconstruction. Mixed scanned pages are explicitly reported. Limits: 20 MB, 200 pages; concept extraction samples at most 24 chunks.
- Token-hashing plus lexical retrieval is transparent and cheap, but weaker than semantic embeddings. Exact citation quotes verify source provenance, not full logical entailment. Broader paraphrases can be refused conservatively.
- Mastery is a heuristic estimate, not a validated psychometric measure. Open-ended grading can vary; the six-case evaluation is small and not a calibrated benchmark.
- Configurable token price rates are estimates; actual provider billing and model availability can differ. Rate limits can require waiting and retrying.
- Local SQLite is for one-worker development only. PostgreSQL is the deployment path. Concurrent duplicate AI requests may spend tokens twice even though persisted state is deduplicated.
- Admin aggregates are prototype-scale; activity/usage/history result sets are bounded, not a full export or cursor-paginated data warehouse. Mastery is current all-time state; date filters apply to events, assessments, usage and job updates. Event type filters apply to the activity stream.
- Authentication has secure session/CSRF/ownership checks, but no email verification, account recovery, multi-factor authentication or distributed abuse control. None of these optional features is represented as implemented.
- Browser verification targets installed Chrome and responsive desktop/mobile viewport layouts. It is not a claim of physical iOS/Android or cross-engine testing.
