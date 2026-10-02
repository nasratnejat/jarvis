import json
import urllib.error
import urllib.request

from app.ai.provider import AIProvider
from app.ai.prompts import SYSTEM_PROMPT


class OpenAIProvider(AIProvider):

    def __init__(
        self,
        api_key,
        model,
    ):
        self.api_key = api_key
        self.model = model

    # ========================================================
    # NORMAL REQUEST
    # ========================================================

    def _request(
        self,
        endpoint,
        payload,
        timeout=30,
    ):

        if not self.api_key:
            return {
                "error": (
                    "My OpenAI API key is not "
                    "configured, Sir. "
                    "Please check your .env file."
                )
            }

        body = json.dumps(
            payload,
            ensure_ascii=False,
        ).encode("utf-8")

        url = (
            "https://api.openai.com/v1/"
            + endpoint
        )

        request = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": (
                    f"Bearer {self.api_key}"
                ),
            },
            method="POST",
        )

        try:
            print(
                f"[OPENAI] POST /v1/{endpoint}"
            )

            with urllib.request.urlopen(
                request,
                timeout=timeout,
            ) as response:

                raw = (
                    response
                    .read()
                    .decode("utf-8")
                )

            data = json.loads(raw)

            print(
                "[OPENAI] Response received."
            )

            return data

        except urllib.error.HTTPError as e:

            try:
                raw_error = (
                    e.read()
                    .decode("utf-8")
                )

                error_data = json.loads(
                    raw_error
                )

                message = (
                    error_data
                    .get("error", {})
                    .get("message")
                )

                if message:
                    print(
                        "[OPENAI HTTP ERROR]",
                        message,
                    )

                    return {
                        "error": (
                            "OpenAI error: "
                            f"{message}"
                        )
                    }

            except Exception:
                pass

            print(
                "[OPENAI HTTP ERROR]",
                repr(e),
            )

            return {
                "error": (
                    "OpenAI returned HTTP "
                    f"error {e.code}, Sir."
                )
            }

        except urllib.error.URLError as e:

            print(
                "[OPENAI CONNECTION ERROR]",
                repr(e),
            )

            return {
                "error": (
                    "I couldn't connect to "
                    "OpenAI, Sir. Please check "
                    "your internet connection."
                )
            }

        except Exception as e:

            print(
                "[OPENAI ERROR]",
                repr(e),
            )

            return {
                "error": (
                    f"I encountered an OpenAI "
                    f"error, Sir: {e}"
                )
            }

    # ========================================================
    # SSE STREAM PARSER
    # ========================================================

    @staticmethod
    def _iter_sse_events(response):
        """
        Parse Server-Sent Events from the Responses API.

        Yields the JSON object carried by each data event.
        """

        data_lines = []

        for raw_line in response:

            if isinstance(
                raw_line,
                bytes,
            ):
                line = raw_line.decode(
                    "utf-8",
                    errors="replace",
                )
            else:
                line = str(raw_line)

            line = line.rstrip(
                "\r\n"
            )

            # Blank line terminates an SSE event.
            if not line:

                if not data_lines:
                    continue

                data = "\n".join(
                    data_lines
                ).strip()

                data_lines = []

                if not data:
                    continue

                if data == "[DONE]":
                    return

                try:
                    yield json.loads(
                        data
                    )
                except json.JSONDecodeError:
                    print(
                        "[OPENAI STREAM] "
                        "Invalid SSE JSON."
                    )

                continue

            # Ignore SSE comments.
            if line.startswith(":"):
                continue

            if line.startswith(
                "data:"
            ):
                data_lines.append(
                    line[5:].lstrip()
                )

        # Handle final event if the connection ends
        # without a trailing blank line.
        if data_lines:

            data = "\n".join(
                data_lines
            ).strip()

            if (
                data
                and data != "[DONE]"
            ):
                try:
                    yield json.loads(
                        data
                    )
                except json.JSONDecodeError:
                    pass

    # ========================================================
    # RESPONSES STREAM
    # ========================================================

    def responses_stream(
        self,
        input_items,
        tools=None,
        timeout=60,
    ):
        """
        Stream Responses API events.

        Text events are exposed as:

            {
                "type": "delta",
                "text": "..."
            }

        Errors are exposed as:

            {
                "type": "error",
                "error": "..."
            }
        """

        if not self.api_key:
            yield {
                "type": "error",
                "error": (
                    "My OpenAI API key is not "
                    "configured, Sir. "
                    "Please check your .env file."
                ),
            }
            return

        payload = {
            "model": self.model,
            "instructions": SYSTEM_PROMPT,
            "input": input_items,
            "stream": True,
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        try:
            serialized = json.dumps(
                payload,
                ensure_ascii=False,
            )

            print(
                "[OPENAI] Approx request chars:",
                len(serialized),
            )

        except Exception:
            pass

        body = json.dumps(
            payload,
            ensure_ascii=False,
        ).encode("utf-8")

        request = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": (
                    f"Bearer {self.api_key}"
                ),
                "Accept": "text/event-stream",
                "Cache-Control": "no-cache",
            },
            method="POST",
        )

        try:

            print(
                "[OPENAI] POST /v1/responses "
                "(streaming)"
            )

            with urllib.request.urlopen(
                request,
                timeout=timeout,
            ) as response:

                for event in self._iter_sse_events(
                    response
                ):

                    event_type = event.get(
                        "type"
                    )

                    if event_type == (
                        "response.output_text.delta"
                    ):

                        delta = event.get(
                            "delta",
                            "",
                        )

                        if isinstance(
                            delta,
                            str,
                        ) and delta:

                            yield {
                                "type": "delta",
                                "text": delta,
                            }

                    elif event_type == "error":

                        message = (
                            event
                            .get("message")
                            or event
                            .get("error")
                            or "OpenAI streaming error."
                        )

                        yield {
                            "type": "error",
                            "error": str(
                                message
                            ),
                        }

                    elif event_type == (
                        "response.failed"
                    ):

                        response_data = event.get(
                            "response",
                            {},
                        )

                        error_data = (
                            response_data
                            .get("error", {})
                            if isinstance(
                                response_data,
                                dict,
                            )
                            else {}
                        )

                        message = (
                            error_data.get(
                                "message"
                            )
                            if isinstance(
                                error_data,
                                dict,
                            )
                            else None
                        )

                        yield {
                            "type": "error",
                            "error": (
                                message
                                or "OpenAI response failed, Sir."
                            ),
                        }

            print(
                "[OPENAI] Streaming response finished."
            )

        except urllib.error.HTTPError as e:

            try:

                raw_error = (
                    e.read()
                    .decode("utf-8")
                )

                error_data = json.loads(
                    raw_error
                )

                message = (
                    error_data
                    .get("error", {})
                    .get("message")
                )

                if message:

                    print(
                        "[OPENAI HTTP ERROR]",
                        message,
                    )

                    yield {
                        "type": "error",
                        "error": (
                            "OpenAI error: "
                            f"{message}"
                        ),
                    }

                    return

            except Exception:
                pass

            print(
                "[OPENAI HTTP ERROR]",
                repr(e),
            )

            yield {
                "type": "error",
                "error": (
                    "OpenAI returned HTTP "
                    f"error {e.code}, Sir."
                ),
            }

        except urllib.error.URLError as e:

            print(
                "[OPENAI CONNECTION ERROR]",
                repr(e),
            )

            yield {
                "type": "error",
                "error": (
                    "I couldn't connect to "
                    "OpenAI, Sir. Please check "
                    "your internet connection."
                ),
            }

        except Exception as e:

            print(
                "[OPENAI STREAM ERROR]",
                repr(e),
            )

            yield {
                "type": "error",
                "error": (
                    f"I encountered an OpenAI "
                    f"streaming error, Sir: {e}"
                ),
            }

    # ========================================================
    # NORMAL RESPONSES API
    # ========================================================

    def responses(
        self,
        input_items,
        tools=None,
    ):

        payload = {
            "model": self.model,
            "instructions": SYSTEM_PROMPT,
            "input": input_items,
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        try:

            serialized = json.dumps(
                payload,
                ensure_ascii=False,
            )

            print(
                "[OPENAI] Approx request chars:",
                len(serialized),
            )

        except Exception:
            pass

        return self._request(
            "responses",
            payload,
        )

    # ========================================================
    # LEGACY ROUTER
    # ========================================================

    def route(
        self,
        user_message,
    ):

        if not user_message:

            return {
                "tool": "none",
            }

        router_tool = {
            "type": "function",
            "name": "select_jarvis_tool",
            "description": (
                "Select the single best JARVIS tool "
                "for the user's request."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "tool": {
                        "type": "string",
                        "enum": [
                            "none",
                            "get_weather",
                            "open_website",
                            "google_search",
                            "search_product_price",
                            "search_youtube",
                            "play_youtube",
                            "media_control",
                            "browser_open",
                            "browser_observe",
                            "browser_click",
                            "browser_back",
                            "browser_forward",
                            "browser_close",
                        ],
                    },
                },
                "required": [
                    "tool",
                ],
                "additionalProperties": False,
            },
            "strict": True,
        }

        instructions = """
You are J.A.R.V.I.S.'s internal tool router.

Select the single best first tool for the user's request.

Use none for ordinary conversation.

Do not answer the user.
Only call select_jarvis_tool.
"""

        payload = {
            "model": self.model,
            "instructions": instructions,
            "input": [
                {
                    "role": "user",
                    "content": user_message,
                }
            ],
            "tools": [
                router_tool,
            ],
            "tool_choice": {
                "type": "function",
                "name": "select_jarvis_tool",
            },
        }

        data = self._request(
            "responses",
            payload,
        )

        if not isinstance(
            data,
            dict,
        ):
            return {
                "tool": "none",
            }

        if data.get("error"):
            return {
                "tool": "none",
            }

        output = data.get(
            "output",
            [],
        )

        if not isinstance(
            output,
            list,
        ):
            return {
                "tool": "none",
            }

        for item in output:

            if not isinstance(
                item,
                dict,
            ):
                continue

            if item.get("type") != (
                "function_call"
            ):
                continue

            if item.get("name") != (
                "select_jarvis_tool"
            ):
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
                return {
                    "tool": "none",
                }

            tool = arguments.get(
                "tool",
                "none",
            )

            if not isinstance(
                tool,
                str,
            ):
                return {
                    "tool": "none",
                }

            return {
                "tool": tool.strip()
            }

        return {
            "tool": "none",
        }

    # ========================================================
    # LEGACY CHAT COMPLETIONS
    # ========================================================

    def ask(
        self,
        user_message,
        conversation=None,
    ):

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            }
        ]

        if conversation:
            messages.extend(
                conversation
            )

        messages.append({
            "role": "user",
            "content": user_message,
        })

        payload = {
            "model": self.model,
            "messages": messages,
        }

        data = self._request(
            "chat/completions",
            payload,
        )

        if "error" in data:
            return data["error"]

        reply = (
            data
            .get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )

        if not reply:

            return (
                "I received an empty "
                "response, Sir."
            )

        return reply.strip()