import atexit
import os
import queue
import threading
from urllib.parse import urlparse, quote_plus

from playwright.sync_api import sync_playwright


# ============================================================
# WEBSITE REGISTRY
# ============================================================

WEBSITES = {
    "google": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "wikipedia": "https://www.wikipedia.org",
    "github": "https://github.com",
    "reddit": "https://www.reddit.com",
    "amazon": "https://www.amazon.com",
    "facebook": "https://www.facebook.com",
    "instagram": "https://www.instagram.com",
    "twitter": "https://twitter.com",
    "x": "https://x.com",
    "linkedin": "https://www.linkedin.com",
    "discord": "https://discord.com",
    "twitch": "https://www.twitch.tv",
    "spotify": "https://open.spotify.com",
    "netflix": "https://www.netflix.com",
    "chatgpt": "https://chatgpt.com",
    "openai": "https://openai.com",
    "nvidia": "https://www.nvidia.com",
    "intel": "https://www.intel.com",
    "amd": "https://www.amd.com",
    "apple": "https://www.apple.com",
    "microsoft": "https://www.microsoft.com",
    "windows": "https://www.microsoft.com/windows",
    "stackoverflow": "https://stackoverflow.com",
    "stack overflow": "https://stackoverflow.com",
    "python": "https://www.python.org",
    "pypi": "https://pypi.org",
    "docker": "https://www.docker.com",
    "huggingface": "https://huggingface.co",
    "hugging face": "https://huggingface.co",
    "w3schools": "https://www.w3schools.com",
}


WEBSITE_ALIASES = {
    "wiki": "wikipedia",
    "wiki pedia": "wikipedia",
    "chat gpt": "chatgpt",
    "hugging face": "huggingface",
    "stack overflow": "stackoverflow",
}


# ============================================================
# WEBSITE RESOLUTION
# ============================================================

def _clean_site_name(site):

    if not isinstance(
        site,
        str,
    ):
        return ""

    site = site.strip().lower()

    site = (
        site
        .replace("https://", "")
        .replace("http://", "")
        .strip("/")
        .strip()
    )

    return site


def resolve_website(site):

    site = _clean_site_name(
        site
    )

    if not site:
        return None

    site = WEBSITE_ALIASES.get(
        site,
        site,
    )

    if site in WEBSITES:
        return WEBSITES[site]

    if "." in site:

        if (
            not site.startswith(
                "http://"
            )
            and not site.startswith(
                "https://"
            )
        ):
            return "https://" + site

    return None


# ============================================================
# BROWSER AGENT
# ============================================================

class BrowserAgent:

    def __init__(self):

        self._commands = queue.Queue()

        self._ready = threading.Event()

        self._shutdown_requested = False

        self._last_link_map = []

        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

        self._worker = threading.Thread(
            target=self._worker_loop,
            name="jarvis-browser-worker",
            daemon=True,
        )

        print(
            "[BROWSER] Starting Playwright worker..."
        )

        self._worker.start()

        if not self._ready.wait(
            timeout=15
        ):

            raise RuntimeError(
                "JARVIS browser worker failed "
                "to initialize."
            )

        print(
            "[BROWSER] Playwright worker ready."
        )

        print(
            "[BROWSER] BrowserAgent ID:",
            id(self),
            "PID:",
            os.getpid(),
        )

        atexit.register(
            self.shutdown
        )

    # ========================================================
    # PUBLIC API
    # ========================================================

    def open(self, url):

        print(
            "[BROWSER] open()",
            "Agent:",
            id(self),
            "PID:",
            os.getpid(),
            "Thread:",
            threading.get_ident(),
        )

        return self._call(
            "open",
            url=url,
        )

    def observe(self):

        print(
            "[BROWSER] observe()",
            "Agent:",
            id(self),
            "PID:",
            os.getpid(),
            "Thread:",
            threading.get_ident(),
        )

        return self._call(
            "observe",
        )

    def click(self, index):

        print(
            "[BROWSER] click()",
            "Agent:",
            id(self),
            "PID:",
            os.getpid(),
            "Thread:",
            threading.get_ident(),
        )

        return self._call(
            "click",
            index=index,
        )

    def back(self):

        print(
            "[BROWSER] back()",
            "Agent:",
            id(self),
            "PID:",
            os.getpid(),
            "Thread:",
            threading.get_ident(),
        )

        return self._call(
            "back",
        )

    def forward(self):

        print(
            "[BROWSER] forward()",
            "Agent:",
            id(self),
            "PID:",
            os.getpid(),
            "Thread:",
            threading.get_ident(),
        )

        return self._call(
            "forward",
        )

    def close(self):

        print(
            "[BROWSER] close()",
            "Agent:",
            id(self),
            "PID:",
            os.getpid(),
            "Thread:",
            threading.get_ident(),
        )

        return self._call(
            "close",
        )

    def status(self):

        return self._call(
            "status",
        )

    def shutdown(self):

        if self._shutdown_requested:
            return

        self._shutdown_requested = True

        try:

            self._commands.put({
                "action": "shutdown",
            })

        except Exception:
            pass

    # ========================================================
    # QUEUE
    # ========================================================

    def _call(
        self,
        action,
        **kwargs,
    ):

        if self._shutdown_requested:

            return {
                "ok": False,
                "error": (
                    "Browser worker is shutting down."
                ),
            }

        response_queue = queue.Queue(
            maxsize=1
        )

        request = {
            "action": action,
            "response_queue": response_queue,
            **kwargs,
        }

        self._commands.put(
            request
        )

        try:

            return response_queue.get(
                timeout=60
            )

        except queue.Empty:

            return {
                "ok": False,
                "error": (
                    "Browser operation timed out, Sir."
                ),
            }

    # ========================================================
    # WORKER
    # ========================================================

    def _worker_loop(self):

        try:

            self._playwright = (
                sync_playwright().start()
            )

            self._ready.set()

            print(
                "[BROWSER] Worker Playwright "
                "initialized.",
                "Agent:",
                id(self),
                "PID:",
                os.getpid(),
                "Worker thread:",
                threading.get_ident(),
            )

            while True:

                request = (
                    self._commands.get()
                )

                action = request.get(
                    "action"
                )

                response_queue = (
                    request.get(
                        "response_queue"
                    )
                )

                try:

                    if action == "open":

                        result = (
                            self._open_on_worker(
                                request.get(
                                    "url"
                                )
                            )
                        )

                    elif action == "observe":

                        result = (
                            self._observe_on_worker()
                        )

                    elif action == "click":

                        result = (
                            self._click_on_worker(
                                request.get(
                                    "index"
                                )
                            )
                        )

                    elif action == "back":

                        result = (
                            self._back_on_worker()
                        )

                    elif action == "forward":

                        result = (
                            self._forward_on_worker()
                        )

                    elif action == "close":

                        result = (
                            self._close_on_worker()
                        )

                    elif action == "status":

                        result = (
                            self._status_on_worker()
                        )

                    elif action == "shutdown":

                        result = {
                            "ok": True
                        }

                        if response_queue:

                            response_queue.put(
                                result
                            )

                        break

                    else:

                        result = {
                            "ok": False,
                            "error": (
                                "Unknown browser "
                                "operation."
                            ),
                        }

                    if response_queue:

                        response_queue.put(
                            result
                        )

                except Exception as e:

                    print(
                        "[BROWSER WORKER ERROR]",
                        repr(e),
                    )

                    result = {
                        "ok": False,
                        "error": str(e),
                    }

                    if response_queue:

                        response_queue.put(
                            result
                        )

        except Exception as e:

            print(
                "[BROWSER WORKER START ERROR]",
                repr(e),
            )

            self._ready.set()

        finally:

            try:

                if self._page:
                    self._page.close()

            except Exception:
                pass

            try:

                if self._context:
                    self._context.close()

            except Exception:
                pass

            try:

                if self._browser:
                    self._browser.close()

            except Exception:
                pass

            try:

                if self._playwright:
                    self._playwright.stop()

            except Exception:
                pass

            self._page = None
            self._context = None
            self._browser = None
            self._playwright = None

            print(
                "[BROWSER] Worker stopped."
            )

    # ========================================================
    # SESSION
    # ========================================================

    def _create_browser_session(self):

        if not self._playwright:
            return False

        print(
            "[BROWSER] Creating controlled "
            "Chromium session..."
        )

        self._browser = (
            self._playwright.chromium.launch(
                headless=False
            )
        )

        self._context = (
            self._browser.new_context(
                viewport={
                    "width": 1440,
                    "height": 900,
                }
            )
        )

        self._page = (
            self._context.new_page()
        )

        self._last_link_map = []

        print(
            "[BROWSER] Controlled page created.",
            "Page:",
            id(self._page),
        )

        return True

    def _ensure_page(self):

        if (
            self._page is None
            or self._page.is_closed()
        ):

            print(
                "[BROWSER] No active page. "
                "Creating one..."
            )

            return self._create_browser_session()

        return True

    def _close_session(self):

        print(
            "[BROWSER] Closing controlled "
            "browser session."
        )

        try:

            if self._page:
                self._page.close()

        except Exception:
            pass

        try:

            if self._context:
                self._context.close()

        except Exception:
            pass

        try:

            if self._browser:
                self._browser.close()

        except Exception:
            pass

        self._page = None
        self._context = None
        self._browser = None
        self._last_link_map = []

    # ========================================================
    # OPEN
    # ========================================================

    def _open_on_worker(
        self,
        url,
    ):

        if not self._ensure_page():

            return {
                "ok": False,
                "error": (
                    "Could not create "
                    "controlled browser page."
                ),
            }

        print(
            "[BROWSER] Opening:",
            url,
            "Page:",
            id(self._page),
        )

        self._page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=30000,
        )

        try:

            self._page.wait_for_load_state(
                "networkidle",
                timeout=5000,
            )

        except Exception:
            pass

        return self._observe_on_worker()

    # ========================================================
    # OBSERVE
    # ========================================================

    def _observe_on_worker(self):

        if (
            self._page is None
            or self._page.is_closed()
        ):

            print(
                "[BROWSER] OBSERVE FAILED:",
                "page is None or closed.",
                "Agent:",
                id(self),
                "PID:",
                os.getpid(),
            )

            return {
                "ok": False,
                "error": (
                    "No controlled browser "
                    "page is currently open."
                ),
            }

        print(
            "[BROWSER] Observing page:",
            id(self._page),
            "URL:",
            self._page.url,
        )

        title = self._page.title()

        url = self._page.url

        parsed = urlparse(url)

        domain = (
            parsed.netloc
            or parsed.path
        )

        try:

            body = self._page.locator(
                "body"
            )

            text = body.inner_text(
                timeout=5000
            )

        except Exception:

            text = ""

        # Keep enough data for the application layer.
        # The AI-facing formatter in app/ai/tools.py
        # performs the actual token reduction.
        text = text[:12000]

        links = []

        self._last_link_map = []

        try:

            anchors = self._page.locator(
                "a"
            )

            count = min(
                anchors.count(),
                1000,
            )

            visible_index = 0

            for raw_index in range(count):

                try:

                    anchor = anchors.nth(
                        raw_index
                    )

                    if not anchor.is_visible():
                        continue

                    link_text = (
                        anchor.inner_text(
                            timeout=1000
                        )
                        .strip()
                    )

                    href = (
                        anchor.get_attribute(
                            "href"
                        )
                    )

                    if not href:
                        continue

                    if not link_text:
                        continue

                    if len(links) >= 30:
                        break

                    links.append({
                        "index": visible_index,
                        "text": link_text[:300],
                        "href": href,
                    })

                    self._last_link_map.append(
                        raw_index
                    )

                    visible_index += 1

                except Exception:
                    continue

        except Exception:
            pass

        return {
            "ok": True,
            "title": title,
            "url": url,
            "domain": domain,
            "text": text,
            "links": links,
        }

    # ========================================================
    # CLICK
    # ========================================================

    def _click_on_worker(
        self,
        index,
    ):

        if (
            self._page is None
            or self._page.is_closed()
        ):

            return {
                "ok": False,
                "error": (
                    "No controlled browser "
                    "page is currently open."
                ),
            }

        try:

            index = int(index)

        except Exception:

            return {
                "ok": False,
                "error": (
                    "Invalid browser link index."
                ),
            }

        if (
            index < 0
            or index >= len(
                self._last_link_map
            )
        ):

            return {
                "ok": False,
                "error": (
                    "That link index is not "
                    "available in the current "
                    "browser observation."
                ),
            }

        raw_index = (
            self._last_link_map[index]
        )

        print(
            "[BROWSER] Clicking visible index:",
            index,
            "DOM index:",
            raw_index,
        )

        try:

            anchor = (
                self._page.locator(
                    "a"
                ).nth(
                    raw_index
                )
            )

            anchor.scroll_into_view_if_needed()

            anchor.click(
                timeout=10000
            )

            try:

                self._page.wait_for_load_state(
                    "domcontentloaded",
                    timeout=10000,
                )

            except Exception:
                pass

            result = self._observe_on_worker()

            result["clicked_index"] = index

            result["clicked_text"] = (
                anchor.inner_text(
                    timeout=1000
                ).strip()
            )

            result["clicked_href"] = (
                anchor.get_attribute(
                    "href"
                )
                or ""
            )

            return result

        except Exception as e:

            print(
                "[BROWSER CLICK ERROR]",
                repr(e),
            )

            return {
                "ok": False,
                "error": (
                    f"Could not click that link: {e}"
                ),
            }

    # ========================================================
    # BACK
    # ========================================================

    def _back_on_worker(self):

        if (
            self._page is None
            or self._page.is_closed()
        ):

            return {
                "ok": False,
                "error": (
                    "No controlled browser "
                    "page is currently open."
                ),
            }

        try:

            result = self._page.go_back(
                wait_until="domcontentloaded",
                timeout=15000,
            )

            if result is None:

                return {
                    "ok": False,
                    "error": (
                        "There is no previous "
                        "page in browser history."
                    ),
                }

            return self._observe_on_worker()

        except Exception as e:

            print(
                "[BROWSER BACK ERROR]",
                repr(e),
            )

            return {
                "ok": False,
                "error": (
                    f"Could not go back: {e}"
                ),
            }

    # ========================================================
    # FORWARD
    # ========================================================

    def _forward_on_worker(self):

        if (
            self._page is None
            or self._page.is_closed()
        ):

            return {
                "ok": False,
                "error": (
                    "No controlled browser "
                    "page is currently open."
                ),
            }

        try:

            result = self._page.go_forward(
                wait_until="domcontentloaded",
                timeout=15000,
            )

            if result is None:

                return {
                    "ok": False,
                    "error": (
                        "There is no next "
                        "page in browser history."
                    ),
                }

            return self._observe_on_worker()

        except Exception as e:

            print(
                "[BROWSER FORWARD ERROR]",
                repr(e),
            )

            return {
                "ok": False,
                "error": (
                    f"Could not go forward: {e}"
                ),
            }

    # ========================================================
    # STATUS
    # ========================================================

    def _status_on_worker(self):

        page_open = (
            self._page is not None
            and not self._page.is_closed()
        )

        return {
            "ok": True,
            "agent_id": id(self),
            "pid": os.getpid(),
            "worker_thread": (
                threading.get_ident()
            ),
            "page_open": page_open,
            "page_id": (
                id(self._page)
                if self._page
                else None
            ),
            "url": (
                self._page.url
                if page_open
                else None
            ),
        }

    # ========================================================
    # CLOSE
    # ========================================================

    def _close_on_worker(self):

        self._close_session()

        return {
            "ok": True,
            "message": (
                "Controlled browser closed."
            ),
        }


# ============================================================
# SINGLE BROWSER INSTANCE
# ============================================================

browser_agent = BrowserAgent()


# ============================================================
# PUBLIC HELPERS
# ============================================================

def open_website(site):

    print(
        "[TOOL BROWSER] open_website()",
        "Agent:",
        id(browser_agent),
        "PID:",
        os.getpid(),
    )

    url = resolve_website(site)

    if not url:

        return (
            "I couldn't identify that website, Sir."
        )

    print(
        f"[TOOL] open_website "
        f"{site!r} -> {url}"
    )

    result = browser_agent.open(
        url
    )

    if not result.get("ok"):

        return (
            "I could not open that website, Sir. "
            + result.get(
                "error",
                "Unknown browser error.",
            )
        )

    title = result.get(
        "title",
        "the website",
    )

    return (
        f"Opened {title}, Sir."
    )


def google_search(query):

    if not query:

        return (
            "Please provide something to search for, Sir."
        )

    query = query.strip()

    url = (
        "https://www.google.com/search?q="
        + quote_plus(query)
    )

    print(
        "[TOOL BROWSER] google_search()",
        "Agent:",
        id(browser_agent),
        "PID:",
        os.getpid(),
    )

    result = browser_agent.open(
        url
    )

    if not result.get("ok"):

        return (
            "I could not perform the Google search, Sir. "
            + result.get(
                "error",
                "Unknown browser error.",
            )
        )

    return (
        "I searched Google for "
        f"{query}, Sir."
    )