import ctypes
import html
import os
import re
import shutil
import subprocess
import time
import urllib.request
import xml.etree.ElementTree as ET


# ============================================================
# J.A.R.V.I.S. — NEWS ENGINE
# ============================================================

NEWS_FEEDS = {

    # --------------------------------------------------------
    # DEFAULT
    # --------------------------------------------------------

    "default": [
        ("BBC News", "https://feeds.bbci.co.uk/news/rss.xml"),
        ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
        ("Sky News", "https://feeds.skynews.com/feeds/rss/home.xml"),
        ("NPR", "https://feeds.npr.org/1001/rss.xml"),
        ("Guardian", "https://www.theguardian.com/world/rss"),
        ("Google News", "https://news.google.com/rss"),
    ],

    # --------------------------------------------------------
    # WORLD
    # --------------------------------------------------------

    "world": [
        ("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml"),
        ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
        ("Sky News", "https://feeds.skynews.com/feeds/rss/world.xml"),
        ("NPR World", "https://feeds.npr.org/1004/rss.xml"),
        ("Guardian World", "https://www.theguardian.com/world/rss"),
        (
            "Google News",
            "https://news.google.com/rss/headlines/section/topic/WORLD",
        ),
    ],

    # --------------------------------------------------------
    # TECHNOLOGY
    # --------------------------------------------------------

    "technology": [
        ("BBC Technology", "https://feeds.bbci.co.uk/news/technology/rss.xml"),
        ("The Verge", "https://www.theverge.com/rss/index.xml"),
        ("Wired", "https://www.wired.com/feed/rss"),
        ("TechCrunch", "https://techcrunch.com/feed/"),
        (
            "Ars Technica",
            "https://feeds.arstechnica.com/arstechnica/index",
        ),
        (
            "Google News Tech",
            "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY",
        ),
    ],

    # --------------------------------------------------------
    # BUSINESS
    # --------------------------------------------------------

    "business": [
        ("BBC Business", "https://feeds.bbci.co.uk/news/business/rss.xml"),
        (
            "CNBC",
            "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        ),
        ("Forbes", "https://www.forbes.com/business/feed/"),
        (
            "MarketWatch",
            "https://feeds.marketwatch.com/marketwatch/topstories/",
        ),
        ("Guardian Business", "https://www.theguardian.com/business/rss"),
        (
            "Google News Business",
            "https://news.google.com/rss/headlines/section/topic/BUSINESS",
        ),
    ],

    # --------------------------------------------------------
    # SCIENCE
    # --------------------------------------------------------

    "science": [
        (
            "BBC Science",
            "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
        ),
        ("New Scientist", "https://www.newscientist.com/feed/home/"),
        (
            "ScienceDaily",
            "https://www.sciencedaily.com/rss/top/science.xml",
        ),
        (
            "NASA",
            "https://www.nasa.gov/rss/dyn/breaking_news.rss",
        ),
        ("Live Science", "https://www.livescience.com/feeds/all"),
        (
            "Google News Science",
            "https://news.google.com/rss/headlines/section/topic/SCIENCE",
        ),
    ],

    # --------------------------------------------------------
    # SPORTS
    # --------------------------------------------------------

    "sports": [
        ("BBC Sport", "https://feeds.bbci.co.uk/sport/rss.xml"),
        ("Sky Sports", "https://www.skysports.com/rss/12040"),
        ("ESPN", "https://www.espn.com/espn/rss/news"),
        ("Guardian Sport", "https://www.theguardian.com/sport/rss"),
        ("Goal", "https://www.goal.com/feeds/en/news"),
        (
            "Google News Sports",
            "https://news.google.com/rss/headlines/section/topic/SPORTS",
        ),
    ],

    # --------------------------------------------------------
    # HEALTH
    # --------------------------------------------------------

    "health": [
        ("BBC Health", "https://feeds.bbci.co.uk/news/health/rss.xml"),
        (
            "WHO",
            "https://www.who.int/feeds/entity/mediacentre/news/en/rss.xml",
        ),
        (
            "WebMD",
            "https://rssfeeds.webmd.com/rss/rss.aspx?RSSSource=RSS_PUBLIC",
        ),
        ("Healthline", "https://www.healthline.com/rss"),
        (
            "Medical News Today",
            "https://www.medicalnewstoday.com/rss",
        ),
        (
            "Google News Health",
            "https://news.google.com/rss/headlines/section/topic/HEALTH",
        ),
    ],

    # --------------------------------------------------------
    # AI
    # --------------------------------------------------------

    "ai": [
        (
            "MIT Technology Review",
            "https://www.technologyreview.com/feed/",
        ),
        (
            "The Verge AI",
            "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        ),
        (
            "Wired AI",
            "https://www.wired.com/feed/tag/ai/latest/rss",
        ),
        ("VentureBeat", "https://venturebeat.com/feed/"),
        ("Hacker News", "https://news.ycombinator.com/rss"),
        (
            "Google News AI",
            "https://news.google.com/rss/search?q=artificial+intelligence",
        ),
    ],

    # --------------------------------------------------------
    # GAMING
    # --------------------------------------------------------

    "gaming": [
        ("IGN", "https://feeds.ign.com/ignfeeds"),
        ("Kotaku", "https://kotaku.com/rss"),
        (
            "Rock Paper Shotgun",
            "https://www.rockpapershotgun.com/feed",
        ),
        ("PC Gamer", "https://www.pcgamer.com/rss/"),
        ("Eurogamer", "https://www.eurogamer.net/feed"),
        (
            "Google News Gaming",
            "https://news.google.com/rss/search?q=gaming",
        ),
    ],

    # --------------------------------------------------------
    # POLITICS
    # --------------------------------------------------------

    "politics": [
        (
            "BBC Politics",
            "https://feeds.bbci.co.uk/news/politics/rss.xml",
        ),
        (
            "Guardian Politics",
            "https://www.theguardian.com/politics/rss",
        ),
        (
            "Politico",
            "https://www.politico.com/rss/politicopicks.xml",
        ),
        ("The Hill", "https://thehill.com/feed/"),
        (
            "NPR Politics",
            "https://feeds.npr.org/1014/rss.xml",
        ),
        (
            "Google News Politics",
            "https://news.google.com/rss/headlines/section/topic/POLITICS",
        ),
    ],

    # --------------------------------------------------------
    # SPACE
    # --------------------------------------------------------

    "space": [
        (
            "NASA",
            "https://www.nasa.gov/rss/dyn/breaking_news.rss",
        ),
        ("Space.com", "https://www.space.com/feeds/all"),
        (
            "Universe Today",
            "https://www.universetoday.com/feed/",
        ),
        (
            "Sky & Telescope",
            "https://skyandtelescope.org/feed/",
        ),
        (
            "NASA Spaceflight",
            "https://www.nasaspaceflight.com/feed/",
        ),
        (
            "Google News Space",
            "https://news.google.com/rss/search?q=space+NASA",
        ),
    ],

    # --------------------------------------------------------
    # ENVIRONMENT
    # --------------------------------------------------------

    "environment": [
        (
            "BBC Environment",
            "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
        ),
        (
            "Guardian Environment",
            "https://www.theguardian.com/environment/rss",
        ),
        (
            "NASA Climate",
            "https://climate.nasa.gov/rss/",
        ),
        (
            "Carbon Brief",
            "https://www.carbonbrief.org/feed/",
        ),
        (
            "NPR Environment",
            "https://feeds.npr.org/1025/rss.xml",
        ),
        (
            "Google News Environment",
            "https://news.google.com/rss/search?q=climate+environment",
        ),
    ],

    # --------------------------------------------------------
    # ENTERTAINMENT
    # --------------------------------------------------------

    "entertainment": [
        (
            "BBC Entertainment",
            "https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml",
        ),
        (
            "Rolling Stone",
            "https://www.rollingstone.com/feed/",
        ),
        ("Variety", "https://variety.com/feed/"),
        (
            "Hollywood Reporter",
            "https://www.hollywoodreporter.com/feed/",
        ),
        ("Deadline", "https://deadline.com/feed/"),
        (
            "Google News Entertainment",
            "https://news.google.com/rss/headlines/section/topic/ENTERTAINMENT",
        ),
    ],

    # --------------------------------------------------------
    # MIDDLE EAST
    # --------------------------------------------------------

    "middleeast": [
        (
            "Al Jazeera",
            "https://www.aljazeera.com/xml/rss/all.xml",
        ),
        (
            "BBC Middle East",
            "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml",
        ),
        ("Arab News", "https://www.arabnews.com/rss.xml"),
        ("Gulf News", "https://gulfnews.com/rss"),
        (
            "NPR World",
            "https://feeds.npr.org/1004/rss.xml",
        ),
        (
            "Google News Middle East",
            "https://news.google.com/rss/search?q=Middle+East",
        ),
    ],
}


# ============================================================
# TOPIC ALIASES
# ============================================================

TOPIC_ALIASES = {
    "tech": "technology",
    "technology": "technology",
    "coding": "technology",
    "programming": "technology",
    "startup": "technology",

    "finance": "business",
    "economy": "business",
    "markets": "business",
    "market": "business",
    "stocks": "business",
    "crypto": "business",
    "money": "business",

    "football": "sports",
    "soccer": "sports",
    "basketball": "sports",
    "sport": "sports",

    "medicine": "health",
    "fitness": "health",
    "covid": "health",

    "machine learning": "ai",
    "artificial intelligence": "ai",
    "openai": "ai",
    "gpt": "ai",

    "games": "gaming",
    "video games": "gaming",
    "game": "gaming",

    "climate": "environment",
    "climate change": "environment",
    "green energy": "environment",
    "nature": "environment",

    "astronomy": "space",
    "nasa": "space",
    "spacex": "space",
    "rockets": "space",

    "movies": "entertainment",
    "music": "entertainment",
    "film": "entertainment",
    "celebrity": "entertainment",
    "tv": "entertainment",

    "middle east": "middleeast",
    "middle eastern": "middleeast",
    "arab": "middleeast",
    "arabic": "middleeast",
    "egypt": "middleeast",
    "egyptian": "middleeast",
    "iran": "middleeast",
    "saudi": "middleeast",
    "gulf": "middleeast",
    "palestine": "middleeast",
    "israel": "middleeast",
    "iraq": "middleeast",
    "syria": "middleeast",
    "lebanon": "middleeast",
    "yemen": "middleeast",
    "jordan": "middleeast",

    "politics": "politics",
    "political": "politics",
    "election": "politics",
    "elections": "politics",
    "congress": "politics",
    "government": "politics",

    "world": "world",
    "international": "world",
    "global": "world",
}


# ============================================================
# VISUAL NEWS SOURCES
# ============================================================

NEWS_WEBSITES = {

    "default": [
        ("BBC News", "https://www.bbc.com/news"),
        ("Al Jazeera", "https://www.aljazeera.com/"),
        ("Sky News", "https://news.sky.com/"),
        ("NPR", "https://www.npr.org/"),
        ("The Guardian", "https://www.theguardian.com/world"),
        ("Google News", "https://news.google.com/"),
    ],

    "world": [
        ("BBC World", "https://www.bbc.com/news/world"),
        ("Al Jazeera", "https://www.aljazeera.com/"),
        ("Sky News World", "https://news.sky.com/world"),
        ("NPR World", "https://www.npr.org/sections/world/"),
        ("Guardian World", "https://www.theguardian.com/world"),
        ("Google News World", "https://news.google.com/"),
    ],

    "technology": [
        ("BBC Technology", "https://www.bbc.com/news/technology"),
        ("The Verge", "https://www.theverge.com/tech"),
        ("Wired", "https://www.wired.com/"),
        ("TechCrunch", "https://techcrunch.com/"),
        ("Ars Technica", "https://arstechnica.com/"),
        ("Google News Technology", "https://news.google.com/"),
    ],

    "business": [
        ("BBC Business", "https://www.bbc.com/news/business"),
        ("CNBC", "https://www.cnbc.com/"),
        ("Forbes", "https://www.forbes.com/"),
        ("MarketWatch", "https://www.marketwatch.com/"),
        ("Guardian Business", "https://www.theguardian.com/business"),
        ("Google News Business", "https://news.google.com/"),
    ],

    "science": [
        ("BBC Science", "https://www.bbc.com/news/science_and_environment"),
        ("New Scientist", "https://www.newscientist.com/"),
        ("ScienceDaily", "https://www.sciencedaily.com/"),
        ("NASA", "https://www.nasa.gov/"),
        ("Live Science", "https://www.livescience.com/"),
        ("Google News Science", "https://news.google.com/"),
    ],

    "sports": [
        ("BBC Sport", "https://www.bbc.com/sport"),
        ("Sky Sports", "https://www.skysports.com/"),
        ("ESPN", "https://www.espn.com/"),
        ("Guardian Sport", "https://www.theguardian.com/sport"),
        ("Goal", "https://www.goal.com/"),
        ("Google News Sports", "https://news.google.com/"),
    ],

    "health": [
        ("BBC Health", "https://www.bbc.com/news/health"),
        ("WHO", "https://www.who.int/news"),
        ("WebMD", "https://www.webmd.com/"),
        ("Healthline", "https://www.healthline.com/"),
        ("Medical News Today", "https://www.medicalnewstoday.com/"),
        ("Google News Health", "https://news.google.com/"),
    ],

    "ai": [
        ("MIT Technology Review", "https://www.technologyreview.com/"),
        (
            "The Verge AI",
            "https://www.theverge.com/ai-artificial-intelligence",
        ),
        (
            "Wired AI",
            "https://www.wired.com/tag/artificial-intelligence/",
        ),
        ("VentureBeat", "https://venturebeat.com/ai/"),
        ("Hacker News", "https://news.ycombinator.com/"),
        ("Google News AI", "https://news.google.com/"),
    ],

    "gaming": [
        ("IGN", "https://www.ign.com/"),
        ("Kotaku", "https://kotaku.com/"),
        ("Rock Paper Shotgun", "https://www.rockpapershotgun.com/"),
        ("PC Gamer", "https://www.pcgamer.com/"),
        ("Eurogamer", "https://www.eurogamer.net/"),
        ("Google News Gaming", "https://news.google.com/"),
    ],

    "politics": [
        ("BBC Politics", "https://www.bbc.com/news/politics"),
        ("Guardian Politics", "https://www.theguardian.com/politics"),
        ("Politico", "https://www.politico.com/"),
        ("The Hill", "https://thehill.com/"),
        ("NPR Politics", "https://www.npr.org/sections/politics/"),
        ("Google News Politics", "https://news.google.com/"),
    ],

    "space": [
        ("NASA", "https://www.nasa.gov/"),
        ("Space.com", "https://www.space.com/"),
        ("Universe Today", "https://www.universetoday.com/"),
        ("Sky & Telescope", "https://skyandtelescope.org/"),
        ("NASA Spaceflight", "https://www.nasaspaceflight.com/"),
        ("Google News Space", "https://news.google.com/"),
    ],

    "environment": [
        (
            "BBC Environment",
            "https://www.bbc.com/news/science_and_environment",
        ),
        (
            "Guardian Environment",
            "https://www.theguardian.com/environment",
        ),
        ("NASA Climate", "https://climate.nasa.gov/"),
        ("Carbon Brief", "https://www.carbonbrief.org/"),
        ("NPR Environment", "https://www.npr.org/sections/climate/"),
        ("Google News Environment", "https://news.google.com/"),
    ],

    "entertainment": [
        ("BBC Entertainment", "https://www.bbc.com/culture"),
        ("Rolling Stone", "https://www.rollingstone.com/"),
        ("Variety", "https://variety.com/"),
        ("Hollywood Reporter", "https://www.hollywoodreporter.com/"),
        ("Deadline", "https://deadline.com/"),
        ("Google News Entertainment", "https://news.google.com/"),
    ],

    "middleeast": [
        ("Al Jazeera", "https://www.aljazeera.com/"),
        (
            "BBC Middle East",
            "https://www.bbc.com/news/world/middle_east",
        ),
        ("Arab News", "https://www.arabnews.com/"),
        ("Gulf News", "https://gulfnews.com/"),
        ("NPR World", "https://www.npr.org/sections/world/"),
        ("Google News Middle East", "https://news.google.com/"),
    ],
}

# ============================================================
# JARVIS NEWS STATE
# ============================================================

NEWS_WINDOWS = set()

LAST_TOPIC = "default"

# ------------------------------------------------------------
# NEW NEWS STATE
#
# Every source gets its OWN five stories.
#
# {
#     "BBC News": [story1, story2, story3, story4, story5],
#     "Al Jazeera": [story1, story2, story3, story4, story5],
#     ...
# }
# ------------------------------------------------------------

NEWS_SOURCE_STORIES = {}

NEWS_SOURCE_ORDER = []


# ============================================================
# HELPERS
# ============================================================

def normalize(text):

    return " ".join(
        (text or "").lower().strip().split()
    )


def resolve_topic(command):

    c = normalize(command)

    aliases = sorted(
        TOPIC_ALIASES.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    )

    for alias, topic in aliases:

        if alias in c:
            return topic

    return "default"


# ============================================================
# RSS FETCH
# ============================================================

def _fetch_feed(url, count=5):

    try:

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "JARVIS-News/6.0"
                )
            },
        )

        with urllib.request.urlopen(
            request,
            timeout=10,
        ) as response:

            data = response.read()

        root = ET.fromstring(data)

        stories = []

        seen = set()

        # ----------------------------------------------------
        # RSS
        # ----------------------------------------------------

        for item in root.findall(".//item"):

            title = item.findtext("title")

            if not title:
                continue

            title = html.unescape(
                title
            )

            title = re.sub(
                r"\s+",
                " ",
                title,
            ).strip()

            key = normalize(title)

            if key in seen:
                continue

            seen.add(key)

            link = item.findtext(
                "link"
            ) or ""

            description = (
                item.findtext(
                    "description"
                )
                or ""
            )

            description = html.unescape(
                description
            )

            description = re.sub(
                r"<[^>]+>",
                " ",
                description,
            )

            description = re.sub(
                r"\s+",
                " ",
                description,
            ).strip()

            if not description:
                description = title

            stories.append(
                {
                    "title": title,
                    "description": description,
                    "link": link,
                }
            )

            if len(stories) >= count:
                break

        # ----------------------------------------------------
        # ATOM FALLBACK
        # ----------------------------------------------------

        if not stories:

            for entry in root.findall(
                ".//{http://www.w3.org/2005/Atom}entry"
            ):

                title_node = entry.find(
                    "{http://www.w3.org/2005/Atom}title"
                )

                if title_node is None:
                    continue

                title = (
                    title_node.text
                    or ""
                ).strip()

                if not title:
                    continue

                title = html.unescape(
                    title
                )

                key = normalize(title)

                if key in seen:
                    continue

                seen.add(key)

                description_node = entry.find(
                    "{http://www.w3.org/2005/Atom}summary"
                )

                description = ""

                if description_node is not None:

                    description = (
                        description_node.text
                        or ""
                    )

                link = ""

                link_node = entry.find(
                    "{http://www.w3.org/2005/Atom}link"
                )

                if link_node is not None:

                    link = link_node.attrib.get(
                        "href",
                        "",
                    )

                description = re.sub(
                    r"<[^>]+>",
                    " ",
                    description,
                )

                description = re.sub(
                    r"\s+",
                    " ",
                    description,
                ).strip()

                if not description:
                    description = title

                stories.append(
                    {
                        "title": title,
                        "description": description,
                        "link": link,
                    }
                )

                if len(stories) >= count:
                    break

        return stories

    except Exception as e:

        print(
            "[NEWS FEED ERROR]",
            url,
            repr(e),
        )

        return []


# ============================================================
# LOAD ALL SIX SOURCES
# ============================================================

def load_all_news_sources(
    topic="default"
):

    global NEWS_SOURCE_STORIES
    global NEWS_SOURCE_ORDER
    global LAST_TOPIC

    topic = TOPIC_ALIASES.get(
        normalize(topic),
        normalize(topic),
    )

    if topic not in NEWS_FEEDS:
        topic = "default"

    NEWS_SOURCE_STORIES = {}

    NEWS_SOURCE_ORDER = []

    feeds = NEWS_FEEDS.get(
        topic,
        [],
    )

    print(
        f"[NEWS] Loading {len(feeds)} "
        f"sources for topic: {topic}"
    )

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # NEWS_FEEDS contains:
    #
    # ("BBC News", "https://...")
    #
    # so we MUST unpack source_name and url.
    # --------------------------------------------------------

    for source_name, url in feeds[:6]:

        print(
            f"[NEWS] Loading: {source_name}"
        )

        stories = _fetch_feed(
            url,
            count=5,
        )

        if not stories:

            print(
                f"[NEWS] No stories from "
                f"{source_name}"
            )

            continue

        NEWS_SOURCE_STORIES[
            source_name
        ] = stories

        NEWS_SOURCE_ORDER.append(
            source_name
        )

        print(
            f"[NEWS] {source_name}: "
            f"{len(stories)} stories loaded"
        )

    LAST_TOPIC = topic

    total = sum(
        len(stories)
        for stories in NEWS_SOURCE_STORIES.values()
    )

    print(
        f"[NEWS] Finished loading "
        f"{len(NEWS_SOURCE_ORDER)} sources "
        f"and {total} stories"
    )

    return NEWS_SOURCE_STORIES


# ============================================================
# SOURCE COUNT
# ============================================================

def get_news_source_count():

    return len(
        NEWS_SOURCE_ORDER
    )


# ============================================================
# READ SOURCE HEADLINE
# ============================================================

def read_source_headline(
    source_number,
    headline_number=1,
):

    if not NEWS_SOURCE_ORDER:

        return (
            "The News Center is not loaded yet, Sir. "
            "Say news first."
        )

    try:

        source_number = int(
            source_number
        )

        headline_number = int(
            headline_number
        )

    except Exception:

        return (
            "I couldn't determine the "
            "news source or headline, Sir."
        )

    # --------------------------------------------------------
    # SOURCE
    # --------------------------------------------------------

    if (
        source_number < 1
        or source_number > len(
            NEWS_SOURCE_ORDER
        )
    ):

        return (
            f"I only have "
            f"{len(NEWS_SOURCE_ORDER)} "
            f"news sources loaded, Sir."
        )

    source_name = NEWS_SOURCE_ORDER[
        source_number - 1
    ]

    stories = NEWS_SOURCE_STORIES.get(
        source_name,
        [],
    )

    # --------------------------------------------------------
    # HEADLINE
    # --------------------------------------------------------

    if (
        headline_number < 1
        or headline_number > len(stories)
    ):

        return (
            f"{source_name} has "
            f"{len(stories)} loaded headlines, "
            f"Sir."
        )

    story = stories[
        headline_number - 1
    ]

    title = story.get(
        "title",
        "Untitled story",
    )

    description = story.get(
        "description",
        "",
    ).strip()

    # --------------------------------------------------------
    # DO NOT REPEAT DESCRIPTION IF IT IS JUST THE TITLE
    # --------------------------------------------------------

    if normalize(
        description
    ) == normalize(title):

        description = ""

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    if description:

        return (
            f"Reading {source_name}, "
            f"headline {headline_number}, Sir. "
            f"The headline is: {title}. "
            f"Here is the report: "
            f"{description}"
        )

    return (
        f"Reading {source_name}, "
        f"headline {headline_number}, Sir. "
        f"The headline is: {title}."
    )


# ============================================================
# BROWSER DETECTION
# ============================================================

def _find_browser():

    candidates = []

    for executable in (
        "chrome.exe",
        "msedge.exe",
        "firefox.exe",
        "brave.exe",
    ):

        found = shutil.which(
            executable
        )

        if found:
            candidates.append(
                found
            )

    candidates.extend(
        [
            os.path.expandvars(
                r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"
            ),
            os.path.expandvars(
                r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
            ),
            os.path.expandvars(
                r"%LocalAppData%\Google\Chrome\Application\chrome.exe"
            ),
            os.path.expandvars(
                r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
            ),
            os.path.expandvars(
                r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
            ),
            os.path.expandvars(
                r"%ProgramFiles%\BraveSoftware\Brave-Browser\Application\brave.exe"
            ),
            os.path.expandvars(
                r"%LocalAppData%\BraveSoftware\Brave-Browser\Application\brave.exe"
            ),
        ]
    )

    for path in candidates:

        if path and os.path.isfile(path):
            return path

    return None


# ============================================================
# WINDOWS API
# ============================================================

def _enum_windows():

    if os.name != "nt":
        return []

    user32 = ctypes.windll.user32

    windows = []

    EnumWindowsProc = ctypes.WINFUNCTYPE(
        ctypes.c_bool,
        ctypes.c_void_p,
        ctypes.c_void_p,
    )

    def callback(hwnd, _):

        if not user32.IsWindowVisible(hwnd):
            return True

        if user32.IsIconic(hwnd):
            return True

        windows.append(hwnd)

        return True

    user32.EnumWindows(
        EnumWindowsProc(callback),
        0,
    )

    return windows


def _window_title(hwnd):

    user32 = ctypes.windll.user32

    length = user32.GetWindowTextLengthW(
        hwnd
    )

    if length <= 0:
        return ""

    buffer = ctypes.create_unicode_buffer(
        length + 1
    )

    user32.GetWindowTextW(
        hwnd,
        buffer,
        length + 1,
    )

    return buffer.value


def _snapshot_windows():

    return set(
        _enum_windows()
    )


def _wait_for_new_window(
    previous_windows,
    timeout=8,
):

    deadline = (
        time.time() + timeout
    )

    while time.time() < deadline:

        current = _snapshot_windows()

        new_windows = (
            current - previous_windows
        )

        if new_windows:

            titled = [
                hwnd
                for hwnd in new_windows
                if _window_title(hwnd)
            ]

            if titled:
                return titled[0]

            return next(
                iter(new_windows)
            )

        time.sleep(0.25)

    return None


def _set_window_position(
    hwnd,
    x,
    y,
    width,
    height,
):

    if not hwnd:
        return False

    try:

        user32 = ctypes.windll.user32

        SWP_NOZORDER = 0x0004
        SWP_SHOWWINDOW = 0x0040

        user32.ShowWindow(
            hwnd,
            9,
        )

        result = user32.SetWindowPos(
            hwnd,
            0,
            int(x),
            int(y),
            int(width),
            int(height),
            SWP_NOZORDER
            | SWP_SHOWWINDOW,
        )

        return bool(result)

    except Exception as e:

        print(
            "[NEWS WINDOW ERROR]",
            repr(e),
        )

        return False


# ============================================================
# SCREEN
# ============================================================

def _get_screen_size():

    try:

        user32 = ctypes.windll.user32

        return (
            user32.GetSystemMetrics(0),
            user32.GetSystemMetrics(1),
        )

    except Exception:

        return (
            1920,
            1080,
        )


# ============================================================
# TILE SIX WINDOWS
# ============================================================

def _tile_windows(windows):

    windows = [
        hwnd
        for hwnd in windows
        if hwnd
    ]

    if not windows:
        return

    screen_width, screen_height = (
        _get_screen_size()
    )

    margin = 8
    gap = 8

    columns = 3
    rows = 2

    usable_width = (
        screen_width
        - (margin * 2)
        - (gap * (columns - 1))
    )

    usable_height = (
        screen_height
        - (margin * 2)
        - (gap * (rows - 1))
    )

    cell_width = (
        usable_width // columns
    )

    cell_height = (
        usable_height // rows
    )

    layout = [
        (0, 0),
        (1, 0),
        (2, 0),
        (0, 1),
        (1, 1),
        (2, 1),
    ]

    for hwnd, (
        column,
        row,
    ) in zip(
        windows[:6],
        layout,
    ):

        x = (
            margin
            + column
            * (cell_width + gap)
        )

        y = (
            margin
            + row
            * (cell_height + gap)
        )

        _set_window_position(
            hwnd,
            x,
            y,
            cell_width,
            cell_height,
        )


# ============================================================
# CLOSE NEWS WINDOWS
# ============================================================

def _close_window(hwnd):

    try:

        user32 = ctypes.windll.user32

        WM_CLOSE = 0x0010

        user32.PostMessageW(
            hwnd,
            WM_CLOSE,
            0,
            0,
        )

        return True

    except Exception as e:

        print(
            "[NEWS CLOSE ERROR]",
            repr(e),
        )

        return False


def close_news_dashboard(
    silent=False
):

    global NEWS_WINDOWS

    if os.name != "nt":

        NEWS_WINDOWS.clear()

        if silent:
            return None

        return (
            "News windows can only be "
            "managed on Windows, Sir."
        )

    closed = 0

    for hwnd in list(
        NEWS_WINDOWS
    ):

        try:

            if ctypes.windll.user32.IsWindow(
                hwnd
            ):

                if _close_window(hwnd):
                    closed += 1

        except Exception:
            pass

    NEWS_WINDOWS.clear()

    if silent:
        return None

    if closed:

        return (
            "Closing the News Center, Sir. "
            f"I closed {closed} news windows."
        )

    return (
        "There are no JARVIS News "
        "windows open, Sir."
    )


# ============================================================
# OPEN NEWS DASHBOARD
# ============================================================

def open_news_dashboard(
    topic="default"
):

    global LAST_TOPIC

    topic = TOPIC_ALIASES.get(
        normalize(topic),
        normalize(topic),
    )

    if topic not in NEWS_FEEDS:
        topic = "default"

    # --------------------------------------------------------
    # STEP 1
    #
    # Load FIVE stories from EVERY source.
    # --------------------------------------------------------

    load_all_news_sources(
        topic
    )

    # --------------------------------------------------------
    # STEP 2
    #
    # Find browser.
    # --------------------------------------------------------

    browser = _find_browser()

    if not browser:

        return (
            "I couldn't find a supported "
            "browser on this PC, Sir."
        )

    # --------------------------------------------------------
    # STEP 3
    #
    # Close only windows previously opened by JARVIS.
    # --------------------------------------------------------

    close_news_dashboard(
        silent=True
    )

    # --------------------------------------------------------
    # STEP 4
    #
    # Open exactly six website windows.
    # --------------------------------------------------------

    sources = NEWS_WEBSITES.get(
        topic,
        NEWS_WEBSITES.get(
            "default",
            [],
        ),
    )[:6]

    opened_windows = []

    print(
        f"[NEWS] Opening "
        f"{len(sources)} source windows"
    )

    for source_name, url in sources:

        previous_windows = (
            _snapshot_windows()
        )

        try:

            subprocess.Popen(
                [
                    browser,
                    "--new-window",
                    url,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        except Exception as e:

            print(
                "[NEWS OPEN ERROR]",
                source_name,
                repr(e),
            )

            continue

        hwnd = _wait_for_new_window(
            previous_windows,
            timeout=6,
        )

        if hwnd:

            opened_windows.append(
                hwnd
            )

            NEWS_WINDOWS.add(
                hwnd
            )

            print(
                f"[NEWS] Opened: "
                f"{source_name}"
            )

        else:

            print(
                "[NEWS] Could not track "
                f"window: {source_name}"
            )

    # --------------------------------------------------------
    # STEP 5
    #
    # Tile the six windows.
    # --------------------------------------------------------

    if opened_windows:

        time.sleep(1)

        _tile_windows(
            opened_windows
        )

    LAST_TOPIC = topic

    # --------------------------------------------------------
    # STEP 6
    #
    # Report loaded state.
    # --------------------------------------------------------

    loaded_sources = len(
        NEWS_SOURCE_ORDER
    )

    total_stories = sum(
        len(stories)
        for stories
        in NEWS_SOURCE_STORIES.values()
    )

    if not opened_windows:

        return (
            "I couldn't open the "
            "News Center, Sir."
        )

    return (
        f"News Center ready, Sir. "
        f"I opened {len(opened_windows)} "
        f"news source windows and loaded "
        f"{total_stories} stories from "
        f"{loaded_sources} sources. "
        f"Five headlines are ready from "
        f"each source. Nothing is being "
        f"read yet."
    )


# ============================================================
# REFRESH
# ============================================================

def refresh_news_dashboard(
    topic=None
):

    if not topic:
        topic = LAST_TOPIC

    return open_news_dashboard(
        topic
    )