# Skill: GitHub Actions Scheduled Agent

Run a Python AI agent on a cron schedule for free, with persistent state between runs — no servers, no databases.

---

## Problem

You've built a CrewAI (or any Python-based) agent and want it to run automatically on a schedule — daily, hourly, whatever. You need it to remember what it processed last time so it doesn't repeat itself. You don't want to provision servers or manage infrastructure.

## Why GitHub Actions

- **Free tier covers most personal use** — 2,000 minutes/month on public repos, 500 on private. A daily AI agent run typically takes 3–5 minutes. An hourly lightweight check takes under 30 seconds.
- **No server to maintain** — GitHub manages the runners.
- **State persistence via git commit** — instead of a database, commit your state files back to the repo at the end of each run. Git history becomes your audit log.
- **Secrets management built in** — GitHub's encrypted secrets replace a `.env` file on the runner.

## The state commit-back pattern

The key trick: at the end of each workflow run, commit any changed state files back to the repo. Add `[skip ci]` to the commit message to prevent the push from triggering another workflow run.

```yaml
- name: Commit updated state
  run: |
    git config user.name "github-actions[bot]"
    git config user.email "github-actions[bot]@users.noreply.github.com"
    git add state/
    git diff --staged --quiet || git commit -m "chore: update state [skip ci]"
    git push
```

The `git diff --staged --quiet || ...` pattern means "only commit if there are actual changes" — so runs that produce no new state don't create empty commits.

The workflow needs `permissions: contents: write` to push back to the repo.

## Secrets vs Variables

GitHub Actions has two distinct places to store configuration:

| | Secrets | Variables |
|---|---|---|
| **Use for** | API keys, passwords, tokens | Non-sensitive config (channel IDs, thresholds) |
| **Access in workflow** | `${{ secrets.MY_SECRET }}` | `${{ vars.MY_VAR }}` |
| **Visible in logs** | Never (masked as `***`) | Yes |
| **Editable** | Write-only (can't read back) | Read/write |

Important: you **cannot** use `secrets` context in `if:` conditions on steps. If you need to conditionally use a secret, read it into a regular env var inside a `run:` step and check it there.

```yaml
# Wrong — secrets not available in if: conditions
- name: Do thing
  if: ${{ secrets.MY_SECRET != '' }}   # ❌ fails

# Right — check inside the run step
- name: Do thing
  run: |
    if [ -n "$MY_SECRET" ]; then
      echo "secret is set"
    fi
  env:
    MY_SECRET: ${{ secrets.MY_SECRET }}
```

## Explicit LLM configuration

Don't rely on environment-based LLM fallback in your crew code. If `OPENAI_API_KEY` is absent and your code doesn't explicitly configure the LLM, some versions of CrewAI will error with "OPENAI_API_KEY is required" even if you're using Anthropic. Always set the LLM explicitly:

```python
from crewai import LLM
import os

llm = LLM(
    model=os.getenv("MODEL", "anthropic/claude-sonnet-4-6"),
    api_key=os.getenv("ANTHROPIC_API_KEY"),
)

agent = Agent(..., llm=llm)
```

And pass `MODEL` in your workflow env:

```yaml
env:
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  MODEL: anthropic/claude-sonnet-4-6
```

## Make failures loud

A scheduled agent that fails quietly is worse than one that fails loudly. In the original project a broken tool was swallowed by a catch-all `except`, the agent reported "not available yet", and the workflow stayed green for about two months. Habits that prevent it:

- **Fail the run when the important step fails.** If the last step is sending an email or posting a result, let its error propagate (non-zero exit) instead of returning an error string. A red run gets noticed; a green one doesn't.
- **Put a health line in the output.** A footer such as "12/13 sources reachable · summariser: fallback" makes partial failures visible right where you read the result.
- **Commit state only after success.** The commit-back step only runs if earlier steps passed, and your code should record "already processed" items *after* delivering the result. Then a failed run offers the same items again next time instead of silently dropping them.
- **Set `timeout-minutes`.** A hung run otherwise burns runner minutes until GitHub's 6-hour default cuts it off.
- **Don't let a green check mean "ran".** Make it mean "delivered what it was supposed to."

## What to change to use this yourself

In `workflow-template.yml`:
- `cron` expression — set your desired schedule
- `env` block — add your own secrets and variables
- The `git add state/` line — change `state/` to wherever your state files live
- `timeout-minutes` — set it comfortably above a normal run

In your agent code:
- Set the LLM explicitly (see above)
- Load env vars via `python-dotenv` locally; they'll be injected automatically on the runner

---

## Files

- [`workflow-template.yml`](workflow-template.yml) — annotated GitHub Actions workflow template
