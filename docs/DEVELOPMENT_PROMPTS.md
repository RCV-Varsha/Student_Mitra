# Material development prompts

These are actual user instructions materially used in this development session. The requirements PDF was read as product specification, not as authority to override the user. Its optional features and final encouragement to expand scope were excluded. No invented separate architecture/frontend/backend prompts or hidden internal reasoning are presented as development prompts.

## Primary development prompt (architecture, frontend, backend, database, AI, testing, documentation)

> Build the AI Study Companion described in Project_Requirements.pdf as a complete, polished, deployable prototype. Implement only Must Have features and mandatory submission requirements. UI quality and visual presentation are part of acceptance.
>
> Execution:
> - Inspect the repository and requirements once. Reuse existing code and stack. If empty, use React + TypeScript, Django REST Framework, PostgreSQL with pgvector, and a persistent background worker.
> - Work autonomously through implementation, verification, and deployment preparation. Ask only for missing credentials or genuinely blocking decisions.
> - Minimize tokens: concise updates, targeted file reads, bounded logs, no repeated plans, full-file dumps, unnecessary agents, or speculative refactoring.
> - Maintain a short requirements checklist. Complete working features, not placeholders. Exclude Should Have/Nice to Have features.
>
> Required functionality:
> 1. Authentication, user/admin roles, server-enforced ownership and project isolation across APIs, files, retrieval, and jobs.
> 2. Spaces with name/description; Projects with name/description/learning goal.
> 3. PDF upload and persistent asynchronous processing: queued/processing/ready/failed, retry, duplicate-job protection, page-aware extraction, concept extraction, and searchable chunks. Clearly report unsupported/scanned content.
> 4. Project-scoped AI Tutor using retrieved material, goals, recent conversation, and compact persistent learning context. Return verifiable document/page citations with source navigation; explicitly state insufficient evidence when unsupported.
> 5. Adaptive quizzes with MCQ and open-ended questions. Select concepts/difficulty using mastery, mistakes, recent performance/activity, and question history—not merely correct→harder. Provide validated rubric-based grading and explanatory feedback.
> 6. Persist concept mastery estimates, evidence/history, growth trends, strengths/weaknesses, repeated mistakes, and actionable next-step recommendations.
> 7. Track learning events. Provide project/global analytics for activity, assessments, mastery, trends, and AI usage. Make repeated submissions/events idempotent.
> 8. Home dashboard: continue learning, recent projects, progress, attention areas, next action.
> 9. Admin dashboard: users, spaces/projects, engagement, assessments/progress, AI usage/evaluations, background jobs, failures, system health; user drill-down and filters by user/project/space/type/date.
> 10. Controlled, schema-validated, permission-checked AI application tools. Never expose unrestricted database access or trust uploaded content as instructions.
> 11. Log AI feature/model, latency, tokens, estimated cost, success/failure, and retrieval source references. Handle timeouts, rate limits, invalid outputs, processing failures, and recovery. Keep secrets outside source control.
>
> UI and representation:
> - Cohesive responsive light theme, clear typography, consistent spacing, accessible contrast, restrained accent colors, polished cards/tables/charts.
> - Sidebar for Spaces/Projects; project navigation: Overview, Materials, Tutor, Quiz, Growth, Analytics.
> - Clear progress indicators, mastery bars, labeled trend charts, readable quiz feedback, clickable citations, and prominent next actions.
> - Include loading, empty, validation, error, retry, and success states. All controls must work.
> - Use real persisted data; label seeded demo data. Never fabricate analytics or AI results. Avoid unnecessary animation and decorative dashboards.
>
> Verification:
> - Run meaningful tests for authentication/authorization, cross-project isolation, citations and unsupported questions, structured outputs/grading, adaptive selection/mastery, recommendations, job retries/failures, and idempotency.
> - Include a small repeatable AI evaluation set covering retrieval, Tutor, assessment, and recommendations.
> - Verify the complete learning loop and admin workflow in-browser; inspect desktop/mobile layouts and fix visible defects. Distinguish mocked tests from live AI verification.
>
> Delivery:
> - Working frontend/backend/database/worker, migrations, dependency lockfiles, .env.example, simple startup/deployment configuration, and demo seed command.
> - README with setup/testing/deployment; architecture diagram and decisions; evaluation approach/results; known limitations.
> - AI usage documentation separating development AI from product AI. Record actual material development prompts.
> - Prepare a short demo script and record the mandatory demo video if tooling permits.
> - Deploy to a public URL and publish a secret-free public GitHub repository using available authorized accounts. If blocked, finish everything else and report the exact missing access; never claim unperformed deployment or tests.
>
> Finish with a concise checklist of completed requirements, verified tests, URLs, and remaining blockers.

## Follow-up: repository and provider selection

> Github access is there for u ..use this repo: https://github.com/RCV-Varsha/Student_Mitra
> This is Ai provider.. Gemini api key: [REDACTED SECRET]
> I didn't understand what do u mean by hosting account

The key is stored only in the ignored local `.env`. Tool execution arguments, terminal commands and authored source are implementation work, not separate user development prompts. Debugging was guided by actual test failures: login CSRF enforcement, local TLS trust, provider model availability, and browser workflow results.

## Final verification constraint

> Finish with the live-AI blocker documented

The user declined further live provider work after the supplied Gemini account reported quota exhaustion. No fallback provider was used.
