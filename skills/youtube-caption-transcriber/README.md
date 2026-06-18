# Skill: YouTube Caption Transcriber

Fetch the full transcript of any YouTube video — free, instant, no audio download, no transcription API.

---

## Problem

You want to get the spoken content of a YouTube video as text so an LLM agent can summarise, analyse, or extract information from it. The obvious paths are expensive or slow: downloading audio with `yt-dlp` and sending it to Whisper costs money and takes time per video. Building a speech-to-text pipeline yourself is a significant engineering effort.

## Why captions instead

YouTube generates automatic captions for most videos. These are available via the `youtube-transcript-api` Python library:

```bash
pip install youtube-transcript-api
```

- **Free** — no API key, no cost per video
- **Instant** — no audio download, no processing time
- **Accurate** — auto-captions are good for clear speech; manually uploaded captions are better
- **Works for most major channels** — the vast majority of established YouTube channels have auto-captions enabled

The limitation: if a video has no captions (rare for established channels, common for very new uploads or channels with disabled captions), this approach returns nothing. A fallback to `yt-dlp` + Whisper can handle those cases.

## Rate limiting

Making many transcript requests in quick succession from the same IP can trigger a temporary block from YouTube (usually minutes to an hour). Two mitigations:

1. **Delay between requests** — configurable via `TRANSCRIPT_FETCH_DELAY` env var (default 5 seconds)
2. **Browser cookies** — pass a `cookies.txt` file (Netscape format, exported from your browser) to bypass IP-based blocks. Set `YOUTUBE_COOKIES_FILE=path/to/cookies.txt` in your environment. This is especially important on cloud runners (GitHub Actions, AWS, GCP) whose IPs YouTube frequently blocks.

To export cookies: install the "Get cookies.txt LOCALLY" browser extension, visit YouTube while logged in, export, save as `cookies.txt`. **Never commit this file.**

## What to change to use this yourself

In `transcribe_tool.py`:
- `_FETCH_DELAY_SECONDS` — adjust if you're processing many videos per run
- `_MAX_RETRIES` — increase for more resilience on flaky connections
- The tool accepts any YouTube URL format or bare video ID — no changes needed for those

---

## Files

- [`transcribe_tool.py`](transcribe_tool.py) — generic CrewAI `BaseTool` subclass, ready to drop in
