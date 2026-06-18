# Skill: YouTube RSS Watcher

Detect new uploads on any YouTube channel — no API key, no quota, no OAuth.

---

## Problem

You want to monitor one or more YouTube channels and act on new videos (summarise them, notify someone, trigger a workflow). The obvious approach — YouTube Data API — requires an API key, has a daily quota (10,000 units), and new videos can take hours to appear.

## Why RSS instead

YouTube exposes a public Atom RSS feed for every channel:

```
https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID
```

- No API key required
- No quota
- Returns the 15 most recent videos
- Updates within minutes of a new upload
- Works from any IP, any environment

The only limitation: 15 videos max per channel. For daily monitoring of active channels, this is plenty.

## How to find a channel ID

Channel IDs start with `UC` and are 24 characters long. Three ways to find one:

**Option 1 — yt-dlp (most reliable):**
```bash
yt-dlp --dump-single-json "https://www.youtube.com/@ChannelHandle/videos" --playlist-items 1 2>/dev/null \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('channel_id'))"
```

**Option 2 — browser source:**
Open the channel page → View Source (Cmd+U) → search for `"channelId"`

**Option 3 — URL:**
If the channel URL is already in the format `youtube.com/channel/UC...`, that last segment is the ID.

## How the deduplication works

A JSON file stores the IDs of videos already processed. On each run:
1. Fetch the RSS feed
2. Compare video IDs to the seen-state file
3. Return only new IDs
4. Write the updated seen-state back

This means "new" means new since the last run, not new in the last 24 hours. Restarting with an empty state file re-processes everything in the feed (useful for initial setup).

## What to change to use this yourself

In `youtube_tool.py`:
- `STATE_DIR` — where your seen-state JSON files live
- The `metal` parameter name is specific to the original project — rename it to whatever makes sense for your use case (e.g. `feed_name`, `topic`, `source`)

In your crew or calling code:
- Pass your own channel IDs
- Pass your own state identifier

---

## Files

- [`youtube_tool.py`](youtube_tool.py) — generic CrewAI `BaseTool` subclass, ready to drop in
