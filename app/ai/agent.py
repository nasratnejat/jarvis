import json

from app.ai.tools import (
    TOOLS,
    TOOL_FUNCTIONS,
)


class JarvisAgent:

    MAX_TOOL_ROUNDS = 6

    TERMINAL_TOOLS = {
        "get_weather",
        "open_website",
        "google_search",
        "search_product_price",
        "search_youtube",
        "play_youtube",
        "media_control",
        "browser_close",
    }

    def __init__(
        self,
        provider,
        conversation,
    ):
        self.provider = provider
        self.conversation = conversation

    @staticmethod
    def _tool_map():

        return {
            tool.get("name"): tool
            for tool in TOOLS
            if isinstance(tool, dict)
            and tool.get("name")
        }

    def _route(
        self,
        user_message,
    ):

        print(
            "[AGENT] Asking AI router for tool..."
        )

        result = self.provider.route(
            user_message,
        )

        if not isinstance(
            result,
            dict,
        ):
            return None

        tool = result.get(
            "tool"
        )

        if not isinstance(
            tool,
            str,
        ):
            return None

        tool = tool.strip()

        if not tool or tool == "none":
            return None

        tool_map = self._tool_map()

        if tool not in tool_map:

            print(
                "[AGENT] Router selected "
                "unknown tool:",
                tool,
            )

            return None

        return tool

    def _selected_tools(
        self,
        selected_name,
    ):

        if not selected_name:
            return []

        tool = self._tool_map().get(
            selected_name
        )

        if not tool:
            return []

        return [tool]

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

            if item.get("type") != (
                "function_call"
            ):
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

    @staticmethod
    def _get_text(
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

        if isinstance(
            text,
            str,
        ) and text.strip():

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

            if item.get("type") != (
                "message"
            ):
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

                if block.get("type") != (
                    "output_text"
                ):
                    continue

                value = block.get(
                    "text",
                    "",
                )

                if isinstance(
                    value,
                    str,
                ):
                    parts.append(value)

        return "\n".join(
            parts
        ).strip()

    def _execute_tool(
        self,
        name,
        arguments,
    ):

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

            result = str(result)

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

    def process(
        self,
        user_message,
    ):

        if not user_message:

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

        selected_name = self._route(
            user_message
        )

        print(
            "[AGENT] AI selected tool:",
            selected_name or "none",
        )

        selected_tools = (
            self._selected_tools(
                selected_name
            )
        )

        print(
            "[AGENT] Execution tools:",
            [
                tool.get("name")
                for tool in selected_tools
            ],
        )

        input_items = []

        previous = (
            self.conversation
            .get_messages()
        )

        recent_messages = previous[-6:]

        for message in recent_messages:

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
                "content": content,
            })

        input_items.append({
            "role": "user",
            "content": user_message,
        })

        executed_tools = []

        # --------------------------------------------------
        # NO TOOL
        # --------------------------------------------------

        if not selected_tools:

            print(
                "[AGENT] No tool required."
            )

            response = (
                self.provider.responses(
                    input_items,
                    None,
                )
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

            if response.get("error"):

                return {
                    "reply": str(
                        response["error"]
                    ),
                    "type": "error",
                    "tools": [],
                }

            reply = self._get_text(
                response
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

        # --------------------------------------------------
        # TOOL LOOP
        # --------------------------------------------------

        for round_number in range(
            self.MAX_TOOL_ROUNDS
        ):

            print(
                "[AGENT] Round",
                round_number + 1,
            )

            response = (
                self.provider.responses(
                    input_items,
                    selected_tools,
                )
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

            if response.get("error"):

                return {
                    "reply": str(
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

            if not function_calls:

                reply = self._get_text(
                    response
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

                result = self._execute_tool(
                    name,
                    call["arguments"],
                )

                executed_tools.append({
                    "name": name,
                    "arguments": call[
                        "arguments"
                    ],
                    "result": result,
                })

                if name in {
                    "browser_open",
                    "browser_click",
                    "browser_back",
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
                    "[AGENT] Terminal tool "
                    "completed; skipping "
                    "final AI round."
                )

                return {
                    "reply": result,
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