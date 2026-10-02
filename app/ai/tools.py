
import urllib.parse
import webbrowser

from weather import get_weather

from app.integrations.browser import (
    browser_agent,
    open_website,
    google_search,
)

from app.commands.media import (
    _handle_volume,
    _handle_mute,
    _handle_media,
)

from app.commands.browser import (
    _youtube_first_result,
)


# ============================================================
# WEATHER
# ============================================================

def tool_get_weather(city):
    if not city:
        return "I need a city to check the weather, Sir."

    city = str(city).strip()

    if not city:
        return "I need a city to check the weather, Sir."

    print(f"[TOOL] get_weather({city!r})")

    try:
        result = get_weather(city)

        if result:
            return str(result)

        return f"I could not retrieve the weather for {city}, Sir."

    except Exception as e:
        print("[TOOL WEATHER ERROR]", repr(e))
        return f"I could not retrieve the weather for {city}, Sir."


# ============================================================
# NORMAL BROWSER
# ============================================================

def tool_open_website(site):
    if not site:
        return "I need to know which website to open, Sir."

    site = str(site).strip().lower()

    if not site:
        return "I need to know which website to open, Sir."

    print(f"[TOOL] open_website({site!r})")

    try:
        result = open_website(site)

        if result:
            return result

        return f"I could not open {site}, Sir."

    except Exception as e:
        print("[TOOL WEBSITE ERROR]", repr(e))
        return f"I could not open {site}, Sir."


def tool_google_search(query):
    if not query:
        return "I need a search query, Sir."

    query = str(query).strip()

    if not query:
        return "I need a search query, Sir."

    print(f"[TOOL] google_search({query!r})")

    try:
        result = google_search(query)

        if result:
            return result

        return (
            f"I could not start the Google search "
            f"for {query}, Sir."
        )

    except Exception as e:
        print("[TOOL GOOGLE ERROR]", repr(e))

        return (
            f"I could not start the Google search "
            f"for {query}, Sir."
        )


# ============================================================
# PRODUCT PRICE SEARCH
# ============================================================

def tool_search_product_price(product, location=None):
    """
    Search Google specifically for a product price.

    Product names are preserved exactly.

    Examples:
        RTX 5090
        RTX 5080 Ti
        iPhone 17 Pro
        Ryzen 9950X
    """

    if not product:
        return (
            "I need to know which product "
            "you want the price for, Sir."
        )

    product = str(product).strip()

    if not product:
        return (
            "I need to know which product "
            "you want the price for, Sir."
        )

    location = (
        str(location).strip()
        if location
        else ""
    )

    print(
        "[TOOL] search_product_price("
        f"product={product!r}, "
        f"location={location!r})"
    )

    query_parts = [
        f'"{product}"',
        "price",
    ]

    if location:
        query_parts.append(location)

    query = " ".join(query_parts)

    print(
        f"[TOOL] Product price query: {query!r}"
    )

    try:
        encoded = urllib.parse.quote_plus(query)

        url = (
            "https://www.google.com/search"
            f"?q={encoded}"
        )

        opened = webbrowser.open(
            url,
            new=2,
        )

        if opened:
            if location:
                return (
                    f"I searched for current prices "
                    f"of {product} in {location}, Sir."
                )

            return (
                f"I searched for current prices "
                f"of {product}, Sir."
            )

        return (
            f"I prepared the price search for "
            f"{product}, but I could not open it, Sir."
        )

    except Exception as e:
        print(
            "[TOOL PRODUCT PRICE ERROR]",
            repr(e),
        )

        return (
            f"I could not search for the current "
            f"price of {product}, Sir."
        )


# ============================================================
# YOUTUBE
# ============================================================

def tool_search_youtube(query):
    if not query:
        return "I need a YouTube search query, Sir."

    query = str(query).strip()

    if not query:
        return "I need a YouTube search query, Sir."

    print(
        f"[TOOL] search_youtube({query!r})"
    )

    try:
        encoded = urllib.parse.quote_plus(query)

        url = (
            "https://www.youtube.com/results"
            f"?search_query={encoded}"
        )

        opened = webbrowser.open(
            url,
            new=2,
        )

        if opened:
            return (
                f"Searching YouTube for "
                f"{query}, Sir."
            )

        return (
            f"I found the YouTube search for "
            f"{query}, but I could not open it, Sir."
        )

    except Exception as e:
        print(
            "[TOOL YOUTUBE SEARCH ERROR]",
            repr(e),
        )

        return (
            f"I could not search YouTube "
            f"for {query}, Sir."
        )


def tool_play_youtube(query):
    if not query:
        return (
            "I need to know what you want "
            "to play, Sir."
        )

    query = str(query).strip()

    if not query:
        return (
            "I need to know what you want "
            "to play, Sir."
        )

    print(
        f"[TOOL] play_youtube({query!r})"
    )

    try:
        video_url = _youtube_first_result(query)

        if not video_url:
            return (
                f"I could not find a YouTube "
                f"result for {query}, Sir."
            )

        print(
            f"[TOOL] YouTube result: {video_url}"
        )

        opened = webbrowser.open(
            video_url,
            new=2,
        )

        if opened:
            return (
                f"Playing the first YouTube "
                f"result for {query}, Sir."
            )

        return (
            f"I found the YouTube result for "
            f"{query}, but I could not open it, Sir."
        )

    except Exception as e:
        print(
            "[TOOL YOUTUBE PLAY ERROR]",
            repr(e),
        )

        return (
            f"I could not play {query} "
            f"on YouTube, Sir."
        )


# ============================================================
# MEDIA
# ============================================================

def tool_media_control(action):
    if not action:
        return (
            "I need to know which media "
            "action you want, Sir."
        )

    action = str(action).strip().lower()

    print(
        f"[TOOL] media_control({action!r})"
    )

    command_map = {
        "play": "play",
        "pause": "pause",
        "next": "next track",
        "previous": "previous track",
        "stop": "stop",
        "mute": "mute",
        "unmute": "unmute",
        "volume_up": "turn up the volume",
        "volume_down": "turn down the volume",
        "volume_max": "volume maximum",
        "volume_min": "volume minimum",
    }

    command = command_map.get(action)

    if not command:
        return (
            f"I do not recognise the media "
            f"action {action}, Sir."
        )

    try:
        result = _handle_volume(command)

        if result is not None:
            return result

        result = _handle_mute(command)

        if result is not None:
            return result

        result = _handle_media(command)

        if result is not None:
            return result

        return (
            f"I could not perform the media "
            f"action {action}, Sir."
        )

    except Exception as e:
        print(
            "[TOOL MEDIA ERROR]",
            repr(e),
        )

        return (
            f"I could not perform the media "
            f"action {action}, Sir."
        )


# ============================================================
# CONTROLLED BROWSER
# ============================================================

def tool_browser_open(url):
    if not url:
        return "I need a URL to open, Sir."

    url = str(url).strip()

    if not url:
        return "I need a URL to open, Sir."

    print(
        f"[TOOL] browser_open({url!r})"
    )

    try:
        result = browser_agent.open(url)

        if not result.get("ok"):
            error = result.get(
                "error",
                "Unknown browser error.",
            )

            return (
                "I could not open that page, Sir. "
                f"{error}"
            )

        title = result.get(
            "title",
            "",
        )

        current_url = result.get(
            "url",
            "",
        )

        return (
            "Browser opened successfully.\n"
            f"Page title: {title}\n"
            f"Current URL: {current_url}\n\n"
            "Initial browser observation:\n"
            f"{_format_browser_observation(result)}"
        )

    except Exception as e:
        print(
            "[TOOL BROWSER OPEN ERROR]",
            repr(e),
        )

        return (
            "I could not open that page, Sir."
        )


def tool_browser_observe():
    print(
        "[TOOL] browser_observe()"
    )

    try:
        result = browser_agent.observe()

        if not result.get("ok"):
            error = result.get(
                "error",
                "Unknown browser error.",
            )

            return (
                "I could not inspect the "
                "browser, Sir. "
                f"{error}"
            )

        return (
            "Browser observation:\n"
            f"{_format_browser_observation(result)}"
        )

    except Exception as e:
        print(
            "[TOOL BROWSER OBSERVE ERROR]",
            repr(e),
        )

        return (
            "I could not inspect the browser, Sir."
        )


def tool_browser_click(index):
    print(
        f"[TOOL] browser_click({index!r})"
    )

    try:
        result = browser_agent.click(index)

        if not result.get("ok"):
            error = result.get(
                "error",
                "Unknown browser error.",
            )

            return (
                "I could not click that browser "
                "link, Sir. "
                f"{error}"
            )

        clicked_text = result.get(
            "clicked_text",
            "",
        )

        clicked_href = result.get(
            "clicked_href",
            "",
        )

        url = result.get(
            "url",
            "",
        )

        title = result.get(
            "title",
            "",
        )

        return (
            "Browser navigation succeeded.\n"
            f"Clicked link: {clicked_text}\n"
            f"Link target: {clicked_href}\n"
            f"Page title: {title}\n"
            f"Current URL: {url}\n\n"
            "Verified page observation:\n"
            f"{_format_browser_observation(result)}"
        )

    except Exception as e:
        print(
            "[TOOL BROWSER CLICK ERROR]",
            repr(e),
        )

        return (
            "I could not click that "
            "browser link, Sir."
        )


def tool_browser_back():
    print(
        "[TOOL] browser_back()"
    )

    try:
        result = browser_agent.back()

        if not result.get("ok"):
            error = result.get(
                "error",
                "Unknown browser error.",
            )

            return (
                "I could not go back in the "
                "browser, Sir. "
                f"{error}"
            )

        return (
            "Browser went back successfully.\n"
            f"Page title: {result.get('title', '')}\n"
            f"Current URL: {result.get('url', '')}\n\n"
            "Verified page observation:\n"
            f"{_format_browser_observation(result)}"
        )

    except Exception as e:
        print(
            "[TOOL BROWSER BACK ERROR]",
            repr(e),
        )

        return (
            "I could not go back in "
            "the browser, Sir."
        )


def tool_browser_close():
    print(
        "[TOOL] browser_close()"
    )

    try:
        browser_agent.close()

        return (
            "The controlled browser session "
            "has been closed, Sir."
        )

    except Exception as e:
        print(
            "[TOOL BROWSER CLOSE ERROR]",
            repr(e),
        )

        return (
            "I could not close the controlled "
            "browser session, Sir."
        )


def _format_browser_observation(result):
    text = result.get(
        "text",
        "",
    )

    links = result.get(
        "links",
        [],
    )

    output = [
        f"Title: {result.get('title', '')}",
        f"URL: {result.get('url', '')}",
        f"Domain: {result.get('domain', '')}",
        "",
        "Visible page text:",
        text[:8000],
    ]

    if links:
        output.append("")
        output.append(
            "Visible links:"
        )

        for link in links[:20]:
            index = link.get(
                "index",
                "",
            )

            label = link.get(
                "text",
                "",
            )

            href = link.get(
                "href",
                "",
            )

            output.append(
                f"[{index}] {label} -> {href}"
            )

    return "\n".join(output)


# ============================================================
# OPENAI TOOL DEFINITIONS
# ============================================================

TOOLS = [

    # --------------------------------------------------------
    # WEATHER
    # --------------------------------------------------------

    {
        "type": "function",
        "name": "get_weather",
        "description": (
            "Get the current weather for a city."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": (
                        "The city to check."
                    ),
                },
            },
            "required": [
                "city",
            ],
            "additionalProperties": False,
        },
        "strict": True,
    },

    # --------------------------------------------------------
    # NORMAL WEBSITE
    # --------------------------------------------------------

    {
        "type": "function",
        "name": "open_website",
        "description": (
            "Open a known website in the "
            "user's normal browser."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "site": {
                    "type": "string",
                    "description": (
                        "Website name such as youtube, "
                        "google, github, reddit, etc."
                    ),
                },
            },
            "required": [
                "site",
            ],
            "additionalProperties": False,
        },
        "strict": True,
    },

    # --------------------------------------------------------
    # GOOGLE SEARCH
    # --------------------------------------------------------

    {
        "type": "function",
        "name": "google_search",
        "description": (
            "Search Google for general information. "
            "Use this for ordinary web searches, not "
            "dedicated product price requests."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "The exact search query. "
                        "Preserve product names and "
                        "model numbers exactly as written."
                    ),
                },
            },
            "required": [
                "query",
            ],
            "additionalProperties": False,
        },
        "strict": True,
    },

    # --------------------------------------------------------
    # PRODUCT PRICE
    # --------------------------------------------------------

    {
        "type": "function",
        "name": "search_product_price",
        "description": (
            "Search Google specifically for the current "
            "price of a physical product. Use this when "
            "the user asks for product price, cost, pricing, "
            "or where to buy a product. Preserve the complete "
            "product/model name exactly. Never split or "
            "rewrite model numbers."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "product": {
                    "type": "string",
                    "description": (
                        "The complete product name exactly "
                        "as the user referred to it. "
                        "Examples: RTX 5090, "
                        "iPhone 17 Pro, Ryzen 9950X."
                    ),
                },
                "location": {
                    "type": "string",
                    "description": (
                        "Optional country, city, or region "
                        "for the price search. Use an empty "
                        "string when no location was requested."
                    ),
                },
            },
            "required": [
                "product",
                "location",
            ],
            "additionalProperties": False,
        },
        "strict": True,
    },

    # --------------------------------------------------------
    # YOUTUBE SEARCH
    # --------------------------------------------------------

    {
        "type": "function",
        "name": "search_youtube",
        "description": (
            "Search YouTube and open the search-results "
            "page. This does NOT play a video."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "What to search for on YouTube."
                    ),
                },
            },
            "required": [
                "query",
            ],
            "additionalProperties": False,
        },
        "strict": True,
    },

    # --------------------------------------------------------
    # YOUTUBE PLAY
    # --------------------------------------------------------

    {
        "type": "function",
        "name": "play_youtube",
        "description": (
            "Find the first YouTube result and open "
            "that video. Use ONLY when the user asks "
            "to play, watch, or listen to something."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "What to play on YouTube."
                    ),
                },
            },
            "required": [
                "query",
            ],
            "additionalProperties": False,
        },
        "strict": True,
    },

    # --------------------------------------------------------
    # MEDIA
    # --------------------------------------------------------

    {
        "type": "function",
        "name": "media_control",
        "description": (
            "Control Windows media playback, "
            "mute, and volume."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "play",
                        "pause",
                        "next",
                        "previous",
                        "stop",
                        "mute",
                        "unmute",
                        "volume_up",
                        "volume_down",
                        "volume_max",
                        "volume_min",
                    ],
                },
            },
            "required": [
                "action",
            ],
            "additionalProperties": False,
        },
        "strict": True,
    },

    # --------------------------------------------------------
    # CONTROLLED BROWSER OPEN
    # --------------------------------------------------------

    {
        "type": "function",
        "name": "browser_open",
        "description": (
            "Open a URL in JARVIS's controlled browser "
            "and inspect the resulting page."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": (
                        "The full URL to open."
                    ),
                },
            },
            "required": [
                "url",
            ],
            "additionalProperties": False,
        },
        "strict": True,
    },

    # --------------------------------------------------------
    # CONTROLLED BROWSER OBSERVE
    # --------------------------------------------------------

    {
        "type": "function",
        "name": "browser_observe",
        "description": (
            "Inspect the currently open controlled "
            "browser page. Returns page title, URL, "
            "visible text, and links. Use this when "
            "the browser state must be inspected."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        "strict": True,
    },

    # --------------------------------------------------------
    # CONTROLLED BROWSER CLICK
    # --------------------------------------------------------

    {
        "type": "function",
        "name": "browser_click",
        "description": (
            "Click a visible link in the currently open "
            "controlled browser. The index MUST come from "
            "a previous browser observation. Never invent "
            "a link index."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "index": {
                    "type": "integer",
                    "description": (
                        "The exact visible-link index "
                        "returned by browser_observe."
                    ),
                },
            },
            "required": [
                "index",
            ],
            "additionalProperties": False,
        },
        "strict": True,
    },

    # --------------------------------------------------------
    # CONTROLLED BROWSER BACK
    # --------------------------------------------------------

    {
        "type": "function",
        "name": "browser_back",
        "description": (
            "Navigate the controlled browser back to "
            "the previous page and verify the result."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        "strict": True,
    },

    # --------------------------------------------------------
    # CONTROLLED BROWSER CLOSE
    # --------------------------------------------------------

    {
        "type": "function",
        "name": "browser_close",
        "description": (
            "Close JARVIS's controlled browser session."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        "strict": True,
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
    "browser_close": tool_browser_close,
}