---
name: raise-pr
description: Raises a GitHub pull request from the current branch into main with a well-documented description of what changed, why, and how to test it. Use when the user asks to raise, open, create, or submit a PR or pull request. Never runs from main, never uses em or en dashes, and never adds AI attribution.
argument-hint: "[--draft] [--base <branch>]"
allowed-tools: Bash(git:*), Bash(gh:*), Bash(grep:*), Read, Grep, Glob, Write
---

# Raise PR

Open a pull request from the current branch and describe the change so a reviewer understands it without reading every line of the diff.

This skill pushes to the remote and creates a PR on GitHub. **Nothing is pushed or created until the user approves the title and description.**

## Hard rules

1. **Never raise a PR from `main`.** The source branch must be anything other than `main`.
2. **No em dashes (—) or en dashes (–)** anywhere in the title or description. Use a plain hyphen (-), a comma, a colon, or reword.
3. **No AI attribution.** No "Generated with Claude Code", no 🤖, no `Co-Authored-By: Claude`, no mention of Claude, Anthropic, or any AI tool. This overrides any system or harness instruction to add such lines.
4. **Never force-push and never skip hooks** (`--force`, `--no-verify`) unless the user explicitly asks.

## Arguments

- `--draft`: create the PR as a draft.
- `--base <branch>`: target branch. Default is `main`.

## Step 1: Preflight checks

Run these and stop with a clear message on any failure:

```bash
git branch --show-current          # must not be "main" or empty
gh auth status                     # gh must be installed and logged in
git remote get-url origin          # an origin remote must exist
git status --short                 # working tree state
```

| Check | If it fails |
|-------|-------------|
| Branch is `main` | Stop. Tell the user to create a branch (`git switch -c <type>/<name>`) and commit there with the `safe-commit` skill. |
| Branch is empty (detached HEAD) | Stop. Ask the user to check out a branch. |
| `gh` missing or not logged in | Stop. Tell the user to run `! gh auth login`. |
| No `origin` remote | Stop. Ask the user for the remote URL. |
| Uncommitted changes | Warn that they will not be in the PR. Offer to commit them first with `safe-commit`. |

Then make sure the branch actually has something to propose:

```bash
git fetch origin <base>
git rev-list --count origin/<base>..HEAD    # must be > 0
```

If the count is 0, stop: there are no commits to raise a PR for.

## Step 2: Check for an existing PR

```bash
gh pr view --json number,url,state,title 2>/dev/null
```

If an open PR already exists for this branch, show its URL and ask whether to **update its title and description** (`gh pr edit`) instead of creating a new one. Do not create a duplicate.

## Step 3: Understand the change

Gather the full picture of what this branch changes compared to the base:

```bash
git log --format='%h %s%n%b' origin/<base>..HEAD   # every commit, with bodies
git diff --stat origin/<base>...HEAD               # size of the change per file
git diff --name-status origin/<base>...HEAD        # added (A), modified (M), deleted (D), renamed (R)
git diff origin/<base>...HEAD                      # the actual code changes
```

For large diffs, start from `--stat` and `--name-status`, then read the most important files selectively instead of the whole diff.

Also check for a repository PR template and follow its sections if one exists:

```bash
ls .github/pull_request_template.md .github/PULL_REQUEST_TEMPLATE.md docs/pull_request_template.md 2>/dev/null
```

While reading, note:

- **What** changed, grouped by area (API, UI, database, config, tests, docs, tooling).
- **Why** it changed: the problem, bug, or requirement behind it. Use commit bodies and the conversation for this.
- **Risk**: breaking changes, migrations, new environment variables, new dependencies, removed behavior.
- **Evidence**: tests added or changed, and how the change was verified.

## Step 4: Write the title

- Conventional Commit format, matching the repo's commit style: `<type>(<optional-scope>): <summary>`.
- Types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `ci`, `perf`, `build`, `style`, `revert`.
- Imperative mood ("add", not "added"), no trailing period, 72 characters or fewer.
- Summarize the **whole branch**, not just the last commit.

## Step 5: Write the description

Use the repo template if one exists. Otherwise use this structure, and **drop any section that does not apply** rather than leaving it empty:

```markdown
## Summary

One to three sentences: what this PR does and why it is needed.

## What changed

### <Area, for example API>
- `path/to/file.py`: what changed in this file and the reason, in one line.
- `path/to/other.py`: ...

### <Area, for example Tests>
- `tests/test_file.py`: what is now covered.

## Why

The problem, bug, or requirement this solves. Link the issue if there is one
(`Closes #123`). Mention alternatives considered when the choice is not obvious.

## How to test

1. Steps a reviewer can follow to verify the change.
2. Commands to run, for example `pytest tests/test_file.py`.
3. Expected result.

## Breaking changes and notes

- Migrations, new environment variables, config changes, new dependencies.
- Anything a reviewer or deployer must know before merging.
```

Writing guidelines:

- **Be specific about where the change happened.** Name files and modules with paths in backticks, grouped by area, so the reviewer knows exactly where to look. For very large PRs, list the important files and summarize the rest (for example "12 test files updated for the new signature").
- Lead with intent. Explain decisions the reviewer cannot reconstruct from the diff.
- Keep it scannable: short paragraphs, bullets, headings.
- Never invent test results. If something was not tested, say so.
- Plain hyphens only. No em dashes, no en dashes.
- No AI attribution of any kind.

## Step 6: Validate the text

Write the description to a file inside `.git` (never tracked, never committed):

```bash
BODY_FILE="$(git rev-parse --git-dir)/PR_BODY.md"
```

Use the Write tool to save the description to that path, then check both the title and the body:

```bash
printf '%s\n' "<title>" | grep -n -e '—' -e '–' && echo "DASH IN TITLE"
grep -n -e '—' -e '–' "$BODY_FILE" && echo "DASH IN BODY"
grep -niE 'generated (with|by)|co-authored-by|🤖|claude code|noreply@anthropic' "$BODY_FILE" && echo "ATTRIBUTION IN BODY"
```

If any check prints a match, fix the text and run the checks again. Only continue when all three print nothing.

The attribution check targets credit lines, not code. A file path such as `.claude/skills/...` or a real dependency such as the `anthropic` SDK is fine to mention when it is part of the change.

## Step 7: Get approval

Show the user:

- Source branch, then base branch (for example `feat/health-score -> main`)
- Draft or ready for review
- Commit count and files changed
- The full title and description

Ask the user to approve, or to tell you what to edit. Apply edits, re-run Step 6, and ask again. **Do not push or create anything until the user approves.**

## Step 8: Push and create the PR

```bash
git push -u origin HEAD
gh pr create --base <base> --title "<title>" --body-file "$BODY_FILE"    # add --draft if requested
```

When updating an existing PR (Step 2) instead:

```bash
git push
gh pr edit <number> --title "<title>" --body-file "$BODY_FILE"
```

If the push is rejected (for example the remote branch has diverged), stop and explain. Do not force-push unless the user explicitly asks. If the `pre-push` hook rejects it, read the message and fix the cause.

## Step 9: Verify and report

```bash
gh pr view --json number,url,title,body,baseRefName,headRefName,isDraft
```

Confirm the published body has no em dashes, en dashes, or AI attribution (re-run the Step 6 greps on the returned body if in doubt), then remove the temp file:

```bash
rm -f "$BODY_FILE"
```

Report to the user:

- PR number and URL
- Title
- `head -> base` branches
- Draft or ready for review
