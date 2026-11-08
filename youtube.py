"""YouTube link parsing for thumbnails and in-app playback.

Only real videos can be embedded. Channel pages, playlists, search results and
the home page return ``None`` so the UI keeps them as plain links.
"""

from __future__ import annotations

import re
from typing import Optional
from urllib.parse import parse_qs, urlparse

THE_YOUTUBE_HOSTS = {
    "youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtube-nocookie.com",
    "youtu.be",
}
VIDEO_PATH_PREFIXES = ("shorts", "live", "embed", "v")
VIDEO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")


def video_id(url: str) -> Optional[str]:
    """Return the 11-character video id for a playable YouTube link."""
    if not url or not url.strip():
        return None

    raw = url.strip()
    if "://" not in raw:
        raw = f"https://{raw}"

    try:
        parsed = urlparse(raw)
    except ValueError:
        return None

    host = (parsed.netloc or "").lower().split(":")[0]
    if host.startswith("www."):
        host = host[4:]
    if host not in THE_YOUTUBE_HOSTS:
        return None

    if host == "youtu.be":
        candidate = parsed.path.strip("/").split("/")[0]
    else:
        parts = [part for part in parsed.path.split("/") if part]
        if parts[:1] == ["watch"]:
            candidate = parse_qs(parsed.query).get("v", [""])[0]
        elif len(parts) >= 2 and parts[0] in VIDEO_PATH_PREFIXES:
            candidate = parts[1]
        else:
            candidate = ""

    return candidate if VIDEO_ID_PATTERN.fullmatch(candidate) else None


def watch_url(video: str) -> str:
    """Normalized link, accepted by ``st.video`` and by a normal browser."""
    return f"https://www.youtube.com/watch?v={video}"


def thumbnail_url(video: str) -> str:
    """Static 16:9 poster, so no YouTube player has to load before a click."""
    return f"https://i.ytimg.com/vi/{video}/mqdefault.jpg"
