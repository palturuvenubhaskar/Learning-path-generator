"""Tests for YouTube link parsing used by the in-app player."""

from __future__ import annotations

import pytest

from youtube import thumbnail_url, video_id, watch_url

VIDEO = "rfscVS0vtbw"


@pytest.mark.parametrize(
    "url",
    [
        f"https://www.youtube.com/watch?v={VIDEO}",
        f"https://youtube.com/watch?v={VIDEO}&t=90s",
        f"https://www.youtube.com/watch?app=desktop&v={VIDEO}",
        f"https://m.youtube.com/watch?v={VIDEO}",
        f"https://youtu.be/{VIDEO}",
        f"https://youtu.be/{VIDEO}?si=tracking",
        f"https://www.youtube.com/shorts/{VIDEO}",
        f"https://www.youtube.com/live/{VIDEO}",
        f"https://www.youtube.com/embed/{VIDEO}",
        f"https://www.youtube-nocookie.com/embed/{VIDEO}",
        f"www.youtube.com/watch?v={VIDEO}",
        f"  https://youtu.be/{VIDEO}  ",
    ],
)
def test_playable_links_are_parsed(url):
    assert video_id(url) == VIDEO


@pytest.mark.parametrize(
    "url",
    [
        "",
        "   ",
        None,
        "https://www.youtube.com/",
        "https://www.youtube.com/results?search_query=python+tutorial",
        "https://www.youtube.com/@freecodecamp",
        "https://www.youtube.com/channel/UC8butISFwT-Wl7EV0hUK0BQ",
        "https://www.youtube.com/playlist?list=PLWKjhJtqVAbleDe3_ZA8h3AO2rXar-q2V",
        "https://www.youtube.com/watch?v=too-short",
        "https://www.youtube.com/watch?v=waytoolongvideoid",
        "https://example.com/watch?v=rfscVS0vtbw",
        "https://notyoutube.com/watch?v=rfscVS0vtbw",
    ],
)
def test_non_videos_are_rejected(url):
    assert video_id(url) is None


def test_watch_url_is_normalized():
    assert watch_url(VIDEO) == f"https://www.youtube.com/watch?v={VIDEO}"


def test_thumbnail_is_a_static_16_by_9_poster():
    assert thumbnail_url(VIDEO) == f"https://i.ytimg.com/vi/{VIDEO}/mqdefault.jpg"
