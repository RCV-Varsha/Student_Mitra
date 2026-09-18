# Verification and known limitations

## Verified

- Production React/TypeScript build passed, including the final accessible admin labels and accurate unavailable-usage display.
- **27 deterministic Django tests passed locally.** AI outputs/provider failures are mocked in relevant unit tests; these do not claim live model quality.
- GitHub CI on implementation commit `dbfb7fe` passed the frontend build and all **27 backend tests/migrations on PostgreSQL 16 with pgvector**. See `ci-results.json` for the successful run URL and job results.
- Live Gemini processed the three-page PDF into page-aware chunks and concepts. Real grounded Tutor answers with document/page citations, unsupported-question abstention, adaptive MCQ generation and grading were observed in browser runs.
- First six-case live evaluation: **4/6 passed**. Two failures involved a transient provider error and concurrent SQLite locking. Follow-up token matching, transaction handling and recovery were repaired. The final attempted live rerun was **3/6**, with remaining provider-dependent cases blocked by HTTP 429 quota exhaustion. Both result files and database evaluation history preserve failures.
- The provider explicitly reported `generate_content_free_tier_requests`, limit **20**, for `gemini-3.6-flash`. The user instructed development to finish with this blocker documented; no alternate provider was silently used.
- **Seven no-mock browser checks passed using real persisted data:** Home, mastery/growth/recommendations, feedback persistence, project analytics, global analytics, 390px mobile navigation/layout, and admin user/date/type filtering with assessment/job/evaluation/health inspection. See `browser-persisted-results.json`.
- Desktop Tutor/admin and mobile Home/Analytics screenshots were visually inspected. Contrast and admin control labeling defects were fixed. No horizontal page overflow or JavaScript errors were observed in the completed persisted-data browser run.
- Live open-ended generation and rubric output were observed during the initial evaluation, but the complete live open-answer-to-persisted-mastery loop was **not verified successfully**. Unit tests cover its validated transaction path. Do not describe the mandatory live demo as fully complete.

## Deployment and recording status

The local app and persistent worker run with SQLite/WAL for demonstration. PostgreSQL/pgvector is the tested CI and Docker deployment path. Docker is absent locally; the installed local PostgreSQL service requires an unavailable password. No local PostgreSQL runtime or Docker launch is claimed.

Public source: https://github.com/RCV-Varsha/Student_Mitra (verified public). The provider key, local environment, database, journals and private media are excluded from the final source tree.

**Public application deployment is blocked:** no authorized hosting account/VM/container credentials were supplied. A hosting service must support Django/Gunicorn, PostgreSQL/pgvector, a persistent worker and shared private media storage. Compose, migrations, health checks, persistent volumes and optional Caddy HTTPS configuration are included. GitHub is source hosting, not the deployed application.

The demo recording uses real browser captures and saved live results. Captions explicitly disclose the quota-blocked open-grading step. It is a partial mandatory demo, not evidence of an unperformed full live loop. See `DEMO.md` and `demo-recording-metadata.json`.

## Known limitations

- Text-based PDFs only; no OCR or image/diagram interpretation; ruled tables and text layout are extracted, while complex tables still need source review. Mixed scanned pages are explicitly reported. Limits: 20 MB, 200 pages; concept extraction samples at most 24 chunks.
- Token-hashing plus lexical retrieval is transparent and cheap, but weaker than semantic embeddings. Exact citation quotes verify source provenance, not full logical entailment. Broader paraphrases can be refused conservatively.
- Mastery is a heuristic estimate, not a validated psychometric measure. Open-ended grading can vary; the six-case evaluation is small and not a calibrated benchmark.
- Configurable token price rates are estimates; actual provider billing and model availability can differ. Rate limits can require waiting, increasing quota or enabling provider billing. Failure responses may omit usage; those rows display Not reported. Aggregate totals reflect only reported usage.
- Local SQLite is for one-worker development only. PostgreSQL is the deployment path. Concurrent duplicate AI requests may spend tokens twice even though persisted state is deduplicated.
- Admin aggregates are prototype-scale; activity/usage/history result sets are bounded, not a full export or cursor-paginated data warehouse. Mastery is current all-time state; date filters apply to events, assessments, usage and job updates. Event type filters apply to the activity stream.
- Authentication has secure session/CSRF/ownership checks, but no email verification, account recovery, multi-factor authentication or distributed abuse control. None of these optional features is represented as implemented.
- Browser verification targets installed Chrome and responsive desktop/mobile viewport layouts. It is not a claim of physical iOS/Android or cross-engine testing.


## Publication correction

The initial push briefly included SQLite test-database journal files (demo and browser-test data). No provider key was present. The files were removed from the published branch history with an exact force-with-lease, ignore rules were expanded to cover journals, and the full committed tree was rescanned for private database/media files and the actual configured API keys. Test sessions are invalidated after verification. The private runtime database and environment file are not part of the final source tree. GitHub may retain unreachable objects outside the branch; no permanent server-side purge is claimed.

## Should Have extension (2026-09-18)

- **41 Django tests passed locally** (27 existing + 14 extension tests); the recorded fixture regression evaluation passed **14/14**. Frontend production build and migration drift check passed. Migration 0002 applied locally.
- The new deterministic suite covers streamed JSON and citation validation, invalid draft rejection, provider contracts, cache isolation/invalidation, continuity, page-aware table extraction, insight jobs, retry recovery and filtered analytics. Provider outputs are mocked. See `regression-results.json` for the exact executed count.
- Six additional browser checks passed with real persisted data and no provider/network mocks: unsupported SSE answer, memory after reload, background insight snapshot, breakdown/trace UI, 390px layouts, and admin insight/user filtering. See `browser-should-results.json`. Desktop/mobile screenshots were visually inspected.
- No new live AI calls. No claim of successful live streamed Gemini/OpenAI answers. Existing demo video predates this extension; screenshots and browser scripts cover the added screens.
