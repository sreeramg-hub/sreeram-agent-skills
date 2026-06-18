# Skill: Attributed Sentiment Prompting

A prompting pattern for getting an LLM to synthesise opinions from sources without fabricating its own unattributed authority.

---

## Problem

When you ask an LLM to summarise opinions from multiple sources (analyst reports, YouTube videos, articles), it tends to flatten them:

> "Gold is expected to reach $4,500 by Q3."

That reads like a fact. It isn't — it's someone's prediction. The LLM synthesised across sources and produced a statement with no attribution, no uncertainty, and no indication that a real person with a specific track record said it.

This matters more in some domains than others. In financial content, health information, political commentary, or any field where "who said it" is part of the signal, unattributed synthesis is actively misleading.

## The pattern

Force attribution at the prompt level, not just as a general instruction. Two complementary techniques:

### 1. Explicit attribution rule in the backstory/goal

```yaml
backstory: >
  You never state a prediction as fact. Every price target, opinion, or
  forecast must be attributed to the specific person or source who stated it —
  e.g. "Jordan Roy-Byrne of TheDailyGold said...", "According to Kitco's
  guest X...", "In the video titled '...', the presenter argued...".
  When sources disagree, you note the disagreement explicitly rather than
  picking a side or averaging the views.
```

### 2. Structured expected output that makes attribution visible

```yaml
expected_output: >
  For each video: channel name, presenter name (if identifiable), 
  publication date, and a 3–5 sentence summary where every claim is
  prefixed with who made it.
  If sources contradict each other, include a "Sources disagree:" note
  with both positions attributed separately.
  Do not include any price target or directional view that is not
  tied to a named source.
```

### 3. Editor role for the final consolidation agent

When a second agent consolidates multiple sources, give it an editor role — not an analyst role:

```yaml
role: Daily Digest Editor
backstory: >
  You are an editor, not an analyst. You receive fully attributed research
  from specialist agents. Your job is to organise and clarify — not to add
  new market opinions, not to draw conclusions the source agents didn't draw,
  and not to flatten attributed opinions into unattributed statements.
  Preserve every attribution exactly as given to you.
```

## Why this works

The LLM's default is to synthesise and smooth — that's what next-token prediction optimises for. The backstory and expected output create a counter-pressure: the model is being evaluated on whether attributions are present, so it keeps them. The editor framing on the final agent prevents the synthesis step from silently re-introducing unattributed claims.

## The disclaimer pattern

For any output that involves aggregated opinions, add a required disclaimer to the task description:

```yaml
description: >
  ...
  End the email with this exact paragraph:
  "This digest is compiled from public sources for personal research only.
  All opinions and price targets are attributed to their original sources
  and do not represent financial advice."
```

Making the disclaimer part of the task (not just a general instruction) means it's part of the expected output and the agent treats its absence as a failure.

## When to use this

- Financial market analysis from multiple sources
- Medical or health information summaries
- Political or policy commentary
- Product reviews or recommendations
- Any domain where "who said it" carries weight

## When not to bother

If the downstream consumer doesn't care about source attribution — e.g. you're summarising your own notes, or producing internal technical documentation — this adds friction without benefit.

---

## Files

- [`example-prompts.md`](example-prompts.md) — copy-paste examples for agents.yaml and tasks.yaml
