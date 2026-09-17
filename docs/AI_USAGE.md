# AI usage and evaluation

## Development AI

Codex assisted with architecture, backend/frontend implementation, security debugging, tests, visual styling, browser automation and documentation in this task. No subagents were used. The actual material user prompts are preserved in `DEVELOPMENT_PROMPTS.md`; the supplied provider credential is intentionally redacted. No AI-generated stock imagery, fabricated analytics, synthetic mastery, or fake product responses are used in the UI.

## Product AI

The configured live provider is Gemini. The API rejected `gemini-2.5-flash` for this account and explicitly recommended `gemini-3.6-flash`, which is now the configured model. Model choice remains an environment variable. An OpenAI structured-output adapter is also implemented but has not been live-verified in this task.

Gemini performs concept extraction, grounded Tutor answers, question generation, and rubric-based open-answer grading. MCQ grading, mastery updates, adaptive selection, retrieval, compact context construction, recommendations and analytics are deterministic application logic. Recommendations do not pretend to be model-generated. The structured tool boundary is permission checked and has no unrestricted database access.

Provider usage metadata supplies token counts; latency is measured server-side. The system records feature/model, success/failure, retrieved chunk references and estimated cost. Price rates are configurable estimates, not a claim of the account's billed cost. Update `AI_INPUT_PRICE_PER_MILLION` and `AI_OUTPUT_PRICE_PER_MILLION` for the selected provider/model. Prompt bodies and API credentials are not logged.

Schemas, task prompts and the common untrusted-data system instruction are in `backend/study/ai.py` and `learning.py`. Pydantic validates structured outputs, exact source quotes validate provenance, and the server checks rubric identity and question shape before persisting results. AI can still make semantic errors even with valid schemas and citations. Users should inspect the quoted source page.

## Evaluation

The repeatable dataset is the three-page demo PDF. The six curated cases cover retrieval/page relevance, grounded Tutor accuracy, unsupported-question abstention, MCQ structure/scoring, open-answer prompt-injection resistance, and recommendation actionability. `evaluate_ai` records results in the database and `docs/evaluation-results.json`. Live checks are small behavioral regression checks, not a statistical quality benchmark or human-reviewed grading calibration.

Unit tests mock generated outputs and provider failures to test security, schema rejection, permission boundaries, idempotency, adaptive behavior, mastery, job claims/failures/retries and structured-output logging deterministically. They are explicitly separate from live Gemini evaluation and the unmocked browser workflow. See `VERIFICATION.md` for actual runs.

Implementation references: [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs), [Gemini structured outputs](https://ai.google.dev/gemini-api/docs/generate-content/structured-output), [Django deployment](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/).
