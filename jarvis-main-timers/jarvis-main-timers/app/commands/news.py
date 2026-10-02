import re

from news import (
    open_news_dashboard,
    close_news_dashboard,
    refresh_news_dashboard,
    load_all_news_sources,
    read_source_headline,
    get_news_source_count,
)


# ============================================================
# NUMBER WORDS
# ============================================================

NUMBER_WORDS = {
    "one": 1,
    "first": 1,

    "two": 2,
    "second": 2,

    "three": 3,
    "third": 3,

    "four": 4,
    "fourth": 4,

    "five": 5,
    "fifth": 5,

    "six": 6,
    "sixth": 6,
}


# ============================================================
# NORMALIZE
# ============================================================

def normalize(text):
    return " ".join(
        (text or "").lower().strip().split()
    )


# ============================================================
# NUMBER
# ============================================================

def parse_number(value):
    value = normalize(value)

    if value.isdigit():
        return int(value)

    return NUMBER_WORDS.get(value)


# ============================================================
# SOURCE NUMBER
#
# first news
# second news
# third news
#
# first news headline 2
# second news headline 5
# ============================================================

def extract_source_number(command):

    c = normalize(command)

    patterns = [
        r"\b(first|second|third|fourth|fifth|sixth|[1-6])\s+news\b",
        r"\bnews\s+(first|second|third|fourth|fifth|sixth|[1-6])\b",
    ]

    for pattern in patterns:

        match = re.search(pattern, c)

        if match:

            number = parse_number(
                match.group(1)
            )

            if number is not None:
                return number

    return None


# ============================================================
# HEADLINE NUMBER
#
# headline 1
# headline first
# headline 5
# ============================================================

def extract_headline_number(command):

    c = normalize(command)

    match = re.search(
        r"\bheadline\s+"
        r"(one|first|two|second|three|third|"
        r"four|fourth|five|fifth|[1-5])\b",
        c,
    )

    if not match:
        return None

    return parse_number(
        match.group(1)
    )


# ============================================================
# NEWS COMMAND DETECTION
# ============================================================

def is_news_command(command):

    c = normalize(command)

    if not c:
        return False

    # --------------------------------------------------------
    # MAIN NEWS CENTER
    # --------------------------------------------------------

    if c in {
        "news",
        "run news",
        "open news",
        "show news",
        "open news center",
        "open news dashboard",
        "show news center",
        "show news dashboard",
    }:
        return True

    # --------------------------------------------------------
    # REFRESH
    # --------------------------------------------------------

    if c in {
        "refresh news",
        "refresh news center",
        "refresh news dashboard",
    }:
        return True

    # --------------------------------------------------------
    # CLOSE
    # --------------------------------------------------------

    if c in {
        "close news",
        "close news center",
        "close news dashboard",
        "stop news",
    }:
        return True

    # --------------------------------------------------------
    # SOURCE + HEADLINE
    #
    # first news headline 2
    # second news headline 5
    # --------------------------------------------------------

    source_number = extract_source_number(c)

    if source_number is not None:
        return True

    # --------------------------------------------------------
    # TOPIC NEWS
    #
    # politics news
    # news politics
    # technology news
    # sports news
    # --------------------------------------------------------

    if c.startswith("news "):
        return True

    if c.endswith(" news"):
        return True

    if c.startswith("open news "):
        return True

    if c.startswith("open ") and c.endswith(" news"):
        return True

    return False


# ============================================================
# TOPIC EXTRACTION
# ============================================================

def extract_topic(command):

    c = normalize(command)

    topic_aliases = {
        "world": "world",
        "international": "world",
        "global": "world",

        "technology": "technology",
        "tech": "technology",

        "business": "business",
        "finance": "business",
        "economy": "business",

        "science": "science",

        "sports": "sports",
        "sport": "sports",
        "football": "sports",
        "soccer": "sports",

        "health": "health",

        "ai": "ai",
        "artificial intelligence": "ai",

        "gaming": "gaming",
        "games": "gaming",

        "politics": "politics",
        "political": "politics",

        "space": "space",
        "nasa": "space",

        "environment": "environment",
        "climate": "environment",

        "entertainment": "entertainment",
        "movies": "entertainment",
        "music": "entertainment",

        "middle east": "middleeast",
        "middle eastern": "middleeast",
    }

    for alias in sorted(
        topic_aliases,
        key=len,
        reverse=True,
    ):

        if alias in c:
            return topic_aliases[alias]

    return "default"


# ============================================================
# HANDLER
# ============================================================

def handle_news(command):

    c = normalize(command)

    if not c:
        return None

    # --------------------------------------------------------
    # SOURCE + HEADLINE
    #
    # first news headline 2
    # second news headline 5
    # third news
    # --------------------------------------------------------

    source_number = extract_source_number(c)

    if source_number is not None:

        headline_number = (
            extract_headline_number(c)
        )

        if headline_number is None:
            headline_number = 1

        return read_source_headline(
            source_number,
            headline_number,
        )

    # --------------------------------------------------------
    # CLOSE
    # --------------------------------------------------------

    if c in {
        "close news",
        "close news center",
        "close news dashboard",
        "stop news",
    }:

        return close_news_dashboard()

    # --------------------------------------------------------
    # REFRESH
    # --------------------------------------------------------

    if c in {
        "refresh news",
        "refresh news center",
        "refresh news dashboard",
    }:

        return refresh_news_dashboard()

    # --------------------------------------------------------
    # DEFAULT NEWS
    #
    # news
    # run news
    # open news
    #
    # IMPORTANT:
    # This loads 5 stories from EACH of the 6 sources.
    # It does NOT read them.
    # --------------------------------------------------------

    if c in {
        "news",
        "run news",
        "open news",
        "show news",
        "open news center",
        "open news dashboard",
        "show news center",
        "show news dashboard",
    }:

        return open_news_dashboard(
            "default"
        )

    # --------------------------------------------------------
    # TOPIC NEWS
    #
    # politics news
    # news politics
    # open news politics
    # --------------------------------------------------------

    topic = extract_topic(c)

    if topic != "default":

        return open_news_dashboard(
            topic
        )

    return None