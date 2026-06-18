"""
YouTube RSS Watcher — CrewAI BaseTool
Detects new uploads on YouTube channels without an API key or quota.

Extracted from: https://github.com/sreeramg-hub/sreeram-agent-crew
License: MIT
"""

import json
import pathlib
import xml.etree.ElementTree as ET
from typing import Type

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# ── Configuration ─────────────────────────────────────────────────────────────

# Directory where seen-state JSON files are stored.
# Each feed gets its own file: state/{feed_name}_seen.json
STATE_DIR = pathlib.Path("state")

NS_ATOM = "{http://www.w3.org/2005/Atom}"
NS_YT = "{http://www.youtube.com/xml/schemas/2015}"
RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

# ── State helpers ──────────────────────────────────────────────────────────────

def _load_seen(feed_name: str) -> set:
    path = STATE_DIR / f"{feed_name}_seen.json"
    if path.exists():
        return set(json.loads(path.read_text()))
    return set()


def _save_seen(feed_name: str, seen: set) -> None:
    STATE_DIR.mkdir(exist_ok=True)
    path = STATE_DIR / f"{feed_name}_seen.json"
    path.write_text(json.dumps(sorted(seen), indent=2))

# ── Tool ──────────────────────────────────────────────────────────────────────

class YoutubeNewUploadsInput(BaseModel):
    channel_ids: str = Field(
        ...,
        description="Comma-separated YouTube channel IDs to check for new uploads.",
    )
    feed_name: str = Field(
        ...,
        description=(
            "Identifier for this feed's seen-state file (e.g. 'tech', 'finance', 'news'). "
            "Each unique feed_name gets its own deduplication state."
        ),
    )


class YoutubeNewUploadsTool(BaseTool):
    name: str = "youtube_new_uploads"
    description: str = (
        "Checks YouTube channels for videos not yet processed. "
        "Returns new video titles, URLs, and published dates. "
        "Updates seen-state so the same video is never returned twice. "
        "Inputs: comma-separated channel_ids, feed_name (any short string identifier)."
    )
    args_schema: Type[BaseModel] = YoutubeNewUploadsInput

    def _run(self, channel_ids: str, feed_name: str) -> str:
        feed_name = feed_name.lower().strip()
        seen = _load_seen(feed_name)
        new_videos = []

        for channel_id in [c.strip() for c in channel_ids.split(",") if c.strip()]:
            url = RSS_URL.format(channel_id=channel_id)
            try:
                resp = requests.get(
                    url, timeout=10, headers={"User-Agent": "Mozilla/5.0"}
                )
                resp.raise_for_status()
                root = ET.fromstring(resp.text)
            except Exception as e:
                new_videos.append(f"[ERROR fetching channel {channel_id}: {e}]")
                continue

            channel_title = getattr(
                root.find(f"{NS_ATOM}title"), "text", channel_id
            )

            for entry in root.findall(f"{NS_ATOM}entry"):
                vid_id_el = entry.find(f"{NS_YT}videoId")
                if vid_id_el is None:
                    continue
                vid_id = vid_id_el.text
                if vid_id in seen:
                    continue

                title = getattr(entry.find(f"{NS_ATOM}title"), "text", "Unknown title")
                published = getattr(
                    entry.find(f"{NS_ATOM}published"), "text", ""
                )[:10]
                video_url = f"https://www.youtube.com/watch?v={vid_id}"

                new_videos.append(
                    f"- [{channel_title}] {published} | {title}\n"
                    f"  URL: {video_url}\n"
                    f"  ID: {vid_id}"
                )
                seen.add(vid_id)

        _save_seen(feed_name, seen)

        if not new_videos:
            return f"No new videos found for feed '{feed_name}' across the provided channels."

        return f"Found {len(new_videos)} new video(s):\n\n" + "\n".join(new_videos)
