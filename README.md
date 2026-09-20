# sreeram-agent-skills

Reusable patterns extracted from [sreeram-agent-crew](https://github.com/sreeramg-hub/sreeram-agent-crew) — a real, running multi-agent automation built on CrewAI and Anthropic Claude.

Each skill here solves a specific problem that comes up when building personal agentic automations. They are documented for someone who has never seen the original project and wants to adapt the pattern to their own use case.

---

## Skills

| Skill | What it solves |
|---|---|
| [youtube-rss-watcher](skills/youtube-rss-watcher/) | Detect new YouTube uploads without an API key or quota |
| [youtube-caption-transcriber](skills/youtube-caption-transcriber/) | Fetch video transcripts free, no audio download (verified from a home IP; cloud IPs may need a proxy) |
| [crewai-custom-tool-pattern](skills/crewai-custom-tool-pattern/) | The correct shape for a CrewAI `BaseTool` subclass |
| [github-actions-scheduled-agent](skills/github-actions-scheduled-agent/) | Run a Python agent on a cron schedule for free, with persistent state |
| [attributed-sentiment-prompting](skills/attributed-sentiment-prompting/) | Get an LLM to synthesise opinions without fabricating authority |

---

## How to use these

Each skill folder contains:
- A `README.md` explaining what problem it solves, why this approach, and what to change to adapt it
- One or more code files that are self-contained and generic (no hardcoded project-specific values)

Take the code file, drop it into your own project, swap in your config, done.

---

## Relationship to sreeram-agent-crew

These patterns originate in [`sreeram-agent-crew`](https://github.com/sreeramg-hub/sreeram-agent-crew) as real, working tools. Once a pattern is proven stable there, it gets extracted and genericised here — placeholder values instead of project-specific ones, explained without assuming the reader is building the same thing.

This repo follows the working repo, not the other way around.

---

## License

MIT — take any of this, adapt it, use it in your own projects.
