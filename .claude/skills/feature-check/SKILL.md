---
name: feature-check
description: Run a per-file quality, security, and test check loop over every file changed on a Linear ticket's branch before marking the feature complete. Use when a ticket/feature is finished and ready to verify before moving it to Done (e.g. "run feature check on AI-22", "is AI-9 ready to close", "check this feature before I mark it done").
---

# Feature Check

Pre-completion gate for a Linear ticket in this repo. Takes a ticket ID
(e.g. `AI-22`), diffs its branch against `main`, and checks quality,
security, and test coverage across the changed files — before the ticket
is allowed to move to Done.

Tickets in this project are flat (no sub-issues/checklists) and each maps
to one branch and a handful of files, so the changed-file list *is* the
natural set of "items" to check — not the ticket itself.

## Steps

1. **Resolve the ticket.**
   - Call `mcp__claude_ai_Linear__get_issue` with the given ID to get its
     `gitBranchName` and current status.
   - If the issue has no branch / no commits on that branch, stop and say
     so — nothing to check. Don't skip the check just because the issue
     is already marked Done — status can be set prematurely (e.g. before
     the work is pushed), so it isn't proof the diff was ever verified.

2. **Get the diff and classify each file.**
   - `git fetch origin main` (if needed), then diff the ticket's branch
     against `main` with rename detection so moved files don't show up as
     an unrelated add+delete pair:
     `git diff main...<gitBranchName> --name-status -M`.
   - This gives you a status per file: `A` (added), `M` (modified), `D`
     (deleted), or `R100`/`R<NN>` (renamed, with old and new paths).
   - Drop lockfiles, generated/build output, anything under `chroma_db/`,
     and binary files (images, PDFs in `backend/uploads/`) — nothing to
     review there.
   - Keep the full diff around for per-file slicing:
     `git diff main...<gitBranchName> -- <file>`.
   - Handle each status differently:
     - **A / M**: full quality, security, and test checks apply (step 3).
     - **D**: no code left to review, so skip quality/security — but
       check whether a test file existed for it and wasn't removed too
       (a dangling test for deleted code will fail or silently rot).
     - **R**: review under the new path; if the diff for a pure rename is
       empty, quality/security checks are moot, but still worth noting
       whether tests or imports elsewhere still reference the old path.

3. **Quality and security — one pass over the whole diff, not one per file.**
   - Invoke `/code-review` at `medium` effort **once**, scoped to the
     full ticket diff (`main...<gitBranchName>`), not sliced per file.
     `/code-review` already reasons over "the current diff" as a unit —
     reviewing files together (rather than in isolation) also means it
     can catch cross-file issues, e.g. a frontend change whose backend
     counterpart changed inconsistently.
   - Invoke `/security-review` the same way, once, over the full diff.
   - Bucket both sets of findings by file afterward for the aggregate
     table in step 5. This turns what used to be `2 × N` separate review
     invocations (N = changed files) into 2 total — the main lever for
     keeping this check fast and cheap on tickets that touch many files.
   - Exception: if a single file's diff is huge (roughly 500+ changed
     lines) relative to the rest of the ticket, it can dilute a whole-diff
     review's attention. Give that file its own follow-up `/code-review`
     pass so it isn't shortchanged.

4. **Test coverage — per-file loop
   - Skip files that are themselves tests (`test_*.py`, `*.test.tsx?`) —
     a test doesn't need a test written against it.
   - For each remaining `A`/`M` file, first judge whether the change is
     trivial or not — trivial means formatting, comments, type
     annotations, import reordering, or constant/config value tweaks with
     no behavior change; anything that adds or changes a function body,
     branch, loop, or error-handling path is non-trivial and should have
     coverage. Trivial changes get marked n/a, not flagged.
   - **Backend** (`backend/**/*.py`, non-trivial): does `test_<module>.py`
     exist?
     - If it exists **and is also in this diff's changed-file list**,
       coverage was actively updated alongside the behavior — run it
       (`pytest path/to/test -q`) and report pass/fail.
     - If it exists but **isn't** in the changed-file list, the behavior
       changed but the test wasn't touched — run it, but flag it
       separately as "existing test not updated — verify it still
       exercises the new behavior" rather than reporting a clean pass.
       A passing stale test can just mean it never reached the changed
       code.
     - If no test file exists at all, flag it as missing coverage.
   - **Frontend** (`frontend/src/**/*.tsx?`, non-trivial): this repo has
     no frontend test runner set up yet (per Linear), so just note
     whether a colocated or `__tests__` test file exists and, if one
     does, whether it's part of this diff — don't invent a runner or try
     to execute anything.
   - Other file types (config, styles, docs, etc.): n/a, not flagged.

5. **Aggregate.** Build one findings table across all files: file path,
   change type (A/M/D/R), quality findings, security findings, test
   status (passing / stale-not-updated / missing / n/a). Only include
   real findings — don't pad the table with "no issues found" noise for
   clean files, just note the count that passed clean.

6. **Gate completion.**
   - If every file is clean (or only has pre-existing/nitpick-level
     findings), tests pass, and nothing is flagged as missing/stale
     coverage: report that AI-XX is ready, then follow the existing
     Linear workflow from CLAUDE.md — move the issue to Done and comment
     with the commit hash that resolved it.
   - If anything fails: report the findings, do **not** touch the Linear
     issue status, and stop. Let the user decide whether to fix first or
     override.

## Out of scope

This skill does not enforce CLAUDE.md's "AI assistance boundaries" (e.g.
flagging whether core RAG logic in `backend/services/{ingest,retrieval,
prompt,stream}.py` was actually hand-written, as opposed to
AI-generated — see AI-26 for why that matters here). That's a separate,
manual review concern, not a quality/security/test check.
