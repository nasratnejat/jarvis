import atexit
import queue
import threading
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright


class BrowserAgent:

    def __init__(self):
        self._commands = queue.Queue()
        self._ready = threading.Event()
        self._shutdown_requested = False

        self._worker = threading.Thread(
            target=self._worker_loop,
            name="jarvis-browser-worker",
            daemon=True,
        )

        self._worker.start()

        if not self._ready.wait(timeout=15):
            raise RuntimeError(
                "The controlled browser worker could not start."
            )

        atexit.register(self.shutdown)

    # ---------------------------------------------------------
    # PUBLIC API
    # ---------------------------------------------------------

    def open(self, url):
        return self._call(
            "open",
            url=url,
        )

    def observe(self):
        return self._call(
            "observe",
        )

    def click(self, index):
        return self._call(
            "click",
            index=index,
        )

    def back(self):
        return self._call(
            "back",
        )

    def close(self):
        return self._call(
            "close",
        )

    def shutdown(self):
        if self._shutdown_requested:
            return

        self._shutdown_requested = True

        try:
            self._commands.put({
                "action": "shutdown",
            })

            if (
                threading.current_thread()
                is not self._worker
            ):
                self._worker.join(timeout=5)

        except Exception:
            pass

    # ---------------------------------------------------------
    # WORKER COMMUNICATION
    # ---------------------------------------------------------

    def _call(self, action, **kwargs):
        if self._shutdown_requested:
            return {
                "ok": False,
                "error": (
                    "The controlled browser worker "
                    "has stopped."
                ),
            }

        response_queue = queue.Queue(maxsize=1)

        self._commands.put({
            "action": action,
            "kwargs": kwargs,
            "response": response_queue,
        })

        try:
            return response_queue.get(timeout=60)

        except queue.Empty:
            return {
                "ok": False,
                "error": (
                    "The controlled browser operation "
                    "timed out."
                ),
            }

    # ---------------------------------------------------------
    # WORKER
    # ---------------------------------------------------------

    def _worker_loop(self):
        playwright = None
        browser = None
        context = None
        page = None

        self._ready.set()

        try:
            playwright = sync_playwright().start()

            while True:
                command = self._commands.get()

                action = command.get("action")
                kwargs = command.get("kwargs", {})
                response_queue = command.get("response")

                if action == "shutdown":
                    break

                try:
                    if action == "open":
                        result = self._open_on_worker(
                            kwargs.get("url"),
                            playwright,
                            browser,
                            context,
                            page,
                        )

                        browser = result.get(
                            "_browser"
                        )

                        context = result.get(
                            "_context"
                        )

                        page = result.get(
                            "_page"
                        )

                        result.pop("_browser", None)
                        result.pop("_context", None)
                        result.pop("_page", None)

                    elif action == "observe":
                        result = self._observe_on_worker(
                            page
                        )

                    elif action == "click":
                        result = self._click_on_worker(
                            page,
                            kwargs.get("index"),
                        )

                    elif action == "back":
                        result = self._back_on_worker(
                            page
                        )

                    elif action == "close":
                        browser, context, page = (
                            self._close_session(
                                browser,
                                context,
                                page,
                            )
                        )

                        result = {
                            "ok": True,
                        }

                    else:
                        result = {
                            "ok": False,
                            "error": (
                                f"Unknown browser "
                                f"operation: {action}"
                            ),
                        }

                except Exception as e:
                    print(
                        "[BROWSER WORKER ERROR]",
                        repr(e),
                    )

                    result = {
                        "ok": False,
                        "error": str(e),
                    }

                if response_queue is not None:
                    try:
                        response_queue.put(
                            result,
                            timeout=5,
                        )
                    except queue.Full:
                        pass

        except Exception as e:
            print(
                "[BROWSER WORKER FATAL]",
                repr(e),
            )

        finally:
            try:
                if page:
                    page.close()
            except Exception:
                pass

            try:
                if context:
                    context.close()
            except Exception:
                pass

            try:
                if browser:
                    browser.close()
            except Exception:
                pass

            try:
                if playwright:
                    playwright.stop()
            except Exception:
                pass

    # ---------------------------------------------------------
    # SESSION MANAGEMENT
    # ---------------------------------------------------------

    def _create_browser_session(
        self,
        playwright,
    ):
        browser = playwright.chromium.launch(
            headless=False,
        )

        context = browser.new_context(
            viewport={
                "width": 1440,
                "height": 900,
            },
        )

        page = context.new_page()

        return browser, context, page

    def _ensure_page(
        self,
        playwright,
        browser,
        context,
        page,
    ):
        if (
            browser is None
            or context is None
            or page is None
            or page.is_closed()
        ):
            (
                browser,
                context,
                page,
            ) = self._create_browser_session(
                playwright
            )

        return browser, context, page

    def _close_session(
        self,
        browser,
        context,
        page,
    ):
        try:
            if page:
                page.close()
        except Exception:
            pass

        try:
            if context:
                context.close()
        except Exception:
            pass

        try:
            if browser:
                browser.close()
        except Exception:
            pass

        # IMPORTANT:
        # Do not kill the worker.
        # A later browser_open can create a
        # completely new browser session.
        return None, None, None

    # ---------------------------------------------------------
    # OPEN
    # ---------------------------------------------------------

    def _open_on_worker(
        self,
        url,
        playwright,
        browser,
        context,
        page,
    ):
        if not url:
            return {
                "ok": False,
                "error": "No URL was supplied.",
            }

        url = str(url).strip()

        if not url:
            return {
                "ok": False,
                "error": "No URL was supplied.",
            }

        if not (
            url.startswith("http://")
            or url.startswith("https://")
        ):
            url = "https://" + url

        (
            browser,
            context,
            page,
        ) = self._ensure_page(
            playwright,
            browser,
            context,
            page,
        )

        print(
            "[BROWSER] Opening:",
            url,
        )

        try:
            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30000,
            )

            try:
                page.wait_for_load_state(
                    "networkidle",
                    timeout=5000,
                )
            except Exception:
                pass

            result = self._observe_on_worker(page)

            result["_browser"] = browser
            result["_context"] = context
            result["_page"] = page

            return result

        except Exception as e:
            print(
                "[BROWSER OPEN ERROR]",
                repr(e),
            )

            return {
                "ok": False,
                "error": str(e),
                "_browser": browser,
                "_context": context,
                "_page": page,
            }

    # ---------------------------------------------------------
    # OBSERVE
    # ---------------------------------------------------------

    def _observe_on_worker(self, page):
        if page is None:
            return {
                "ok": False,
                "error": (
                    "No controlled browser page "
                    "is currently open."
                ),
            }

        if page.is_closed():
            return {
                "ok": False,
                "error": (
                    "The controlled browser page "
                    "is closed."
                ),
            }

        try:
            title = page.title()
        except Exception:
            title = ""

        try:
            url = page.url
        except Exception:
            url = ""

        parsed = urlparse(url)

        domain = parsed.netloc

        try:
            text = page.locator("body").inner_text(
                timeout=5000
            )
        except Exception:
            text = ""

        text = text.strip()

        # Keep browser observations bounded.
        text = text[:12000]

        links = []

        try:
            elements = page.locator("a").all()

            for index, element in enumerate(
                elements[:50]
            ):
                try:
                    label = element.inner_text(
                        timeout=1000
                    ).strip()

                    href = element.get_attribute(
                        "href"
                    )

                    if not href:
                        continue

                    if not label:
                        label = href

                    links.append({
                        "index": len(links),
                        "text": label[:200],
                        "href": href[:1000],
                    })

                    if len(links) >= 30:
                        break

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

    # ---------------------------------------------------------
    # CLICK
    # ---------------------------------------------------------

    def _click_on_worker(
        self,
        page,
        index,
    ):
        if page is None:
            return {
                "ok": False,
                "error": (
                    "No controlled browser page "
                    "is currently open."
                ),
            }

        if page.is_closed():
            return {
                "ok": False,
                "error": (
                    "The controlled browser page "
                    "is closed."
                ),
            }

        try:
            index = int(index)
        except (TypeError, ValueError):
            return {
                "ok": False,
                "error": "The browser link index was invalid.",
            }

        try:
            elements = page.locator("a").all()

            if index < 0 or index >= len(elements):
                return {
                    "ok": False,
                    "error": (
                        f"No link exists at index {index}."
                    ),
                }

            element = elements[index]

            try:
                label = element.inner_text(
                    timeout=1000
                ).strip()
            except Exception:
                label = ""

            try:
                href = element.get_attribute(
                    "href"
                )
            except Exception:
                href = ""

            print(
                "[BROWSER] Clicking:",
                index,
                label,
                href,
            )

            before_url = page.url

            try:
                element.scroll_into_view_if_needed(
                    timeout=2000
                )
            except Exception:
                pass

            try:
                element.click(
                    timeout=10000
                )
            except Exception:
                # Some pages navigate through JS and
                # can be more reliable through force.
                element.click(
                    timeout=10000,
                    force=True,
                )

            try:
                page.wait_for_load_state(
                    "domcontentloaded",
                    timeout=10000,
                )
            except Exception:
                pass

            try:
                page.wait_for_load_state(
                    "networkidle",
                    timeout=5000,
                )
            except Exception:
                pass

            after_url = page.url

            observation = self._observe_on_worker(
                page
            )

            if not observation.get("ok"):
                return observation

            return {
                "ok": True,
                "clicked_index": index,
                "clicked_text": label,
                "clicked_href": href or "",
                "previous_url": before_url,
                "url_changed": (
                    before_url != after_url
                ),
                "title": observation.get(
                    "title",
                    "",
                ),
                "url": observation.get(
                    "url",
                    "",
                ),
                "domain": observation.get(
                    "domain",
                    "",
                ),
                "text": observation.get(
                    "text",
                    "",
                ),
                "links": observation.get(
                    "links",
                    [],
                ),
            }

        except Exception as e:
            print(
                "[BROWSER CLICK ERROR]",
                repr(e),
            )

            return {
                "ok": False,
                "error": str(e),
            }

    # ---------------------------------------------------------
    # BACK
    # ---------------------------------------------------------

    def _back_on_worker(self, page):
        if page is None:
            return {
                "ok": False,
                "error": (
                    "No controlled browser page "
                    "is currently open."
                ),
            }

        if page.is_closed():
            return {
                "ok": False,
                "error": (
                    "The controlled browser page "
                    "is closed."
                ),
            }

        try:
            before_url = page.url

            page.go_back(
                wait_until="domcontentloaded",
                timeout=15000,
            )

            try:
                page.wait_for_load_state(
                    "networkidle",
                    timeout=5000,
                )
            except Exception:
                pass

            observation = self._observe_on_worker(
                page
            )

            if not observation.get("ok"):
                return observation

            return {
                "ok": True,
                "previous_url": before_url,
                "title": observation.get(
                    "title",
                    "",
                ),
                "url": observation.get(
                    "url",
                    "",
                ),
                "domain": observation.get(
                    "domain",
                    "",
                ),
                "text": observation.get(
                    "text",
                    "",
                ),
                "links": observation.get(
                    "links",
                    [],
                ),
            }

        except Exception as e:
            print(
                "[BROWSER BACK ERROR]",
                repr(e),
            )

            return {
                "ok": False,
                "error": str(e),
            }


browser_agent = BrowserAgent()