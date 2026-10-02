import urllib.parse
import webbrowser


WEBSITES = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "github": "https://github.com",
    "gmail": "https://mail.google.com",
    "chatgpt": "https://chatgpt.com",
    "reddit": "https://www.reddit.com",
    "instagram": "https://www.instagram.com",
    "facebook": "https://www.facebook.com",
    "linkedin": "https://www.linkedin.com",
    "discord": "https://discord.com",
    "spotify": "https://open.spotify.com",
    "netflix": "https://www.netflix.com",
    "amazon": "https://www.amazon.com",
    "drive": "https://drive.google.com",
    "docs": "https://docs.google.com",
    "sheets": "https://sheets.google.com",
    "notion": "https://www.notion.so",
}


def open_website(name):
    name = name.lower().strip()

    url = WEBSITES.get(name)

    if not url:
        return None

    try:
        webbrowser.open(url)

        return {
            "name": name,
            "url": url
        }

    except Exception as e:
        print(
            "[BROWSER ERROR]",
            repr(e)
        )

        return None


def google_search(query):
    query = query.strip()

    if not query:
        return None

    url = (
        "https://www.google.com/search?q="
        + urllib.parse.quote(query)
    )

    try:
        webbrowser.open(url)

        return {
            "name": query,
            "url": url
        }

    except Exception as e:
        print(
            "[SEARCH ERROR]",
            repr(e)
        )

        return None