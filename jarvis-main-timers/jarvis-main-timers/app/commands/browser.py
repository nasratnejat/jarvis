import re

from app.integrations.browser import (
    WEBSITES,
    open_website,
    google_search,
)


def is_browser_command(command):
    if not command:
        return False

    c = command.lower().strip()

    # Direct website
    if c in WEBSITES:
        return True

    # Open website
    if c.startswith("open "):
        target = c[5:].strip()

        if target in WEBSITES:
            return True

    # Google / search
    if re.match(
        r"^(?:google|search(?: for)?)\s+(.+)$",
        c
    ):
        return True

    return False


def handle_browser_command(command):
    if not command:
        return None

    c = command.lower().strip()

    # --------------------------------------------------------
    # OPEN WEBSITE
    # --------------------------------------------------------

    if c.startswith("open "):
        target = c[5:].strip()

        result = open_website(target)

        if result:
            return f"Opening {target.title()}, Sir."

    # --------------------------------------------------------
    # DIRECT WEBSITE
    # --------------------------------------------------------

    if c in WEBSITES:
        result = open_website(c)

        if result:
            return f"Opening {c.title()}, Sir."

    # --------------------------------------------------------
    # GOOGLE SEARCH
    # --------------------------------------------------------

    search_match = re.match(
        r"^(?:google|search(?: for)?)\s+(.+)$",
        c
    )

    if search_match:
        query = search_match.group(1)

        result = google_search(query)

        if result:
            return f"Searching for {query}, Sir."

    return None