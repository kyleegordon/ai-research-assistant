---
name: feature-check
description: Run a per-file quality, security, and test check loop over every file changed on a Linear ticket's branch before marking the feature complete. Use when a ticket/feature is finished and ready to verify before moving it to Done (e.g. "run feature check on AI-22", "is AI-9 ready to close", "check this feature before I mark it done").
---

# Feature Check

Pre-completion gate for a Linear ticket in this repo. Takes a ticket ID
(e.g. `AI-22`), diffs its branch against `main`, and loops over each
changed file running quality, security, and test checks — before the
ticket is allowed to move to Done.

Tickets in this project are flat (no sub-issues/checklists) and each maps
to one branch and a handful of files, so the changed-file list *is* the
natural set of "items" to loop over — not the ticket itself.

## Steps

1. **Resolve the ticket.**
   - Call `mcp__claude_ai_Linear__get_issue` with the given ID to get its
     `gitBranchName` and current status.
   - If the issue has no branch / no commits on that branch, stop and say
     so — nothing to check. Don't skip the check just because the issue
     is already marked Done — status can be set prematurely (e.g. before
     the work is pushed), so it isn't proof the diff was ever verified.

2. **Get the diff and file list.**
   - `git fetch origin main` (if needed), then diff the ticket's branch
     against `main`: `git diff main...<gitBranchName> --name-only` to get
     the changed file list, and keep the full diff around for per-file
     slicing (`git diff main...<gitBranchName> -- <file>`).
   - Drop lockfiles, generated/build output, and anything under
     `chroma_db/` — nothing to review there.

3. **Loop over each changed file.** For every remaining file, run three
   checks scoped to that file's slice of the diff:
   - **Quality** — invoke `/code-review` at `medium` effort. Since
     `/code-review` reasons over "the current diff," scope it by giving
     it just this file's diff slice as context and filtering its findings
     down to lines in this file (correctness bugs, reuse/simplification,
     efficiency).
   - **Security** — invoke `/security-review` the same way, scoped to
     this file's diff slice.
   - **Tests** — check whether this file has corresponding test coverage:
     - Backend (`backend/**/*.py`): is there a `test_<module>.py` that
       exercises it? If yes, run it (`pytest path/to/test -q`); if no test
       exists for a file with non-trivial logic, flag it.
     - Frontend (`frontend/src/**/*.tsx?`): is there a colocated or
       `__tests__` test file? This repo doesn't have a frontend test
       runner set up yet (per Linear), so for frontend files just note
       whether coverage exists — don't invent a runner.

4. **Aggregate.** Build one findings table across all files: file path,
   quality findings, security findings, test status (passing / missing /
   n/a). Only include real findings — don't pad the table with "no issues
   found" noise for clean files, just note the count that passed clean.

5. **Gate completion.**
   - If every file is clean (or only has pre-existing/nitpick-level
     findings) and tests pass: report that AI-XX is ready, then follow
     the existing Linear workflow from CLAUDE.md — move the issue to Done
     and comment with the commit hash that resolved it.
   - If anything fails: report the findings, do **not** touch the Linear
     issue status, and stop. Let the user decide whether to fix first or
     override.

## Out of scope

This skill does not enforce CLAUDE.md's "AI assistance boundaries" (e.g.
flagging whether core RAG logic in `backend/services/{ingest,retrieval,
prompt,stream}.py` was actually hand-written, as opposed to
AI-generated — see AI-26 for why that matters here). That's a separate,
manual review concern, not a quality/security/test check.
