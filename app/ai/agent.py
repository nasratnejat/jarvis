import json
import re

from app.ai.tools import (
    TOOLS,
    TOOL_FUNCTIONS,
)


class JarvisAgent:

    MAX_TOOL_ROUNDS = 5

    # Conversation history limits.
    MAX_CONTEXT_MESSAGES = 6
    MAX_CONTEXT_CHARS = 3500

    # Keep browser analysis compact.
    MAX_BROWSER_CONTEXT_CHARS = 1800

    # Tools where the tool result itself is enough.
    TERMINAL_TOOLS = {
        "get_weather",
        "open_website",
        "google_search",
        "search_product_price",
        "search_youtube",
        "play_youtube",
        "media_control",
        "browser_open",
        "browser_back",
        "browser_forward",
        "browser_close",
    }

    TOOL_INTENT_WORDS = {
        "open",
        "visit",
        "website",
        "browser",
        "page",
        "click",
        "search",
        "google",
        "look",
        "find",
        "price",
        "cost",
        "weather",
        "youtube",
        "video",
        "play",
        "watch",
        "listen",
        "pause",
        "resume",
        "stop",
        "mute",
        "unmute",
        "volume",
        "next",
        "previous",
        "back",
        "forward",
        "close",
        "exit",
    }

    BROWSER_CONTEXT_PATTERNS = (
        # Direct observation.
        r"\bwhat\s+do\s+you\s+see\b",
        r"\bwhat\s+can\s+you\s+see\b",
        r"\btell\s+me\s+what\s+you\s+see\b",
        r"\bwhat\s+are\s+you\s+seeing\b",
        r"\bwhat\s+is\s+on\s+(?:this|the)\s+(?:page|website|webpage)\b",
        r"\bwhat(?:'s|\s+is)\s+on\s+(?:this|the)\s+(?:page|website|webpage)\b",

        # Current page / browser references.
        r"\bcurrent\s+page\b",
        r"\bcurrent\s+website\b",
        r"\bcurrent\s+webpage\b",
        r"\bcurrent\s+browser\b",
        r"\bthis\s+page\b",
        r"\bthis\s+website\b",
        r"\bthis\s+webpage\b",

        # Inspect / analyse.
        r"\binspect\s+(?:this|the)\b",
        r"\banaly[sz]e\s+(?:this|the)\b",
        r"\banalyse\s+(?:this|the)\b",
        r"\blook\s+at\s+(?:this|the)\b",
        r"\blook\s+through\s+(?:this|the)\b",

        # Evaluative requests.
        r"\bshould\s+i\s+buy\s+(?:this|that)\b",
        r"\bshould\s+i\s+purchase\s+(?:this|that)\b",
        r"\bis\s+(?:this|that)\s+worth\s+buying\b",
        r"\bis\s+(?:this|that)\s+worth\s+it\b",
        r"\bwould\s+you\s+buy\s+(?:this|that)\b",
        r"\bdo\s+you\s+recommend\s+(?:this|that)\b",
        r"\bwould\s+you\s+recommend\s+(?:this|that)\b",

        # Opinions.
        r"\bwhat\s+do\s+you\s+think\s+of\s+(?:this|that)\b",
        r"\bwhat\s+do\s+you\s+think\s+about\s+(?:this|that)\b",
        r"\btell\s+me\s+about\s+(?:this|that)\b",
        r"\bwhat\s+can\s+you\s+tell\s+me\s+about\s+(?:this|that)\b",
        r"\bgive\s+me\s+(?:your\s+)?suggestion(?:s)?\b",
        r"\bgive\s+me\s+(?:your\s+)?recommendation(?:s)?\b",
        r"\bgive\s+me\s+your\s+opinion\b",
        r"\bwhat(?:'s|\s+is)\s+your\s+opinion\b",

        # Buying decisions.
        r"\bdo\s+you\s+think\s+i\s+should\s+buy\s+(?:this|that)\b",
        r"\bdo\s+you\s+think\s+i\s+should\s+get\s+(?:this|that)\b",
        r"\bshould\s+i\s+get\s+(?:this|that)\b",
        r"\bshould\s+i\s+order\s+(?:this|that)\b",
        r"\bshould\s+i\s+choose\s+(?:this|that)\b",

        # Generic analysis.
        r"\btell\s+me\s+what\s+you\s+think\s+about\s+(?:this|that)\b",
        r"\bcan\s+you\s+analyse\s+(?:this|that)\b",
        r"\bcan\s+you\s+analyze\s+(?:this|that)\b",
        r"\bcan\s+you\s+review\s+(?:this|that)\b",
        r"\breview\s+(?:this|that)\b",
    )

    KNOWN_SITES = {
        "google",
        "google.com",
        "youtube",
        "youtube.com",
        "wikipedia",
        "wikipedia.org",
        "wiki",
        "github",
        "github.com",
        "reddit",
        "reddit.com",
        "amazon",
        "amazon.com",
        "facebook",
        "facebook.com",
        "instagram",
        "instagram.com",
        "twitter",
        "twitter.com",
        "x",
        "x.com",
        "linkedin",
        "linkedin.com",
        "discord",
        "discord.com",
        "twitch",
        "twitch.tv",
        "spotify",
        "spotify.com",
        "netflix",
        "netflix.com",
        "chatgpt",
        "chatgpt.com",
        "openai",
        "openai.com",
        "nvidia",
        "nvidia.com",
        "intel",
        "intel.com",
        "amd",
        "amd.com",
        "apple",
        "apple.com",
        "microsoft",
        "microsoft.com",
        "windows",
        "windows.com",
        "stackoverflow",
        "stackoverflow.com",
        "python",
        "python.org",
        "pypi",
        "pypi.org",
        "docker",
        "docker.com",
        "huggingface",
        "huggingface.co",
        "w3schools",
        "w3schools.com",
    }

    WAKE_WORDS = {
        "jarvis",
        "jarvas",
        "jervis",
        "jarvi",
        "gervais",
        "travis",
        "charvis",
        "jarvus",
    }

    WAKE_PREFIXES = {
        "hey",
        "ok",
        "okay",
    }

    def __init__(
        self,
        provider,
        conversation=None,
        context=None,
    ):
        """
        Supports both:

            JarvisAgent(provider, conversation)

        and:

            JarvisAgent(
                provider=provider,
                context=context,
            )
        """

        self.provider = provider

        if context is not None:
            self.conversation = context
        elif conversation is not None:
            self.conversation = conversation
        else:
            self.conversation = None

    # ========================================================
    # RESPONSE TEXT SAFETY
    # ========================================================

    @staticmethod
    def _safe_reply_text(value):
        """
        Always convert agent/tool results to plain text.
        Prevents [object Object] from reaching the frontend.
        """

        if value is None:
            return ""

        if isinstance(
            value,
            str,
        ):
            return value.strip()

        if isinstance(
            value,
            dict,
        ):
            for key in (
                "reply",
                "output_text",
                "text",
                "message",
                "content",
            ):
                candidate = value.get(
                    key
                )

                if isinstance(
                    candidate,
                    str,
                ):
                    candidate = candidate.strip()

                    if candidate:
                        return candidate

            try:
                return json.dumps(
                    value,
                    ensure_ascii=False,
                )

            except Exception:
                return str(value)

        if isinstance(
            value,
            list,
        ):
            try:
                return json.dumps(
                    value,
                    ensure_ascii=False,
                )

            except Exception:
                return str(value)

        return str(value)

    # ========================================================
    # WAKE WORD DETECTION
    # ========================================================

    @classmethod
    def _is_wake_command(
        cls,
        user_message,
    ):
        """
        Handles:

            jarvis
            jarvis jarvis
            hey jarvis
            hey jarvis jarvis
            okay jarvis
            ok jarvis jarvis

        without an AI request.
        """

        text = str(
            user_message
        ).strip().lower()

        if not text:
            return False

        text = re.sub(
            r"[.,!?]+",
            " ",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

        if not text:
            return False

        words = text.split()

        # Remove optional acknowledgement prefix.
        if (
            words
            and words[0] in cls.WAKE_PREFIXES
        ):
            words = words[1:]

        if not words:
            return False

        # Every remaining word must be a known
        # JARVIS wake-word variant.
        return all(
            word in cls.WAKE_WORDS
            for word in words
        )

    # ========================================================
    # RESPONSES API HELPERS
    # ========================================================

    @staticmethod
    def _get_output(
        response,
    ):

        if not isinstance(
            response,
            dict,
        ):
            return []

        output = response.get(
            "output"
        )

        if not isinstance(
            output,
            list,
        ):
            return []

        return output

    @staticmethod
    def _get_function_calls(
        output,
    ):

        calls = []

        for item in output:

            if not isinstance(
                item,
                dict,
            ):
                continue

            if item.get(
                "type"
            ) != "function_call":
                continue

            name = item.get(
                "name"
            )

            call_id = item.get(
                "call_id"
            )

            if not name or not call_id:
                continue

            arguments = item.get(
                "arguments",
                "{}",
            )

            try:
                arguments = json.loads(
                    arguments
                )

            except Exception:
                arguments = {}

            if not isinstance(
                arguments,
                dict,
            ):
                arguments = {}

            calls.append({
                "name": name,
                "call_id": call_id,
                "arguments": arguments,
            })

        return calls

    @classmethod
    def _get_text(
        cls,
        response,
    ):

        if not isinstance(
            response,
            dict,
        ):
            return ""

        text = response.get(
            "output_text"
        )

        if (
            isinstance(
                text,
                str,
            )
            and text.strip()
        ):
            return text.strip()

        output = response.get(
            "output",
            [],
        )

        if not isinstance(
            output,
            list,
        ):
            return ""

        parts = []

        for item in output:

            if not isinstance(
                item,
                dict,
            ):
                continue

            if item.get(
                "type"
            ) != "message":
                continue

            content = item.get(
                "content",
                [],
            )

            if not isinstance(
                content,
                list,
            ):
                continue

            for block in content:

                if not isinstance(
                    block,
                    dict,
                ):
                    continue

                if block.get(
                    "type"
                ) != "output_text":
                    continue

                value = block.get(
                    "text",
                    "",
                )

                if isinstance(
                    value,
                    str,
                ):
                    parts.append(
                        value
                    )

        return "\n".join(
            parts
        ).strip()

    # ========================================================
    # BROWSER CONTEXT
    # ========================================================

    @classmethod
    def _looks_like_browser_context_request(
        cls,
        user_message,
    ):

        text = str(
            user_message
        ).strip().lower()

        if not text:
            return False

        for pattern in cls.BROWSER_CONTEXT_PATTERNS:

            if re.search(
                pattern,
                text,
            ):
                return True

        return False

    # ========================================================
    # TOOL INTENT
    # ========================================================

    @classmethod
    def _looks_like_tool_request(
        cls,
        user_message,
    ):

        text = str(
            user_message
        ).strip().lower()

        if not text:
            return False

        if cls._looks_like_browser_context_request(
            text
        ):
            return True

        explicit_patterns = (
            r"\bopen\b",
            r"\bvisit\b",
            r"\btake\s+me\s+to\b",
            r"\bgo\s+to\b",
            r"\bsearch\b",
            r"\blook\s+up\b",
            r"\bfind\b",
            r"\bprice\b",
            r"\bcost\b",
            r"\bweather\b",
            r"\byoutube\b",
            r"\bclick\b",
            r"\bcurrent\s+page\b",
            r"\bcurrent\s+website\b",
            r"\bcurrent\s+browser\b",
            r"\bgo\s+back\b",
            r"\bgo\s+forward\b",
            r"\bclose\s+(?:the\s+)?browser\b",
        )

        for pattern in explicit_patterns:

            if re.search(
                pattern,
                text,
            ):
                return True

        if text in cls.TOOL_INTENT_WORDS:
            return True

        words = set(
            re.findall(
                r"\b[a-z0-9_-]+\b",
                text,
            )
        )

        if words.intersection(
            cls.TOOL_INTENT_WORDS
        ):
            return True

        return False

    # ========================================================
    # LOCAL ROUTER HELPERS
    # ========================================================

    @classmethod
    def _normalize_site_target(
        cls,
        target,
    ):

        target = str(
            target
        ).strip()

        if not target:
            return ""

        normalized = re.sub(
            r"[^a-zA-Z0-9.\-]+",
            " ",
            target,
        ).strip().lower()

        # apple com -> apple.com
        match = re.fullmatch(
            r"([a-z0-9-]+)\s+com",
            normalized,
        )

        if match:
            normalized = (
                f"{match.group(1)}.com"
            )

        # github io -> github.io
        match = re.fullmatch(
            r"([a-z0-9-]+)\s+io",
            normalized,
        )

        if match:
            normalized = (
                f"{match.group(1)}.io"
            )

        # python org -> python.org
        match = re.fullmatch(
            r"([a-z0-9-]+)\s+org",
            normalized,
        )

        if match:
            normalized = (
                f"{match.group(1)}.org"
            )

        return normalized

    @classmethod
    def _count_repeated_command(
        cls,
        text,
        word,
    ):

        return max(
            1,
            len(
                re.findall(
                    rf"\b{re.escape(word)}\b",
                    text,
                )
            ),
        )

    # ========================================================
    # LOCAL FAST ROUTER
    # ========================================================

    @classmethod
    def _local_route(
        cls,
        user_message,
    ):

        text = str(
            user_message
        ).strip()

        if not text:
            return None

        lower = re.sub(
            r"\s+",
            " ",
            text.lower(),
        ).strip()

        # ----------------------------------------------------
        # WAKE WORD
        # ----------------------------------------------------

        if cls._is_wake_command(
            lower
        ):
            return {
                "name": "wake_ack",
                "arguments": {},
                "needs_ai": False,
            }

        # ----------------------------------------------------
        # BROWSER BACK
        # ----------------------------------------------------

        back_clean = re.sub(
            r"\b(?:please|jarvis)\b",
            "",
            lower,
        )

        back_clean = re.sub(
            r"\s+",
            " ",
            back_clean,
        ).strip()

        if re.fullmatch(
            r"(?:go\s+)?back(?:\s+back)*",
            back_clean,
        ):

            count = cls._count_repeated_command(
                back_clean,
                "back",
            )

            return {
                "name": "browser_back",
                "arguments": {
                    "count": count,
                },
                "needs_ai": False,
            }

        # ----------------------------------------------------
        # BROWSER FORWARD
        # ----------------------------------------------------

        forward_clean = re.sub(
            r"\b(?:please|jarvis)\b",
            "",
            lower,
        )

        forward_clean = re.sub(
            r"\s+",
            " ",
            forward_clean,
        ).strip()

        if re.fullmatch(
            r"(?:go\s+)?forward(?:\s+forward)*",
            forward_clean,
        ):

            count = cls._count_repeated_command(
                forward_clean,
                "forward",
            )

            return {
                "name": "browser_forward",
                "arguments": {
                    "count": count,
                },
                "needs_ai": False,
            }

        # ----------------------------------------------------
        # BROWSER CLOSE
        # ----------------------------------------------------

        close_clean = re.sub(
            r"\b(?:please|jarvis)\b",
            "",
            lower,
        )

        close_clean = re.sub(
            r"\s+",
            " ",
            close_clean,
        ).strip()

        if (
            re.fullmatch(
                r"(?:close|exit)"
                r"(?:\s+(?:close|exit))*",
                close_clean,
            )
            or re.fullmatch(
                r"(?:close|exit)"
                r"(?:\s+(?:close|exit))*"
                r"\s+(?:the\s+)?browser",
                close_clean,
            )
        ):

            return {
                "name": "browser_close",
                "arguments": {},
                "needs_ai": False,
            }

        # ----------------------------------------------------
        # BROWSER OBSERVATION
        # ----------------------------------------------------

        explicit_observation = (
            (
                re.search(
                    r"\b(?:what\s+can\s+you\s+see|what\s+do\s+you\s+see)\b",
                    lower,
                )
                and re.search(
                    r"\b(?:page|browser|website|webpage)\b",
                    lower,
                )
            )
            or re.search(
                r"\b(?:inspect|observe)\s+(?:the\s+)?"
                r"(?:current\s+)?"
                r"(?:page|browser|website|webpage)\b",
                lower,
            )
        )

        browser_context_request = (
            cls._looks_like_browser_context_request(
                lower
            )
        )

        if (
            explicit_observation
            or browser_context_request
        ):
            return {
                "name": "browser_observe",
                "arguments": {},
                "needs_ai": True,
            }

        # ----------------------------------------------------
        # OPEN WEBSITE
        # ----------------------------------------------------

        open_match = re.search(
            r"\b(?:open|visit|take\s+me\s+to|go\s+to|bring\s+up)\s+(.+?)"
            r"(?:\s+website)?$",
            lower,
        )

        if open_match:

            site = open_match.group(
                1
            ).strip()

            site = re.sub(
                r"^(?:the\s+)?",
                "",
                site,
            ).strip()

            normalized_site = (
                cls._normalize_site_target(
                    site
                )
            )

            if (
                normalized_site
                in cls.KNOWN_SITES
            ):

                return {
                    "name": "open_website",
                    "arguments": {
                        "site": normalized_site,
                    },
                    "needs_ai": False,
                }

        normalized_single = (
            cls._normalize_site_target(
                lower
            )
        )

        if (
            normalized_single
            in cls.KNOWN_SITES
        ):

            return {
                "name": "open_website",
                "arguments": {
                    "site": normalized_single,
                },
                "needs_ai": False,
            }

        # ----------------------------------------------------
        # GOOGLE SEARCH
        # ----------------------------------------------------

        search_patterns = (
            r"^(?:google\s+)?search\s+(?:for\s+)?(.+)$",
            r"^(?:google\s+)?look\s+up\s+(.+)$",
            r"^search\s+google\s+for\s+(.+)$",
        )

        for pattern in search_patterns:

            match = re.match(
                pattern,
                text,
                re.IGNORECASE,
            )

            if match:

                query = match.group(
                    1
                ).strip()

                if query:

                    return {
                        "name": "google_search",
                        "arguments": {
                            "query": query,
                        },
                        "needs_ai": False,
                    }

        # ----------------------------------------------------
        # WEATHER
        # ----------------------------------------------------

        weather_match = re.search(
            r"\bweather\b(?:\s+(?:in|for|at)\s+(.+))?$",
            text,
            re.IGNORECASE,
        )

        if weather_match:

            location = (
                weather_match.group(
                    1
                )
                or ""
            ).strip()

            if location:

                return {
                    "name": "get_weather",
                    "arguments": {
                        "location": location,
                    },
                    "needs_ai": False,
                }

        # ----------------------------------------------------
        # YOUTUBE SEARCH
        # ----------------------------------------------------

        youtube_match = re.match(
            r"^(?:search\s+)?youtube\s+(?:for\s+)?(.+)$",
            text,
            re.IGNORECASE,
        )

        if youtube_match:

            query = youtube_match.group(
                1
            ).strip()

            if query:

                return {
                    "name": "search_youtube",
                    "arguments": {
                        "query": query,
                    },
                    "needs_ai": False,
                }

        # ----------------------------------------------------
        # YOUTUBE PLAY
        # ----------------------------------------------------

        play_match = re.match(
            r"^(?:play|watch|listen\s+to)\s+(.+?)"
            r"(?:\s+on\s+youtube)?$",
            text,
            re.IGNORECASE,
        )

        if play_match:

            query = play_match.group(
                1
            ).strip()

            if query:

                return {
                    "name": "play_youtube",
                    "arguments": {
                        "query": query,
                    },
                    "needs_ai": False,
                }

        # ----------------------------------------------------
        # MEDIA
        # ----------------------------------------------------

        media_map = {
            "play": "play",
            "pause": "pause",
            "resume": "play",
            "stop": "stop",
            "mute": "mute",
            "unmute": "unmute",
            "next": "next",
            "next track": "next",
            "previous": "previous",
            "previous track": "previous",
            "volume up": "volume_up",
            "turn volume up": "volume_up",
            "turn up the volume": "volume_up",
            "volume down": "volume_down",
            "turn volume down": "volume_down",
            "turn down the volume": "volume_down",
            "maximum volume": "volume_max",
            "max volume": "volume_max",
            "volume maximum": "volume_max",
            "minimum volume": "volume_min",
            "min volume": "volume_min",
            "volume minimum": "volume_min",
        }

        if lower in media_map:

            return {
                "name": "media_control",
                "arguments": {
                    "action": media_map[
                        lower
                    ],
                },
                "needs_ai": False,
            }

        # ----------------------------------------------------
        # PRODUCT PRICE
        # ----------------------------------------------------

        price_match = re.match(
            r"^(?:find|check|search|tell\s+me|what(?:'s|\s+is))"
            r"(?:\s+the)?\s+(?:current\s+)?(?:price|cost)"
            r"(?:\s+of|\s+for|\s+is)?\s+(.+)$",
            text,
            re.IGNORECASE,
        )

        if price_match:

            product = price_match.group(
                1
            ).strip()

            if product:

                return {
                    "name": "search_product_price",
                    "arguments": {
                        "product": product,
                        "location": "",
                    },
                    "needs_ai": False,
                }

        price_match = re.search(
            r"\b(?:price|cost)\s+(?:of|for)\s+(.+)$",
            text,
            re.IGNORECASE,
        )

        if price_match:

            product = price_match.group(
                1
            ).strip()

            if product:

                return {
                    "name": "search_product_price",
                    "arguments": {
                        "product": product,
                        "location": "",
                    },
                    "needs_ai": False,
                }

        return None

    # ========================================================
    # TOOL EXECUTION
    # ========================================================

    def _execute_tool(
        self,
        name,
        arguments,
    ):

        if name == "wake_ack":

            result = (
                "I'm listening, Sir."
            )

            print(
                "[AGENT] Wake acknowledgement."
            )

            return result

        function = TOOL_FUNCTIONS.get(
            name
        )

        if function is None:

            return (
                f"I do not have a tool named "
                f"{name}, Sir."
            )

        try:

            print(
                f"[AGENT] Executing tool: {name}"
            )

            print(
                f"[AGENT] Arguments: {arguments}"
            )

            result = function(
                **arguments
            )

            if result is None:

                result = (
                    "The tool completed without "
                    "returning a result."
                )

            result = self._safe_reply_text(
                result
            )

            print(
                f"[AGENT] Tool result: {result}"
            )

            return result

        except Exception as e:

            print(
                "[AGENT TOOL ERROR]",
                repr(e),
            )

            return (
                f"The {name} tool failed: {e}"
            )

    def _execute_browser_navigation(
        self,
        name,
        count,
    ):

        try:
            count = int(
                count
            )
        except Exception:
            count = 1

        count = max(
            1,
            min(
                count,
                10,
            ),
        )

        last_result = ""

        for index in range(
            count
        ):

            print(
                f"[AGENT] "
                f"{name} "
                f"{index + 1}/{count}"
            )

            last_result = (
                self._execute_tool(
                    name,
                    {},
                )
            )

        return self._safe_reply_text(
            last_result
        )

    # ========================================================
    # CONVERSATION INPUT
    # ========================================================

    def _build_input(
        self,
        user_message,
    ):

        input_items = []

        if self.conversation is not None:

            if hasattr(
                self.conversation,
                "get_ai_messages",
            ):

                previous = (
                    self.conversation.get_ai_messages(
                        max_messages=(
                            self.MAX_CONTEXT_MESSAGES
                        ),
                        max_chars=(
                            self.MAX_CONTEXT_CHARS
                        ),
                    )
                )

            elif hasattr(
                self.conversation,
                "get_messages",
            ):

                previous = (
                    self.conversation.get_messages()
                )[
                    -self.MAX_CONTEXT_MESSAGES:
                ]

            else:

                previous = []

        else:

            previous = []

        for message in previous:

            if not isinstance(
                message,
                dict,
            ):
                continue

            role = message.get(
                "role"
            )

            content = message.get(
                "content"
            )

            if role not in {
                "user",
                "assistant",
            }:
                continue

            if not content:
                continue

            input_items.append({
                "role": role,
                "content": str(
                    content
                ),
            })

        input_items.append({
            "role": "user",
            "content": user_message,
        })

        return input_items

    # ========================================================
    # BROWSER CONTEXT COMPACTION
    # ========================================================

    @staticmethod
    def _score_browser_line(
        line,
    ):
        """
        Keep information-rich lines when the browser
        snapshot needs to be reduced.
        """

        text = line.lower()

        score = 0

        important_terms = {
            "price": 8,
            "$": 8,
            "€": 8,
            "from ": 7,
            "memory": 7,
            "ram": 7,
            "storage": 7,
            "ssd": 7,
            "gb": 6,
            "tb": 6,
            "chip": 7,
            "processor": 7,
            "cpu": 7,
            "gpu": 7,
            "battery": 7,
            "hours": 6,
            "display": 6,
            "screen": 6,
            "resolution": 6,
            "spec": 7,
            "tech": 5,
            "compare": 5,
            "buy": 5,
            "shop": 4,
            "product": 5,
            "macbook": 5,
            "iphone": 5,
            "ipad": 5,
            "watch": 4,
            "feature": 5,
            "performance": 5,
        }

        for term, value in important_terms.items():

            if term in text:
                score += value

        if len(line) > 180:
            score += 1

        if len(line) < 4:
            score -= 2

        return score

    @classmethod
    def _compact_browser_snapshot(
        cls,
        snapshot,
    ):
        """
        Preserve the page identity plus the most useful
        product/spec/price lines while reducing token usage.
        """

        snapshot = cls._safe_reply_text(
            snapshot
        ).strip()

        if not snapshot:
            return ""

        lines = [
            line.strip()
            for line in snapshot.splitlines()
            if line.strip()
        ]

        if not lines:
            return ""

        if len(snapshot) <= (
            cls.MAX_BROWSER_CONTEXT_CHARS
        ):
            return snapshot

        # Always preserve the beginning because it normally
        # contains page/site identity.
        first_lines = lines[:6]

        candidates = []

        for index, line in enumerate(
            lines
        ):

            if index < 6:
                continue

            score = (
                cls._score_browser_line(
                    line
                )
            )

            candidates.append(
                (
                    score,
                    index,
                    line,
                )
            )

        candidates.sort(
            key=lambda item: (
                -item[0],
                item[1],
            )
        )

        selected = list(
            first_lines
        )

        current_length = sum(
            len(line) + 1
            for line in selected
        )

        for score, index, line in candidates:

            if score <= 0:
                continue

            line_length = len(line) + 1

            if (
                current_length
                + line_length
                > cls.MAX_BROWSER_CONTEXT_CHARS
            ):
                continue

            selected.append(
                line
            )

            current_length += (
                line_length
            )

        # Return in original page order.
        selected_set = set(
            selected
        )

        ordered = []

        for line in lines:

            if (
                line in selected_set
                and line not in ordered
            ):
                ordered.append(
                    line
                )

        result = "\n".join(
            ordered
        ).strip()

        if len(result) > (
            cls.MAX_BROWSER_CONTEXT_CHARS
        ):
            result = (
                result[
                    :cls.MAX_BROWSER_CONTEXT_CHARS
                ]
                .rstrip()
                + "..."
            )

        return result

    def _build_browser_input(
        self,
        user_message,
        browser_result,
    ):

        browser_result = (
            self._compact_browser_snapshot(
                browser_result
            )
        )

        return [
            {
                "role": "user",
                "content": (
                    "User request:\n"
                    f"{user_message}\n\n"
                    "Current browser page:\n"
                    f"{browser_result}\n\n"
                    "Answer using only information "
                    "supported by this page. "
                    "Do not invent missing prices, "
                    "specifications, features or facts. "
                    "Distinguish visible facts from "
                    "your assessment. "
                    "Do not read or repeat the full URL."
                ),
            },
        ]

    # ========================================================
    # NORMAL AI
    # ========================================================

    def _normal_ai_response(
        self,
        user_message,
    ):

        print(
            "[AGENT] Normal conversation. "
            "AI call without tools."
        )

        input_items = self._build_input(
            user_message
        )

        response = self.provider.responses(
            input_items,
            None,
        )

        if not isinstance(
            response,
            dict,
        ):

            return {
                "reply": (
                    "I received an invalid "
                    "response from OpenAI, Sir."
                ),
                "type": "error",
                "tools": [],
            }

        if response.get(
            "error"
        ):

            return {
                "reply": self._safe_reply_text(
                    response["error"]
                ),
                "type": "error",
                "tools": [],
            }

        reply = self._get_text(
            response
        )

        reply = self._safe_reply_text(
            reply
        )

        if not reply:

            return {
                "reply": (
                    "OpenAI returned an empty "
                    "response, Sir."
                ),
                "type": "error",
                "tools": [],
            }

        return {
            "reply": reply,
            "type": "ai",
            "tools": [],
        }

    # ========================================================
    # MAIN PROCESS
    # ========================================================

    def process(
        self,
        user_message,
    ):

        if user_message is None:

            return {
                "reply": "",
                "type": "none",
                "tools": [],
            }

        user_message = str(
            user_message
        ).strip()

        if not user_message:

            return {
                "reply": "",
                "type": "none",
                "tools": [],
            }

        print(
            f"[AGENT] Processing: "
            f"{user_message!r}"
        )

        # ====================================================
        # LOCAL FAST ROUTER
        # ====================================================

        local = self._local_route(
            user_message
        )

        if local:

            name = local[
                "name"
            ]

            arguments = local[
                "arguments"
            ]

            needs_ai = local[
                "needs_ai"
            ]

            print(
                "[AGENT] Local route:",
                name,
                arguments,
                "needs_ai=",
                needs_ai,
            )

            # Repeated browser navigation.
            if name in {
                "browser_back",
                "browser_forward",
            }:

                result = (
                    self._execute_browser_navigation(
                        name,
                        arguments.get(
                            "count",
                            1,
                        ),
                    )
                )

            else:

                result = (
                    self._execute_tool(
                        name,
                        arguments,
                    )
                )

            executed_tools = [{
                "name": name,
                "arguments": arguments,
                "result": result,
            }]

            # Deterministic local response.
            if not needs_ai:

                return {
                    "reply": self._safe_reply_text(
                        result
                    ),
                    "type": "local",
                    "tools": executed_tools,
                }

            # Browser observation gets exactly one
            # compact AI request.
            browser_input = (
                self._build_browser_input(
                    user_message,
                    result,
                )
            )

            print(
                "[AGENT] Browser observation requires "
                "one compact AI response."
            )

            response = self.provider.responses(
                browser_input,
                None,
            )

            if not isinstance(
                response,
                dict,
            ):

                return {
                    "reply": (
                        "I received an invalid "
                        "response from OpenAI, Sir."
                    ),
                    "type": "error",
                    "tools": executed_tools,
                }

            if response.get(
                "error"
            ):

                return {
                    "reply": self._safe_reply_text(
                        response["error"]
                    ),
                    "type": "error",
                    "tools": executed_tools,
                }

            reply = self._get_text(
                response
            )

            reply = self._safe_reply_text(
                reply
            )

            if not reply:

                reply = (
                    self._safe_reply_text(
                        result
                    )
                )

            return {
                "reply": reply,
                "type": "agent",
                "tools": executed_tools,
            }

        # ====================================================
        # NORMAL CHAT
        # ====================================================

        if not self._looks_like_tool_request(
            user_message
        ):

            return self._normal_ai_response(
                user_message
            )

        # ====================================================
        # TOOL-CAPABLE AI AGENT
        # ====================================================

        print(
            "[AGENT] Tool-like request. "
            "Using AI agent with tools."
        )

        input_items = self._build_input(
            user_message
        )

        executed_tools = []

        selected_tools = TOOLS

        for round_number in range(
            self.MAX_TOOL_ROUNDS
        ):

            print(
                "[AGENT] Round",
                round_number + 1,
            )

            response = self.provider.responses(
                input_items,
                selected_tools,
            )

            if not isinstance(
                response,
                dict,
            ):

                return {
                    "reply": (
                        "I received an invalid "
                        "response from OpenAI, Sir."
                    ),
                    "type": "error",
                    "tools": executed_tools,
                }

            if response.get(
                "error"
            ):

                return {
                    "reply": self._safe_reply_text(
                        response["error"]
                    ),
                    "type": "error",
                    "tools": executed_tools,
                }

            output = self._get_output(
                response
            )

            print(
                "[AGENT] Output item count:",
                len(output),
            )

            function_calls = (
                self._get_function_calls(
                    output
                )
            )

            # No tool selected.
            if not function_calls:

                reply = self._get_text(
                    response
                )

                reply = self._safe_reply_text(
                    reply
                )

                if reply:

                    return {
                        "reply": reply,
                        "type": (
                            "agent"
                            if executed_tools
                            else "ai"
                        ),
                        "tools": executed_tools,
                    }

                return {
                    "reply": (
                        "OpenAI returned an empty "
                        "response, Sir."
                    ),
                    "type": "error",
                    "tools": executed_tools,
                }

            # Preserve Responses API output items.
            for item in output:

                if isinstance(
                    item,
                    dict,
                ):

                    input_items.append(
                        item
                    )

            requires_followup = False

            for call in function_calls:

                name = call[
                    "name"
                ]

                arguments = call[
                    "arguments"
                ]

                if (
                    name
                    in {
                        "browser_back",
                        "browser_forward",
                    }
                    and "count" in arguments
                ):

                    result = (
                        self._execute_browser_navigation(
                            name,
                            arguments.get(
                                "count",
                                1,
                            ),
                        )
                    )

                else:

                    result = (
                        self._execute_tool(
                            name,
                            arguments,
                        )
                    )

                result = self._safe_reply_text(
                    result
                )

                executed_tools.append({
                    "name": name,
                    "arguments": arguments,
                    "result": result,
                })

                if name in {
                    "browser_observe",
                    "browser_click",
                }:

                    requires_followup = True

                input_items.append({
                    "type": (
                        "function_call_output"
                    ),
                    "call_id": call[
                        "call_id"
                    ],
                    "output": result,
                })

            # Deterministic terminal tool needs
            # no extra AI round.
            if (
                not requires_followup
                and len(function_calls) == 1
                and function_calls[0][
                    "name"
                ] in self.TERMINAL_TOOLS
            ):

                result = (
                    executed_tools[-1]
                    ["result"]
                )

                print(
                    "[AGENT] Terminal tool completed; "
                    "skipping final AI round."
                )

                return {
                    "reply": self._safe_reply_text(
                        result
                    ),
                    "type": "agent",
                    "tools": executed_tools,
                }

        return {
            "reply": (
                "I reached the execution limit "
                "for that request, Sir."
            ),
            "type": "agent",
            "tools": executed_tools,
        }