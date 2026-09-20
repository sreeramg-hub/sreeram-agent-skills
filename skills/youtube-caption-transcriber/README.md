# Skill: YouTube Caption Transcriber

Fetch the full transcript of a YouTube video from its captions — free, no audio download, no transcription API.

> **Status: verified from a home connection, unverified from cloud runners.**
> Fetching a 6,800-word transcript from a normal laptop works. Whether it works from GitHub Actions or another datacenter IP depends on YouTube, which often refuses those requests — see [Cloud IPs](#cloud-ips-and-blocking). The original project ended up not depending on transcripts at all (see [What happened in the original project](#what-happened-in-the-original-project)).

---

## Problem

You want the spoken content of a YouTube video as text so an LLM agent can summarise or analyse it. The obvious paths are expensive or slow: downloading audio with `yt-dlp` and sending it to Whisper costs money and time per video, and building your own speech-to-text pipeline is a lot of work.

## Why captions

YouTube generates automatic captions for most videos, and the `youtube-transcript-api` library reads them:

```bash
pip install youtube-transcript-api
```

- **Free** — no API key, no cost per video
- **Fast** — no audio download or processing
- **Good enough** — auto-captions are fine for clear speech; manually uploaded captions are better

The limitation: videos without captions (very new uploads, or channels that disable them) return nothing.

## What the tool returns

An agent can act on the first word of the result:

| Result starts with | Meaning | Retried? |
|---|---|---|
| `[Transcript — N words]` | Success | — |
| `TRANSCRIPT_UNAVAILABLE` | No captions, or disabled. Often just "too new" — try again tomorrow | No |
| `TRANSCRIPT_BLOCKED` | YouTube refused the request (typical on cloud IPs) | No — the same IP gets the same answer |
| `TRANSCRIPT_ERROR` | Anything else (network trouble, bad input) | Yes, up to `TRANSCRIPT_MAX_RETRIES` |

Keeping these apart matters: a tool that reports every failure as "no captions yet" hides real problems (see below).

## Cloud IPs and blocking

YouTube frequently refuses caption requests from datacenter addresses (GitHub Actions, AWS, GCP), which the library reports as `RequestBlocked` / `IpBlocked`. We have **not** verified whether GitHub's runners are affected. If you hit `TRANSCRIPT_BLOCKED`, the library supports routing through a proxy, and this tool reads it from the environment:

| Environment variable | Use |
|---|---|
| `WEBSHARE_PROXY_USERNAME` + `WEBSHARE_PROXY_PASSWORD` | Rotating residential proxies from [webshare.io](https://www.webshare.io) (paid) |
| `YOUTUBE_PROXY_URL` | Any other HTTP(S) proxy, e.g. `http://user:pass@host:port` |

With neither set, the request goes out directly.

**Do not pass cookies.** Older versions of this skill did (`YouTubeTranscriptApi(cookies=...)`). In `youtube-transcript-api` 1.x the constructor only accepts `proxy_config` and `http_client`, so that argument raises a `TypeError`.

## What happened in the original project

In [sreeram-agent-crew](https://github.com/sreeramg-hub/sreeram-agent-crew) this tool ran daily on GitHub Actions with the `cookies=` argument above. Every call raised the `TypeError`, a catch-all `except Exception` swallowed it, and the tool answered "transcript not yet available, will retry". The workflow showed green for about two months while a retry queue grew to 88 videos and runs slowed to ten minutes. Because it failed before sending any request, we never learned whether YouTube would have blocked GitHub's IPs.

Lessons baked into this version:
1. Don't catch-all and relabel — report *why* it failed, with a distinct label per cause.
2. Don't retry a block.
3. Surface failures where you'll see them (in the crew, the digest email now carries a health line).

The crew then switched the video section to **links only** (title, channel description, link) and stopped transcribing. If you need summaries of what was said and can't get transcripts, another option is handing the video URL to a model that can read YouTube links directly; we have not tried that yet.

## What to change to use this yourself

In `transcribe_tool.py`:
- `TRANSCRIPT_FETCH_DELAY` (default 5 s) — pause before each fetch; lower it for a single video
- `TRANSCRIPT_MAX_RETRIES` (default 2) — attempts for transient errors
- The language is `["en"]` in `_run`; change it for other languages
- The tool accepts any YouTube URL form or a bare video ID

---

## Files

- [`transcribe_tool.py`](transcribe_tool.py) — generic CrewAI `BaseTool` subclass, ready to drop in (tested with `youtube-transcript-api` 1.2.x)
