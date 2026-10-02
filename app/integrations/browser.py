import atexit
import os
import queue
import re
import threading

from urllib.parse import (
    quote_plus,
    urlparse,
)

from playwright.sync_api import (
    sync_playwright,
)


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

def _clean_site_name(
    site,
):

    if not isinstance(
        site,
        str,
    ):
        return ""

    site = site.strip().lower()

    site = (
        site
        .replace(
            "https://",
            "",
        )
        .replace(
            "http://",
            "",
        )
        .strip("/")
        .strip()
    )

    return site


def resolve_website(
    site,
):

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

        if not site.startswith(
            "http://"
        ) and not site.startswith(
            "https://"
        ):

            return (
                "https://"
                + site
            )

    return None


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def _normalize_click_text(
    value,
):

    value = str(
        value or ""
    ).strip().lower()

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    value = re.sub(
        r"[^\w\s.-]",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


# ============================================================
# BROWSER AGENT
# ============================================================

class BrowserAgent:

    def __init__(self):

        self._commands = queue.Queue()

        self._ready = threading.Event()

        self._shutdown_requested = False

        # Maps observation indexes to DOM action IDs.
        self._last_action_map = []

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

    def open(
        self,
        url,
    ):

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
            "observe"
        )

    def click(
        self,
        index=None,
        target=None,
    ):

        print(
            "[BROWSER] click()",
            "Agent:",
            id(self),
            "PID:",
            os.getpid(),
            "Thread:",
            threading.get_ident(),
            "index:",
            index,
            "target:",
            target,
        )

        return self._call(
            "click",
            index=index,
            target=target,
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
            "back"
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
            "forward"
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
            "close"
        )

    def status(self):

        return self._call(
            "status"
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
                                ),
                                request.get(
                                    "target"
                                ),
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

    def _create_browser_session(
        self,
    ):

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

        self._last_action_map = []

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
        self._last_action_map = []

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
    # PAGE EXTRACTION
    # ========================================================

    def _extract_page_structure(
        self,
    ):

        if not self._page:
            return {
                "headings": [],
                "description": "",
                "actions": [],
            }

        script = """
        () => {
            const visible = (el) => {
                if (!el) return false;

                const style = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();

                if (style.display === "none") return false;
                if (style.visibility === "hidden") return false;
                if (parseFloat(style.opacity || "1") === 0) return false;

                return (
                    rect.width > 0 &&
                    rect.height > 0
                );
            };

            const clean = (value) =>
                String(value || "")
                    .replace(/\\s+/g, " ")
                    .trim();

            const headings = Array.from(
                document.querySelectorAll(
                    "h1, h2, h3"
                )
            )
                .filter(visible)
                .map((el) =>
                    clean(el.innerText || el.textContent)
                )
                .filter(Boolean)
                .slice(0, 20);

            const description =
                document.querySelector(
                    'meta[name="description"]'
                )?.content || "";

            const nodes = Array.from(
                document.querySelectorAll(
                    [
                        "a",
                        "button",
                        '[role="button"]',
                        "summary",
                        'input[type="button"]',
                        'input[type="submit"]'
                    ].join(",")
                )
            );

            const actions = [];

            for (const el of nodes) {
                if (!visible(el)) continue;

                const disabled =
                    el.disabled === true ||
                    el.getAttribute("aria-disabled") === "true";

                if (disabled) continue;

                const text = clean(
                    el.innerText ||
                    el.value ||
                    el.getAttribute("aria-label") ||
                    el.getAttribute("title") ||
                    ""
                );

                const aria =
                    clean(
                        el.getAttribute(
                            "aria-label"
                        ) || ""
                    );

                const title =
                    clean(
                        el.getAttribute(
                            "title"
                        ) || ""
                    );

                const href =
                    el.tagName.toLowerCase() === "a"
                        ? (
                            el.getAttribute("href") ||
                            ""
                        )
                        : "";

                if (!text && !aria && !title) {
                    continue;
                }

                const id =
                    actions.length;

                el.setAttribute(
                    "data-jarvis-action-id",
                    String(id)
                );

                actions.push({
                    id,
                    text: text.slice(0, 300),
                    aria_label: aria.slice(0, 200),
                    title: title.slice(0, 200),
                    href,
                    kind:
                        el.tagName.toLowerCase() === "a"
                            ? "link"
                            : "button"
                });

                if (actions.length >= 60) {
                    break;
                }
            }

            return {
                headings,
                description: clean(description).slice(0, 500),
                actions
            };
        }
        """

        try:

            return (
                self._page.evaluate(
                    script
                )
                or {
                    "headings": [],
                    "description": "",
                    "actions": [],
                }
            )

        except Exception as e:

            print(
                "[BROWSER] Structure extraction error:",
                repr(e),
            )

            return {
                "headings": [],
                "description": "",
                "actions": [],
            }

    # ========================================================
    # OBSERVE
    # ========================================================

    def _observe_on_worker(
        self,
    ):

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

        parsed = urlparse(
            url
        )

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

        text = text[:12000]

        structure = (
            self._extract_page_structure()
        )

        actions = structure.get(
            "actions",
            [],
        )

        # Rebuild index map.
        self._last_action_map = [
            item.get(
                "id"
            )
            for item in actions
            if isinstance(
                item,
                dict,
            )
        ]

        # Expose action data under the historic
        # "links" field for compatibility with
        # app/ai/tools.py.
        links = []

        for action in actions:

            if not isinstance(
                action,
                dict,
            ):
                continue

            links.append({
                "index": action.get(
                    "id"
                ),
                "text": action.get(
                    "text",
                    "",
                ),
                "href": action.get(
                    "href",
                    "",
                ),
                "aria_label": action.get(
                    "aria_label",
                    "",
                ),
                "title": action.get(
                    "title",
                    "",
                ),
                "kind": action.get(
                    "kind",
                    "link",
                ),
            })

        return {
            "ok": True,
            "title": title,
            "url": url,
            "domain": domain,
            "description": structure.get(
                "description",
                "",
            ),
            "headings": structure.get(
                "headings",
                [],
            ),
            "text": text,
            "links": links,
        }

    # ========================================================
    # ACTION SAFETY
    # ========================================================

    @staticmethod
    def _is_consequential_target(
        target,
    ):
        """
        Block obviously consequential actions from
        semantic clicking.

        Navigation such as "Buy" is allowed.
        Actual purchase/commit actions are not.
        """

        normalized = _normalize_click_text(
            target
        )

        dangerous_phrases = (
            "place order",
            "submit order",
            "confirm purchase",
            "confirm order",
            "pay now",
            "make payment",
            "delete account",
            "delete permanently",
            "remove account",
            "cancel subscription",
            "sign out all",
        )

        return any(
            phrase in normalized
            for phrase in dangerous_phrases
        )

    # ========================================================
    # ACTION MATCHING
    # ========================================================

    def _find_action_by_target(
        self,
        target,
    ):

        if (
            self._page is None
            or self._page.is_closed()
        ):
            return None

        target_normalized = (
            _normalize_click_text(
                target
            )
        )

        if not target_normalized:
            return None

        try:

            structure = (
                self._extract_page_structure()
            )

            actions = structure.get(
                "actions",
                [],
            )

        except Exception:

            actions = []

        best = None
        best_score = 0

        target_tokens = set(
            target_normalized.split()
        )

        for action in actions:

            if not isinstance(
                action,
                dict,
            ):
                continue

            fields = [
                action.get(
                    "text",
                    "",
                ),
                action.get(
                    "aria_label",
                    "",
                ),
                action.get(
                    "title",
                    "",
                ),
            ]

            combined = " ".join(
                str(field or "")
                for field in fields
            )

            normalized = (
                _normalize_click_text(
                    combined
                )
            )

            if not normalized:
                continue

            score = 0

            if (
                normalized
                == target_normalized
            ):
                score += 100

            if (
                target_normalized
                in normalized
            ):
                score += 60

            if (
                normalized
                in target_normalized
            ):
                score += 35

            tokens = set(
                normalized.split()
            )

            overlap = len(
                target_tokens
                & tokens
            )

            score += (
                overlap * 15
            )

            if normalized.startswith(
                target_normalized
            ):
                score += 20

            if target_normalized.startswith(
                normalized
            ):
                score += 10

            if score > best_score:

                best_score = score

                best = action

        return best

    # ========================================================
    # CLICK
    # ========================================================

    def _click_on_worker(
        self,
        index=None,
        target=None,
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

        chosen_index = None
        chosen_target = None

        # ----------------------------------------------------
        # Semantic target.
        # ----------------------------------------------------

        if (
            target is not None
            and str(target).strip()
        ):

            target = str(
                target
            ).strip()

            if self._is_consequential_target(
                target
            ):

                return {
                    "ok": False,
                    "error": (
                        "That action appears "
                        "consequential and requires "
                        "confirmation before clicking."
                    ),
                }

            action = (
                self._find_action_by_target(
                    target
                )
            )

            if not action:

                return {
                    "ok": False,
                    "error": (
                        f"I could not find a visible "
                        f"clickable element matching "
                        f"'{target}'."
                    ),
                }

            chosen_index = action.get(
                "id"
            )

            chosen_target = target

            print(
                "[BROWSER] Semantic click matched:",
                target,
                "->",
                action,
            )

        # ----------------------------------------------------
        # Numeric index.
        # ----------------------------------------------------

        else:

            try:
                chosen_index = int(
                    index
                )
            except (
                TypeError,
                ValueError,
            ):

                return {
                    "ok": False,
                    "error": (
                        "Invalid browser action index."
                    ),
                }

        if (
            chosen_index is None
        ):

            return {
                "ok": False,
                "error": (
                    "No browser action was selected."
                ),
            }

        try:

            selector = (
                '[data-jarvis-action-id="'
                f'{chosen_index}'
                '"]'
            )

            element = self._page.locator(
                selector
            ).first

            if not element.is_visible():

                return {
                    "ok": False,
                    "error": (
                        "That browser element is "
                        "no longer visible."
                    ),
                }

            clicked_text = (
                element.inner_text(
                    timeout=1000
                ).strip()
            )

            if not clicked_text:

                clicked_text = (
                    element.get_attribute(
                        "aria-label"
                    )
                    or element.get_attribute(
                        "title"
                    )
                    or ""
                ).strip()

            clicked_href = (
                element.get_attribute(
                    "href"
                )
                or ""
            )

            print(
                "[BROWSER] Clicking action:",
                chosen_index,
                clicked_text,
            )

            before_pages = (
                list(
                    self._context.pages
                )
                if self._context
                else []
            )

            element.scroll_into_view_if_needed()

            element.click(
                timeout=10000
            )

            # If the click opened a new tab/window,
            # continue with that page.
            if self._context:

                after_pages = list(
                    self._context.pages
                )

                if len(after_pages) > len(
                    before_pages
                ):

                    self._page = (
                        after_pages[-1]
                    )

            try:

                self._page.wait_for_load_state(
                    "domcontentloaded",
                    timeout=10000,
                )

            except Exception:
                pass

            try:

                self._page.wait_for_load_state(
                    "networkidle",
                    timeout=3000,
                )

            except Exception:
                pass

            result = (
                self._observe_on_worker()
            )

            result[
                "clicked_index"
            ] = chosen_index

            result[
                "clicked_text"
            ] = clicked_text

            result[
                "clicked_href"
            ] = clicked_href

            if chosen_target:
                result[
                    "clicked_target"
                ] = chosen_target

            return result

        except Exception as e:

            print(
                "[BROWSER CLICK ERROR]",
                repr(e),
            )

            return {
                "ok": False,
                "error": (
                    f"Could not click that "
                    f"browser element: {e}"
                ),
            }

    # ========================================================
    # BACK
    # ========================================================

    def _back_on_worker(
        self,
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

            result = (
                self._page.go_back(
                    wait_until="domcontentloaded",
                    timeout=15000,
                )
            )

            if result is None:

                return {
                    "ok": False,
                    "error": (
                        "There is no previous "
                        "page in browser history."
                    ),
                }

            return (
                self._observe_on_worker()
            )

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

    def _forward_on_worker(
        self,
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

            result = (
                self._page.go_forward(
                    wait_until="domcontentloaded",
                    timeout=15000,
                )
            )

            if result is None:

                return {
                    "ok": False,
                    "error": (
                        "There is no next "
                        "page in browser history."
                    ),
                }

            return (
                self._observe_on_worker()
            )

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

    def _status_on_worker(
        self,
    ):

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

    def _close_on_worker(
        self,
    ):

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
# PUBLIC WEBSITE HELPER
# ============================================================

def open_website(
    site,
):

    print(
        "[TOOL BROWSER] open_website()",
        "Agent:",
        id(browser_agent),
        "PID:",
        os.getpid(),
    )

    url = resolve_website(
        site
    )

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

    if not result.get(
        "ok"
    ):

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


# ============================================================
# GOOGLE SEARCH
# ============================================================

def google_search(
    query,
):

    if not query:

        return (
            "Please provide something "
            "to search for, Sir."
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

    if not result.get(
        "ok"
    ):

        return (
            "I could not perform the "
            "Google search, Sir. "
            + result.get(
                "error",
                "Unknown browser error.",
            )
        )

    return (
        "I searched Google for "
        f"{query}, Sir."
    )