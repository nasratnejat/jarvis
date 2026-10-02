import re
import urllib.parse
import webbrowser

from app.integrations.browser import (
    WEBSITES,
    open_website,
    google_search,
)


YOUTUBE_SEARCH_PREFIX = "ytsearch1:"


def _youtube_first_result(query):
    """
    Resolve the first YouTube search result.

    Returns the YouTube video URL or None.
    """

    if not query:
        return None

    query = query.strip()

    if not query:
        return None

    try:
        import yt_dlp

        options = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": True,
        }

        search_term = (
            YOUTUBE_SEARCH_PREFIX
            + query
        )

        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(
                search_term,
                download=False,
            )

        if not info:
            return None

        entries = info.get("entries")

        if not entries:
            return None

        first = entries[0]

        if not first:
            return None

        video_id = first.get("id")

        if not video_id:
            return None

        return (
            "https://www.youtube.com/watch?v="
            + video_id
        )

    except Exception as e:
        print(
            "[YOUTUBE ERROR]",
            repr(e),
        )

        return None


def _extract_youtube_query(command):
    if not command:
        return None

    c = command.strip()

    if not c:
        return None

    patterns = (
        # play X on YouTube
        r"^(?:play|listen\s+to|watch)\s+(.+?)\s+"
        r"(?:on|in)\s+youtube$",

        # search X on YouTube
        r"^(?:search|find)\s+(.+?)\s+"
        r"(?:on|in)\s+youtube$",

        # YouTube X
        r"^youtube\s+(.+)$",

        # search YouTube for X
        r"^(?:search|find)\s+youtube\s+"
        r"(?:for\s+)?(.+)$",

        # play X YouTube
        r"^(?:play|listen\s+to|watch)\s+(.+?)\s+"
        r"youtube$",
    )

    for pattern in patterns:
        match = re.match(
            pattern,
            c,
            re.IGNORECASE,
        )

        if match:
            query = match.group(1).strip()

            if query:
                return query

    return None


def is_youtube_command(command):
    if not command:
        return False

    c = command.lower().strip()

    if not c:
        return False

    return (
        _extract_youtube_query(c)
        is not None
    )


def handle_youtube_command(command):
    if not command:
        return None

    query = _extract_youtube_query(command)

    if not query:
        return None

    print(
        f"[YOUTUBE] Searching for: {query!r}"
    )

    video_url = _youtube_first_result(
        query
    )

    if not video_url:
        return (
            f"I could not find a YouTube result "
            f"for {query}, Sir."
        )

    print(
        f"[YOUTUBE] Opening: {video_url}"
    )

    try:
        opened = webbrowser.open(
            video_url,
            new=2,
        )

        if opened:
            return (
                f"Playing the first YouTube result "
                f"for {query}, Sir."
            )

        return (
            f"I found the YouTube result for "
            f"{query}, but I could not open it, Sir."
        )

    except Exception:
        return (
            f"I found the YouTube result for "
            f"{query}, but I could not open it, Sir."
        )


def is_browser_command(command):
    if not command:
        return False

    c = command.lower().strip()

    if not c:
        return False

    # --------------------------------------------------------
    # YOUTUBE
    # --------------------------------------------------------

    if is_youtube_command(c):
        return True

    # --------------------------------------------------------
    # DIRECT WEBSITE
    # --------------------------------------------------------

    if c in WEBSITES:
        return True

    # --------------------------------------------------------
    # OPEN WEBSITE
    # --------------------------------------------------------

    if c.startswith("open "):
        target = c[5:].strip()

        if target in WEBSITES:
            return True

    # --------------------------------------------------------
    # GOOGLE / SEARCH
    # --------------------------------------------------------

    if re.match(
        r"^(?:google|search(?: for)?)\s+(.+)$",
        c,
        re.IGNORECASE,
    ):
        return True

    return False


def handle_browser_command(command):
    if not command:
        return None

    c = command.lower().strip()

    # --------------------------------------------------------
    # YOUTUBE
    # --------------------------------------------------------

    result = handle_youtube_command(c)

    if result:
        return result

    # --------------------------------------------------------
    # OPEN WEBSITE
    # --------------------------------------------------------

    if c.startswith("open "):
        target = c[5:].strip()

        result = open_website(target)

        if result:
            return (
                f"Opening {target.title()}, Sir."
            )

    # --------------------------------------------------------
    # DIRECT WEBSITE
    # --------------------------------------------------------

    if c in WEBSITES:
        result = open_website(c)

        if result:
            return (
                f"Opening {c.title()}, Sir."
            )

    # --------------------------------------------------------
    # GOOGLE SEARCH
    # --------------------------------------------------------

    search_match = re.match(
        r"^(?:google|search(?: for)?)\s+(.+)$",
        c,
        re.IGNORECASE,
    )

    if search_match:
        query = search_match.group(1).strip()

        result = google_search(query)

        if result:
            return (
                f"Searching for {query}, Sir."
            )

    return None