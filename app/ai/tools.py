import re
from urllib.parse import quote_plus

from app.integrations.browser import (
    browser_agent,
    open_website,
    google_search,
)


# ============================================================
# BASIC TOOLS
# ============================================================

def tool_get_weather(location):
    """
    Weather placeholder.
    """

    location = str(
        location or ""
    ).strip()

    if not location:
        return {
            "ok": False,
            "error": "No location provided.",
        }

    return {
        "ok": False,
        "error": (
            "Weather lookup is not currently "
            f"available for {location}."
        ),
    }


def tool_open_website(site):

    site = str(
        site or ""
    ).strip()

    if not site:
        return {
            "ok": False,
            "error": "No website specified.",
        }

    print(
        f"[TOOL] open_website({site!r})"
    )

    try:

        result = open_website(
            site
        )

        print(
            f"[TOOL] open_website {site!r} -> "
            f"{result!r}"
        )

        return result

    except Exception as e:

        print(
            "[TOOL ERROR] open_website:",
            repr(e),
        )

        return {
            "ok": False,
            "error": str(e),
        }


def tool_google_search(query):

    query = str(
        query or ""
    ).strip()

    if not query:
        return {
            "ok": False,
            "error": "No search query provided.",
        }

    print(
        f"[TOOL] google_search({query!r})"
    )

    try:

        result = google_search(
            query
        )

        print(
            f"[TOOL] google_search -> "
            f"{result!r}"
        )

        return result

    except Exception as e:

        print(
            "[TOOL ERROR] google_search:",
            repr(e),
        )

        return {
            "ok": False,
            "error": str(e),
        }


# ============================================================
# PRODUCT / YOUTUBE / MEDIA
# ============================================================

def tool_search_product_price(
    product,
):
    """
    Search the browser for the exact product phrase.

    Important:
    - Preserve the user's exact model name.
    - Never silently correct model numbers.
    """

    product = str(
        product or ""
    ).strip()

    if not product:
        return {
            "ok": False,
            "error": "No product specified.",
        }

    print(
        f"[TOOL] search_product_price("
        f"{product!r})"
    )

    try:

        exact_query = (
            f'"{product}" price'
        )

        result = google_search(
            exact_query
        )

        return result

    except Exception as e:

        print(
            "[TOOL ERROR] search_product_price:",
            repr(e),
        )

        return {
            "ok": False,
            "error": str(e),
        }


def tool_search_youtube(
    query,
):

    query = str(
        query or ""
    ).strip()

    if not query:
        return {
            "ok": False,
            "error": (
                "No YouTube search query provided."
            ),
        }

    print(
        f"[TOOL] search_youtube({query!r})"
    )

    try:

        url = (
            "https://www.youtube.com/results"
            "?search_query="
            + quote_plus(query)
        )

        result = browser_agent.open(
            url
        )

        return result

    except Exception as e:

        print(
            "[TOOL ERROR] search_youtube:",
            repr(e),
        )

        return {
            "ok": False,
            "error": str(e),
        }


def tool_play_youtube(
    query,
):

    query = str(
        query or ""
    ).strip()

    if not query:
        return {
            "ok": False,
            "error": "No video specified.",
        }

    print(
        f"[TOOL] play_youtube({query!r})"
    )

    try:

        url = (
            "https://www.youtube.com/results"
            "?search_query="
            + quote_plus(query)
        )

        result = browser_agent.open(
            url
        )

        return result

    except Exception as e:

        print(
            "[TOOL ERROR] play_youtube:",
            repr(e),
        )

        return {
            "ok": False,
            "error": str(e),
        }


def tool_media_control(
    action,
):

    action = str(
        action or ""
    ).strip().lower()

    if not action:
        return {
            "ok": False,
            "error": (
                "No media action provided."
            ),
        }

    print(
        f"[TOOL] media_control({action!r})"
    )

    return {
        "ok": True,
        "action": action,
        "message": (
            f"Media action received: {action}"
        ),
    }


# ============================================================
# BROWSER TEXT CLEANING
# ============================================================

def _clean_browser_text(
    text,
):
    """
    Remove obvious webpage noise while preserving
    useful product, specification and descriptive text.
    """

    if not text:
        return ""

    text = str(text)

    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    lines = []

    noise_exact = {
        "menu",
        "close",
        "search",
        "sign in",
        "log in",
        "login",
        "register",
        "account",
        "cart",
        "shopping bag",
        "home",
        "skip to content",
        "skip to main content",
        "cookie settings",
        "privacy",
        "terms",
    }

    for raw_line in text.splitlines():

        line = raw_line.strip()

        if not line:
            continue

        lower = line.lower()

        if lower in noise_exact:
            continue

        if re.fullmatch(
            r"(?:https?://|www\.)\S+",
            line,
            flags=re.IGNORECASE,
        ):
            continue

        if (
            "://" in line
            and len(line) > 100
        ):
            continue

        if len(line) > 500:
            line = (
                line[:500]
                .rstrip()
                + "..."
            )

        lines.append(
            line
        )

    deduped = []

    for line in lines:

        if (
            deduped
            and line == deduped[-1]
        ):
            continue

        deduped.append(
            line
        )

    return "\n".join(
        deduped
    )


# ============================================================
# BROWSER RELEVANCE SCORING
# ============================================================

def _score_browser_line(
    line,
):
    """
    Score information-rich page content.

    Higher scores mean:
    - product names
    - prices
    - specifications
    - availability
    - reviews
    - comparisons
    """

    lower = line.lower()

    score = 0

    keywords = (
        # Products
        "macbook",
        "iphone",
        "ipad",
        "galaxy",
        "thinkpad",
        "rtx",
        "geforce",
        "radeon",
        "laptop",
        "desktop",
        "monitor",
        "keyboard",
        "mouse",

        # Pricing
        "price",
        "from $",
        "from €",
        "from £",
        "$",
        "€",
        "£",
        "usd",
        "eur",
        "sale",
        "discount",
        "deal",

        # Purchase
        "buy",
        "purchase",
        "available",
        "in stock",
        "out of stock",

        # Specifications
        "spec",
        "specification",
        "memory",
        "ram",
        "storage",
        "ssd",
        "processor",
        "cpu",
        "gpu",
        "display",
        "screen",
        "battery",
        "resolution",
        "refresh rate",
        "cores",
        "chip",

        # Reviews
        "review",
        "rating",
        "pros",
        "cons",
        "performance",
        "comparison",
        "compare",
    )

    for keyword in keywords:

        if keyword in lower:
            score += 3

    if len(line) <= 120:
        score += 1

    if len(line) < 8:
        score -= 2

    return score


def _compact_browser_text(
    text,
    max_chars=2200,
):
    """
    Keep the most useful browser content while
    preserving original page order.
    """

    cleaned = _clean_browser_text(
        text
    )

    if not cleaned:
        return ""

    lines = [
        line.strip()
        for line in cleaned.splitlines()
        if line.strip()
    ]

    if not lines:
        return ""

    if len(cleaned) <= max_chars:
        return cleaned

    scored = []

    for index, line in enumerate(
        lines
    ):

        scored.append(
            (
                _score_browser_line(
                    line
                ),
                index,
                line,
            )
        )

    ranked = sorted(
        scored,
        key=lambda item: (
            -item[0],
            item[1],
        ),
    )

    selected_indexes = set()

    current_chars = 0

    # Preserve beginning of page.
    for index in range(
        min(8, len(lines))
    ):

        line = lines[index]

        if (
            current_chars
            + len(line)
            + 1
            <= max_chars
        ):

            selected_indexes.add(
                index
            )

            current_chars += (
                len(line)
                + 1
            )

    # Add useful information.
    for (
        score,
        index,
        line,
    ) in ranked:

        if index in selected_indexes:
            continue

        if score <= 0:
            continue

        required = (
            len(line)
            + 1
        )

        if (
            current_chars
            + required
            > max_chars
        ):
            continue

        selected_indexes.add(
            index
        )

        current_chars += required

        if current_chars >= max_chars:
            break

    selected = [
        lines[index]
        for index in sorted(
            selected_indexes
        )
    ]

    result = "\n".join(
        selected
    )

    if len(result) > max_chars:
        result = (
            result[:max_chars]
            .rstrip()
            + "..."
        )

    return result


# ============================================================
# BROWSER ACTION COMPACTION
# ============================================================

def _compact_browser_links(
    links,
    max_links=18,
):
    """
    Preserve useful visible actions.

    The browser engine now returns:
    - links
    - buttons
    - action labels
    - visible text

    Only labels are exposed to the AI-facing snapshot.
    Raw hrefs remain internal.
    """

    if not links:
        return []

    useful_words = (
        "buy",
        "price",
        "shop",
        "store",
        "spec",
        "specs",
        "compare",
        "review",
        "product",
        "details",
        "overview",
        "features",
        "support",
        "learn",
        "next",
        "previous",
        "continue",
        "download",
    )

    selected = []

    # First collect highly useful actions.
    for link in links:

        if not isinstance(
            link,
            dict,
        ):
            continue

        text = str(
            link.get(
                "text",
                "",
            )
        ).strip()

        if not text:
            continue

        lower = text.lower()

        if any(
            word in lower
            for word in useful_words
        ):

            selected.append(
                link
            )

    # Fill remaining slots.
    if len(selected) < max_links:

        for link in links:

            if not isinstance(
                link,
                dict,
            ):
                continue

            text = str(
                link.get(
                    "text",
                    "",
                )
            ).strip()

            if not text:
                continue

            existing_indexes = {
                item.get(
                    "index"
                )
                for item in selected
            }

            if (
                link.get("index")
                in existing_indexes
            ):
                continue

            selected.append(
                link
            )

            if len(selected) >= max_links:
                break

    return selected[:max_links]


# ============================================================
# BROWSER OBSERVATION FORMAT
# ============================================================

def _format_browser_observation(
    result,
):
    """
    Convert the browser engine's structured observation
    into a compact AI-facing snapshot.

    Full URLs are deliberately excluded.
    """

    if not isinstance(
        result,
        dict,
    ):
        return str(result)

    if not result.get(
        "ok",
        True,
    ):

        return str(
            result.get(
                "error",
                "Browser observation failed.",
            )
        )

    title = str(
        result.get(
            "title",
            "",
        )
    ).strip()

    domain = str(
        result.get(
            "domain",
            "",
        )
    ).strip()

    description = str(
        result.get(
            "description",
            "",
        )
    ).strip()

    headings = result.get(
        "headings",
        [],
    )

    text = str(
        result.get(
            "text",
            "",
        )
    )

    links = result.get(
        "links",
        [],
    )

    compact_text = _compact_browser_text(
        text,
        max_chars=2200,
    )

    compact_links = _compact_browser_links(
        links,
        max_links=18,
    )

    parts = []

    if title:
        parts.append(
            f"Page: {title}"
        )

    if domain:
        readable_domain = domain

        if readable_domain.lower().startswith(
            "www."
        ):
            readable_domain = (
                readable_domain[4:]
            )

        readable_domain = (
            readable_domain
            .split(":")[0]
        )

        parts.append(
            f"Website: {readable_domain}"
        )

    if description:
        parts.append(
            "\nPage description:\n"
            + description[:500]
        )

    if headings:
        heading_lines = []

        for heading in headings[:12]:

            heading = str(
                heading
            ).strip()

            if heading:
                heading_lines.append(
                    f"- {heading}"
                )

        if heading_lines:
            parts.append(
                "\nHeadings:\n"
                + "\n".join(
                    heading_lines
                )
            )

    if compact_text:
        parts.append(
            "\nPage content:\n"
            + compact_text
        )

    if compact_links:

        action_lines = []

        for link in compact_links:

            index = link.get(
                "index"
            )

            text_value = str(
                link.get(
                    "text",
                    "",
                )
            ).strip()

            kind = str(
                link.get(
                    "kind",
                    "link",
                )
            ).strip()

            aria = str(
                link.get(
                    "aria_label",
                    "",
                )
            ).strip()

            if not text_value and aria:
                text_value = aria

            if not text_value:
                continue

            if index is None:
                action_lines.append(
                    f"- {kind}: {text_value}"
                )
            else:
                action_lines.append(
                    f"- [{index}] "
                    f"{kind}: {text_value}"
                )

        if action_lines:
            parts.append(
                "\nVisible clickable elements:\n"
                + "\n".join(
                    action_lines
                )
            )

    return "\n".join(
        parts
    )


# ============================================================
# BROWSER TOOLS
# ============================================================

def tool_browser_open(
    url,
):

    url = str(
        url or ""
    ).strip()

    if not url:
        return {
            "ok": False,
            "error": "No URL provided.",
        }

    print(
        f"[TOOL] browser_open({url!r})"
    )

    try:

        result = browser_agent.open(
            url
        )

        return _format_browser_observation(
            result
        )

    except Exception as e:

        print(
            "[TOOL ERROR] browser_open:",
            repr(e),
        )

        return {
            "ok": False,
            "error": str(e),
        }


def tool_browser_observe():

    print(
        "[TOOL] browser_observe()"
    )

    try:

        result = browser_agent.observe()

        formatted = (
            _format_browser_observation(
                result
            )
        )

        return formatted

    except Exception as e:

        print(
            "[TOOL ERROR] browser_observe:",
            repr(e),
        )

        return {
            "ok": False,
            "error": str(e),
        }


def tool_browser_click(
    index=None,
    target=None,
):
    """
    Smart browser click.

    Modes:

        browser_click(index=5)

        browser_click(target="Buy")

        browser_click(
            target="Tech Specs"
        )

    Index remains fully supported.
    Target performs semantic matching against
    currently visible links/buttons.
    """

    if (
        index is None
        and not str(
            target or ""
        ).strip()
    ):
        return {
            "ok": False,
            "error": (
                "Provide either a browser "
                "link index or a visible target."
            ),
        }

    if index is not None:

        try:
            index = int(index)
        except (
            TypeError,
            ValueError,
        ):
            return {
                "ok": False,
                "error": (
                    "Browser link index "
                    "must be an integer."
                ),
            }

        print(
            f"[TOOL] browser_click(index={index})"
        )

        try:

            result = browser_agent.click(
                index=index
            )

            return (
                _format_browser_observation(
                    result
                )
            )

        except Exception as e:

            print(
                "[TOOL ERROR] browser_click:",
                repr(e),
            )

            return {
                "ok": False,
                "error": str(e),
            }

    target = str(
        target or ""
    ).strip()

    print(
        f"[TOOL] browser_click("
        f"target={target!r})"
    )

    try:

        result = browser_agent.click(
            target=target
        )

        return (
            _format_browser_observation(
                result
            )
        )

    except Exception as e:

        print(
            "[TOOL ERROR] browser_click:",
            repr(e),
        )

        return {
            "ok": False,
            "error": str(e),
        }


def tool_browser_back():

    print(
        "[TOOL] browser_back()"
    )

    try:

        result = browser_agent.back()

        return (
            _format_browser_observation(
                result
            )
        )

    except Exception as e:

        print(
            "[TOOL ERROR] browser_back:",
            repr(e),
        )

        return {
            "ok": False,
            "error": str(e),
        }


def tool_browser_forward():

    print(
        "[TOOL] browser_forward()"
    )

    try:

        result = browser_agent.forward()

        return (
            _format_browser_observation(
                result
            )
        )

    except Exception as e:

        print(
            "[TOOL ERROR] browser_forward:",
            repr(e),
        )

        return {
            "ok": False,
            "error": str(e),
        }


def tool_browser_close():

    print(
        "[TOOL] browser_close()"
    )

    try:

        result = browser_agent.close()

        return result

    except Exception as e:

        print(
            "[TOOL ERROR] browser_close:",
            repr(e),
        )

        return {
            "ok": False,
            "error": str(e),
        }


# ============================================================
# TOOL DEFINITIONS FOR OPENAI
# ============================================================

TOOLS = [

    {
        "type": "function",
        "name": "get_weather",
        "description": (
            "Get the weather for a location."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": (
                        "City or location."
                    ),
                },
            },
            "required": [
                "location",
            ],
        },
    },

    {
        "type": "function",
        "name": "open_website",
        "description": (
            "Open a known website in the "
            "controlled browser."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "site": {
                    "type": "string",
                    "description": (
                        "Website name or URL."
                    ),
                },
            },
            "required": [
                "site",
            ],
        },
    },

    {
        "type": "function",
        "name": "google_search",
        "description": (
            "Search Google for information."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Exact search query."
                    ),
                },
            },
            "required": [
                "query",
            ],
        },
    },

    {
        "type": "function",
        "name": "search_product_price",
        "description": (
            "Search for the price of an exact "
            "product. Preserve the user's exact "
            "product name and model."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "product": {
                    "type": "string",
                    "description": (
                        "Exact product name/model "
                        "from the user."
                    ),
                },
            },
            "required": [
                "product",
            ],
        },
    },

    {
        "type": "function",
        "name": "search_youtube",
        "description": (
            "Search YouTube for a video."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "YouTube search query."
                    ),
                },
            },
            "required": [
                "query",
            ],
        },
    },

    {
        "type": "function",
        "name": "play_youtube",
        "description": (
            "Open YouTube for a requested video."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Video to find and play."
                    ),
                },
            },
            "required": [
                "query",
            ],
        },
    },

    {
        "type": "function",
        "name": "media_control",
        "description": (
            "Control media playback."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": (
                        "Media action such as play, pause, "
                        "stop, next, previous, mute or volume."
                    ),
                },
            },
            "required": [
                "action",
            ],
        },
    },

    {
        "type": "function",
        "name": "browser_open",
        "description": (
            "Open an arbitrary URL in the "
            "controlled browser."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": (
                        "Complete URL to open."
                    ),
                },
            },
            "required": [
                "url",
            ],
        },
    },

    {
        "type": "function",
        "name": "browser_observe",
        "description": (
            "Inspect the currently open webpage. "
            "Returns the page title, website, headings, "
            "important content, prices/specifications, "
            "and visible clickable elements with indexes. "
            "Use this when the user asks about the current "
            "page or wants analysis of something visible."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },

    {
        "type": "function",
        "name": "browser_click",
        "description": (
            "Click a visible element in the controlled browser. "
            "Prefer the numeric index from the latest "
            "browser_observe result when available. "
            "You may also provide target text such as "
            "'Buy', 'Tech Specs', 'Compare', or 'Learn more' "
            "for semantic clicking. "
            "Only target currently visible clickable elements."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "index": {
                    "type": "integer",
                    "description": (
                        "Visible clickable-element index "
                        "from the latest browser observation."
                    ),
                },
                "target": {
                    "type": "string",
                    "description": (
                        "Visible text, aria-label or button/link "
                        "target to click semantically."
                    ),
                },
            },
            "additionalProperties": False,
        },
    },

    {
        "type": "function",
        "name": "browser_back",
        "description": (
            "Navigate back one page in the "
            "controlled browser."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },

    {
        "type": "function",
        "name": "browser_forward",
        "description": (
            "Navigate forward one page in the "
            "controlled browser."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },

    {
        "type": "function",
        "name": "browser_close",
        "description": (
            "Close the controlled browser session."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


# ============================================================
# TOOL FUNCTION REGISTRY
# ============================================================

TOOL_FUNCTIONS = {
    "get_weather": tool_get_weather,
    "open_website": tool_open_website,
    "google_search": tool_google_search,
    "search_product_price": tool_search_product_price,
    "search_youtube": tool_search_youtube,
    "play_youtube": tool_play_youtube,
    "media_control": tool_media_control,
    "browser_open": tool_browser_open,
    "browser_observe": tool_browser_observe,
    "browser_click": tool_browser_click,
    "browser_back": tool_browser_back,
    "browser_forward": tool_browser_forward,
    "browser_close": tool_browser_close,
}