import re

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
    Keep this function available for the existing tool registry.
    """
    location = str(location or "").strip()

    if not location:
        return {
            "ok": False,
            "error": "No location provided."
        }

    return {
        "ok": False,
        "error": f"Weather lookup is not currently available for {location}."
    }


def tool_open_website(site):
    site = str(site or "").strip()

    if not site:
        return {
            "ok": False,
            "error": "No website specified."
        }

    print(f"[TOOL] open_website({site!r})")

    try:
        result = open_website(site)

        print(
            f"[TOOL] open_website {site!r} -> "
            f"{result!r}"
        )

        return result

    except Exception as e:
        print(
            "[TOOL ERROR] open_website:",
            repr(e)
        )

        return {
            "ok": False,
            "error": str(e)
        }


def tool_google_search(query):
    query = str(query or "").strip()

    if not query:
        return {
            "ok": False,
            "error": "No search query provided."
        }

    print(f"[TOOL] google_search({query!r})")

    try:
        result = google_search(query)

        print(
            f"[TOOL] google_search -> "
            f"{result!r}"
        )

        return result

    except Exception as e:
        print(
            "[TOOL ERROR] google_search:",
            repr(e)
        )

        return {
            "ok": False,
            "error": str(e)
        }


# ============================================================
# PRODUCT / YOUTUBE / MEDIA
# ============================================================

def tool_search_product_price(product):
    """
    Search the browser for the exact product phrase.

    Important:
    - Preserve the user's exact model name.
    - Never silently correct model numbers.
    """

    product = str(product or "").strip()

    if not product:
        return {
            "ok": False,
            "error": "No product specified."
        }

    print(
        f"[TOOL] search_product_price("
        f"{product!r})"
    )

    try:
        exact_query = f'"{product}" price'

        result = google_search(exact_query)

        return result

    except Exception as e:
        print(
            "[TOOL ERROR] search_product_price:",
            repr(e)
        )

        return {
            "ok": False,
            "error": str(e)
        }


def tool_search_youtube(query):
    query = str(query or "").strip()

    if not query:
        return {
            "ok": False,
            "error": "No YouTube search query provided."
        }

    print(f"[TOOL] search_youtube({query!r})")

    try:
        result = browser_agent.open(
            "https://www.youtube.com/results?search_query="
            + query.replace(" ", "+")
        )

        return result

    except Exception as e:
        print(
            "[TOOL ERROR] search_youtube:",
            repr(e)
        )

        return {
            "ok": False,
            "error": str(e)
        }


def tool_play_youtube(query):
    query = str(query or "").strip()

    if not query:
        return {
            "ok": False,
            "error": "No video specified."
        }

    print(f"[TOOL] play_youtube({query!r})")

    try:
        result = browser_agent.open(
            "https://www.youtube.com/results?search_query="
            + query.replace(" ", "+")
        )

        return result

    except Exception as e:
        print(
            "[TOOL ERROR] play_youtube:",
            repr(e)
        )

        return {
            "ok": False,
            "error": str(e)
        }


def tool_media_control(action):
    action = str(action or "").strip().lower()

    if not action:
        return {
            "ok": False,
            "error": "No media action provided."
        }

    print(f"[TOOL] media_control({action!r})")

    # Keep the existing media command contract simple.
    return {
        "ok": True,
        "action": action,
        "message": f"Media action received: {action}"
    }


# ============================================================
# BROWSER OBSERVATION
# ============================================================

def _clean_browser_text(text):
    """
    Clean browser text before sending it to the AI.

    Removes common browser/page noise while preserving useful
    product, pricing, specification and descriptive content.
    """

    if not text:
        return ""

    text = str(text)

    # Normalize whitespace.
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    lines = []

    # Common navigation / UI noise.
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
        "learn more",
        "read more",
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

        # Ignore obvious URL-only lines.
        if re.fullmatch(
            r"(?:https?://|www\.)\S+",
            line,
            flags=re.IGNORECASE,
        ):
            continue

        # Ignore extremely long technical URL-like strings.
        if (
            "://" in line
            and len(line) > 80
        ):
            continue

        # Ignore giant repeated navigation strings.
        if len(line) > 500:
            line = line[:500].rstrip() + "..."

        lines.append(line)

    # Remove immediate duplicates.
    deduped = []

    for line in lines:
        if deduped and line == deduped[-1]:
            continue

        deduped.append(line)

    return "\n".join(deduped)


def _score_browser_line(line):
    """
    Give useful page content a higher priority.

    This lets us keep product/pricing/specification information
    while dropping generic page boilerplate.
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

        # Reviews / evaluation
        "review",
        "rating",
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

    # Headings and short descriptive sentences are useful.
    if len(line) <= 120:
        score += 1

    # Very short fragments are usually navigation.
    if len(line) < 8:
        score -= 2

    return score


def _compact_browser_text(text, max_chars=2200):
    """
    Keep the most useful page information without dumping the
    entire webpage into the model.
    """

    cleaned = _clean_browser_text(text)

    if not cleaned:
        return ""

    lines = [
        line.strip()
        for line in cleaned.splitlines()
        if line.strip()
    ]

    if not lines:
        return ""

    # Preserve original order while calculating relevance.
    scored = []

    for index, line in enumerate(lines):
        scored.append(
            (
                _score_browser_line(line),
                index,
                line,
            )
        )

    # Highest-value lines first.
    ranked = sorted(
        scored,
        key=lambda item: (
            -item[0],
            item[1],
        )
    )

    selected_indexes = set()
    current_chars = 0

    # Always preserve the beginning of the page because it
    # often contains the main title/product description.
    for index in range(
        min(8, len(lines))
    ):
        line = lines[index]

        if (
            current_chars + len(line) + 1
            <= max_chars
        ):
            selected_indexes.add(index)
            current_chars += len(line) + 1

    # Add relevant lines until the compact budget is reached.
    for score, index, line in ranked:
        if index in selected_indexes:
            continue

        if score <= 0:
            continue

        if (
            current_chars + len(line) + 1
            > max_chars
        ):
            continue

        selected_indexes.add(index)
        current_chars += len(line) + 1

        if current_chars >= max_chars:
            break

    # Restore webpage order.
    selected = [
        lines[index]
        for index in sorted(selected_indexes)
    ]

    result = "\n".join(selected)

    if len(result) > max_chars:
        result = result[:max_chars].rstrip() + "..."

    return result


def _compact_browser_links(links, max_links=12):
    """
    Keep useful navigation links but never expose raw URLs to the AI
    unless the tool specifically needs them internally.
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
    )

    selected = []

    # First collect useful links.
    for link in links:
        if not isinstance(link, dict):
            continue

        text = str(
            link.get("text", "")
        ).strip()

        href = str(
            link.get("href", "")
        ).strip()

        if not text:
            continue

        lower = text.lower()

        if any(
            word in lower
            for word in useful_words
        ):
            selected.append(
                {
                    "text": text,
                    "href": href,
                }
            )

    # Then fill remaining slots.
    if len(selected) < max_links:
        for link in links:
            if not isinstance(link, dict):
                continue

            text = str(
                link.get("text", "")
            ).strip()

            href = str(
                link.get("href", "")
            ).strip()

            if not text:
                continue

            if any(
                item.get("text") == text
                for item in selected
            ):
                continue

            selected.append(
                {
                    "text": text,
                    "href": href,
                }
            )

            if len(selected) >= max_links:
                break

    return selected[:max_links]


def _format_browser_observation(result):
    """
    Convert the raw browser observation into a compact,
    conversational AI-facing representation.

    IMPORTANT:
    The complete URL remains available internally through the
    browser tool, but is deliberately NOT included in the
    conversational snapshot.
    """

    if not isinstance(result, dict):
        return str(result)

    if not result.get("ok", True):
        return str(
            result.get(
                "error",
                "Browser observation failed."
            )
        )

    title = str(
        result.get("title", "")
    ).strip()

    url = str(
        result.get("url", "")
    ).strip()

    domain = str(
        result.get("domain", "")
    ).strip()

    text = str(
        result.get("text", "")
    )

    links = result.get(
        "links",
        []
    )

    # --------------------------------------------------------
    # Human-readable site name.
    # --------------------------------------------------------

    readable_domain = domain

    if readable_domain.lower().startswith("www."):
        readable_domain = readable_domain[4:]

    # Remove unnecessary port.
    readable_domain = readable_domain.split(":")[0]

    # --------------------------------------------------------
    # Compact page content.
    # --------------------------------------------------------

    compact_text = _compact_browser_text(
        text,
        max_chars=2200,
    )

    compact_links = _compact_browser_links(
        links,
        max_links=12,
    )

    parts = []

    if title:
        parts.append(
            f"Page: {title}"
        )

    if readable_domain:
        parts.append(
            f"Website: {readable_domain}"
        )

    if compact_text:
        parts.append(
            "\nPage content:\n"
            + compact_text
        )

    if compact_links:
        link_lines = []

        for link in compact_links:
            text_value = link.get(
                "text",
                ""
            ).strip()

            if text_value:
                link_lines.append(
                    f"- {text_value}"
                )

        if link_lines:
            parts.append(
                "\nUseful page links:\n"
                + "\n".join(link_lines)
            )

    # Keep the exact URL available only inside this function's
    # internal data path. Do NOT append it to the AI text.
    #
    # `url` intentionally unused here.
    _ = url

    return "\n".join(parts)


# ============================================================
# BROWSER TOOLS
# ============================================================

def tool_browser_open(url):
    url = str(url or "").strip()

    if not url:
        return {
            "ok": False,
            "error": "No URL provided."
        }

    print(f"[TOOL] browser_open({url!r})")

    try:
        result = browser_agent.open(url)

        return _format_browser_observation(
            result
        )

    except Exception as e:
        print(
            "[TOOL ERROR] browser_open:",
            repr(e)
        )

        return {
            "ok": False,
            "error": str(e)
        }


def tool_browser_observe():
    print("[TOOL] browser_observe()")

    try:
        result = browser_agent.observe()

        formatted = _format_browser_observation(
            result
        )

        return formatted

    except Exception as e:
        print(
            "[TOOL ERROR] browser_observe:",
            repr(e)
        )

        return {
            "ok": False,
            "error": str(e)
        }


def tool_browser_click(index):
    try:
        index = int(index)
    except (
        TypeError,
        ValueError,
    ):
        return {
            "ok": False,
            "error": "Browser link index must be an integer."
        }

    print(
        f"[TOOL] browser_click("
        f"{index})"
    )

    try:
        result = browser_agent.click(index)

        return _format_browser_observation(
            result
        )

    except Exception as e:
        print(
            "[TOOL ERROR] browser_click:",
            repr(e)
        )

        return {
            "ok": False,
            "error": str(e)
        }


def tool_browser_back():
    print("[TOOL] browser_back()")

    try:
        result = browser_agent.back()

        return _format_browser_observation(
            result
        )

    except Exception as e:
        print(
            "[TOOL ERROR] browser_back:",
            repr(e)
        )

        return {
            "ok": False,
            "error": str(e)
        }


def tool_browser_forward():
    print("[TOOL] browser_forward()")

    try:
        result = browser_agent.forward()

        return _format_browser_observation(
            result
        )

    except Exception as e:
        print(
            "[TOOL ERROR] browser_forward:",
            repr(e)
        )

        return {
            "ok": False,
            "error": str(e)
        }


def tool_browser_close():
    print("[TOOL] browser_close()")

    try:
        result = browser_agent.close()

        return result

    except Exception as e:
        print(
            "[TOOL ERROR] browser_close:",
            repr(e)
        )

        return {
            "ok": False,
            "error": str(e)
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
                "location"
            ],
        },
    },

    {
        "type": "function",
        "name": "open_website",
        "description": (
            "Open a known website in the controlled browser."
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
                "site"
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
                "query"
            ],
        },
    },

    {
        "type": "function",
        "name": "search_product_price",
        "description": (
            "Search for the price of an exact product. "
            "Preserve the user's exact product name and model."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "product": {
                    "type": "string",
                    "description": (
                        "Exact product name/model from the user."
                    ),
                },
            },
            "required": [
                "product"
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
                "query"
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
                "query"
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
                "action"
            ],
        },
    },

    {
        "type": "function",
        "name": "browser_open",
        "description": (
            "Open an arbitrary URL in the controlled browser."
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
                "url"
            ],
        },
    },

    {
        "type": "function",
        "name": "browser_observe",
        "description": (
            "Inspect the currently open webpage. "
            "Use this when the user asks what is on the current page, "
            "asks whether they should buy something shown on the page, "
            "or asks about visible page content."
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
            "Click a visible browser link using its index from "
            "the latest browser observation."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "index": {
                    "type": "integer",
                    "description": (
                        "Visible link index from browser observation."
                    ),
                },
            },
            "required": [
                "index"
            ],
        },
    },

    {
        "type": "function",
        "name": "browser_back",
        "description": (
            "Navigate back one page in the controlled browser."
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
            "Navigate forward one page in the controlled browser."
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