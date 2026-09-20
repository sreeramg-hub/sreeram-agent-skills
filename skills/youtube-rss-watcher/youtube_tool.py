"""
YouTube RSS Watcher — CrewAI BaseTool
Detects new uploads on YouTube channels without an API key or quota.

Returns each new video's channel, title, date, link and the channel-written
description. It does not read the video itself, so callers should not claim
anything about what was said in it.

Extracted from: https://github.com/sreeramg-hub/sreeram-agent-crew
License: MIT
"""

import json
import pathlib
import re
import time
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
NS_MEDIA = "{http://search.yahoo.com/mrss/}"
RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

# The feed endpoint is occasionally flaky (transient 404s), so retry a few times.
FETCH_ATTEMPTS = 3

# Descriptions are written by the channel: keep them short and strip links
# (sponsor/affiliate spam) before they reach an LLM prompt.
DESCRIPTION_MAX_CHARS = 400

# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_seen(feed_name: str) -> set:
    path = STATE_DIR / f"{feed_name}_seen.json"
    if path.exists():
        return set(json.loads(path.read_text()))
    return set()


def _save_seen(feed_name: str, seen: set) -> None:
    STATE_DIR.mkdir(exist_ok=True)
    path = STATE_DIR / f"{feed_name}_seen.json"
    path.write_text(json.dumps(sorted(seen), indent=2))


def _fetch_feed(channel_id: str) -> ET.Element:
    last_error = None
    for attempt in range(FETCH_ATTEMPTS):
        if attempt:
            time.sleep(2 * attempt)
        try:
            resp = requests.get(
                RSS_URL.format(channel_id=channel_id),
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            resp.raise_for_status()
            return ET.fromstring(resp.text)
        except Exception as e:
            last_error = e
    raise last_error


def _short_description(entry: ET.Element) -> str:
    el = entry.find(f"{NS_MEDIA}group/{NS_MEDIA}description")
    text = (el.text or "") if el is not None else ""
    text = re.sub(r"https?://\S+", "", text)
    text = " ".join(text.split())
    if len(text) > DESCRIPTION_MAX_CHARS:
        text = text[:DESCRIPTION_MAX_CHARS].rstrip() + "…"
    return text

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
        "Returns each new video's channel, title, published date, link and the "
        "channel-written description (the video itself is not read). "
        "Updates seen-state so the same video is never returned twice. "
        "Inputs: comma-separated channel_ids, feed_name (any short string identifier)."
    )
    args_schema: Type[BaseModel] = YoutubeNewUploadsInput

    def _run(self, channel_ids: str, feed_name: str) -> str:
        feed_name = feed_name.lower().strip()
        seen = _load_seen(feed_name)
        new_videos, errors, checked = [], [], []

        for channel_id in [c.strip() for c in channel_ids.split(",") if c.strip()]:
            try:
                root = _fetch_feed(channel_id)
            except Exception as e:
                errors.append(f"[ERROR fetching channel {channel_id}: {e}]")
                continue

            channel_title = getattr(root.find(f"{NS_ATOM}title"), "text", channel_id)
            checked.append(channel_title)

            for entry in root.findall(f"{NS_ATOM}entry"):
                vid_id_el = entry.find(f"{NS_YT}videoId")
                if vid_id_el is None:
                    continue
                vid_id = vid_id_el.text
                if vid_id in seen:
                    continue

                title = getattr(entry.find(f"{NS_ATOM}title"), "text", "Unknown title")
                published = getattr(entry.find(f"{NS_ATOM}published"), "text", "")[:10]
                description = _short_description(entry)

                new_videos.append(
                    f"- [{channel_title}] {published} | {title}\n"
                    f"  URL: https://www.youtube.com/watch?v={vid_id}\n"
                    f"  Description (written by the channel, unverified): "
                    f"{description or '(none provided)'}"
                )
                seen.add(vid_id)

        _save_seen(feed_name, seen)

        parts = []
        if new_videos:
            parts.append(f"Found {len(new_videos)} new video(s):\n" + "\n".join(new_videos))
        else:
            parts.append(
                f"No new videos found for feed '{feed_name}'. "
                f"Channels checked: {', '.join(checked) or 'none'}."
            )
        if errors:
            # Reported separately so a failed fetch is never mistaken for "no new videos".
            parts.append("Some channels could not be checked this time:\n" + "\n".join(errors))
        return "\n\n".join(parts)
