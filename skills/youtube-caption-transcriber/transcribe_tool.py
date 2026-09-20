"""
YouTube Caption Transcriber — CrewAI BaseTool
Fetches a video's transcript from its captions: no API key, no audio download.

Tested with youtube-transcript-api 1.2.x. Works from a normal home connection;
YouTube often refuses these requests from cloud/datacenter IPs, in which case
the tool returns TRANSCRIPT_BLOCKED and you need a proxy (see the README).

Extracted from: https://github.com/sreeramg-hub/sreeram-agent-crew
License: MIT
"""

import os
import re
import time
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from youtube_transcript_api import (
    NoTranscriptFound,
    RequestBlocked,  # also covers IpBlocked
    TranscriptsDisabled,
    YouTubeTranscriptApi,
)
from youtube_transcript_api.proxies import GenericProxyConfig, WebshareProxyConfig

# ── Configuration ─────────────────────────────────────────────────────────────

# Seconds to wait before each fetch, to stay polite when processing many videos.
_FETCH_DELAY_SECONDS = float(os.getenv("TRANSCRIPT_FETCH_DELAY", "5"))

# Attempts for transient errors (network hiccups). A blocked IP is NOT retried:
# asking again from the same address gets the same answer.
_MAX_RETRIES = int(os.getenv("TRANSCRIPT_MAX_RETRIES", "2"))


def _proxy_config():
    """Optional proxy, read from the environment. Returns None for a direct connection.

    WEBSHARE_PROXY_USERNAME / WEBSHARE_PROXY_PASSWORD  rotating residential proxies from webshare.io
    YOUTUBE_PROXY_URL                                   any other HTTP(S) proxy, e.g. http://user:pass@host:port
    """
    username = os.getenv("WEBSHARE_PROXY_USERNAME")
    password = os.getenv("WEBSHARE_PROXY_PASSWORD")
    if username and password:
        return WebshareProxyConfig(proxy_username=username, proxy_password=password)
    proxy_url = os.getenv("YOUTUBE_PROXY_URL")
    if proxy_url:
        return GenericProxyConfig(http_url=proxy_url, https_url=proxy_url)
    return None


def _extract_video_id(url: str) -> str | None:
    match = re.search(r"(?:v=|youtu\.be/|/embed/|/shorts/)([A-Za-z0-9_-]{11})", url)
    if match:
        return match.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url.strip()):
        return url.strip()
    return None


# ── Tool ──────────────────────────────────────────────────────────────────────

class TranscribeVideoInput(BaseModel):
    video_url: str = Field(
        ..., description="YouTube video URL or video ID to transcribe."
    )


class TranscribeVideoTool(BaseTool):
    name: str = "transcribe_video"
    description: str = (
        "Fetches the transcript of a YouTube video from its captions. "
        "Returns the transcript as plain text, or a line starting with "
        "TRANSCRIPT_UNAVAILABLE (no captions), TRANSCRIPT_BLOCKED (YouTube refused "
        "the request) or TRANSCRIPT_ERROR (anything else). "
        "Input: a YouTube video URL or video ID."
    )
    args_schema: Type[BaseModel] = TranscribeVideoInput

    def _run(self, video_url: str) -> str:
        video_id = _extract_video_id(video_url.strip())
        if not video_id:
            return f"TRANSCRIPT_ERROR: could not extract a video ID from: {video_url}"

        last_error = None
        for attempt in range(_MAX_RETRIES):
            time.sleep(_FETCH_DELAY_SECONDS * (2 ** attempt))  # 1x, 2x, 4x ... the base delay
            try:
                api = YouTubeTranscriptApi(proxy_config=_proxy_config())
                transcript_list = api.list(video_id)
                try:
                    transcript = transcript_list.find_manually_created_transcript(["en"])
                except NoTranscriptFound:
                    transcript = transcript_list.find_generated_transcript(["en"])
                text = " ".join(s.text for s in transcript.fetch())
                return f"[Transcript — {len(text.split())} words]\n\n{text}"

            except TranscriptsDisabled:
                return f"TRANSCRIPT_UNAVAILABLE: captions are disabled for video {video_id}."
            except NoTranscriptFound:
                return (
                    f"TRANSCRIPT_UNAVAILABLE: no English captions for video {video_id}. "
                    "Very new uploads often have none yet."
                )
            except RequestBlocked:
                return (
                    f"TRANSCRIPT_BLOCKED: YouTube refused the request for video {video_id}. "
                    "This is typical on cloud IPs; set WEBSHARE_PROXY_USERNAME/PASSWORD or "
                    "YOUTUBE_PROXY_URL to route through a proxy."
                )
            except Exception as e:  # transient network errors: try again
                last_error = e

        return (
            f"TRANSCRIPT_ERROR: could not fetch video {video_id} after "
            f"{_MAX_RETRIES} attempts ({type(last_error).__name__}: {last_error})."
        )
