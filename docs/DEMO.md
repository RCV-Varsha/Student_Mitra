# Demo script (about 4 minutes)

1. **Home (15s)** - Sign in. Show continue learning, actual event counts and estimated mastery. Explain that the sample PDF is labeled demo data; scores are real attempts.
2. **Organize (25s)** - Create a Space with a description. Create a Project with description and learning goal.
3. **Material (30s)** - Upload `demo-material.pdf`. Show queued/processing/ready and page count. Explain that an independent worker continues after the browser closes. Show the unsupported-scan message/retry behavior if needed.
4. **Tutor (40s)** - Ask 'Where does the Calvin cycle occur?' Open the linked document/page and compare the quoted evidence. Ask 'What is the current price of bitcoin?' Show insufficient evidence.
5. **Practice (60s)** - Generate and answer an MCQ. Show the selection evidence. Generate an open-ended question, explain the concept, and inspect individual rubric feedback.
6. **Growth (25s)** - Show before/after mastery, evidence count, strengths/weaknesses and a concrete recommendation. Explain that mastery is an estimate.
7. **Analytics (20s)** - Show real activity and assessment charts plus AI model, tokens, estimated cost and latency. Switch to global analytics.
8. **Admin (30s)** - Sign in as administrator. Filter by learner/project, inspect assessments, job status/failures, worker health and live evaluation results.
9. **Mobile (15s)** - Open sidebar and navigate at 390px width. Show readable cards and contained tables.

`frontend/verify-browser.mjs` automates this workflow against the running local application without mocking AI. Recording is silent and may include provider waiting time. See `VERIFICATION.md` for the actual video outcome.

## Actual recording

`demo.mp4` is an edited, silent recording of real browser operations: initial Space/Project/upload flow and a paced walkthrough of real persisted results. Captions disclose the live open-grading quota blocker. It does not fabricate a completed open assessment. `record-demo.mjs` uses saved results and makes no provider calls; the full live test remains separately available in `verify-browser.mjs`.
