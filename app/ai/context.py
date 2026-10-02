from collections import deque


class ConversationContext:

    # Keep enough history for natural continuity,
    # but don't allow old conversations to grow indefinitely.
    DEFAULT_LIMIT = 20

    # Maximum characters we allow the AI context to consume.
    DEFAULT_AI_CHAR_LIMIT = 3500

    def __init__(self, limit=DEFAULT_LIMIT):
        self.messages = deque(
            maxlen=limit
        )

    # ========================================================
    # MESSAGE STORAGE
    # ========================================================

    def add_user(self, content):

        if content is None:
            return

        content = str(content).strip()

        if not content:
            return

        self.messages.append({
            "role": "user",
            "content": content,
        })

    def add_assistant(self, content):

        if content is None:
            return

        content = str(content).strip()

        if not content:
            return

        self.messages.append({
            "role": "assistant",
            "content": content,
        })

    # ========================================================
    # RAW CONTEXT
    # ========================================================

    def get_messages(self):

        return list(
            self.messages
        )

    # ========================================================
    # COMPACT AI CONTEXT
    #
    # Keeps the newest useful conversation while applying
    # a hard character budget.
    # ========================================================

    def get_ai_messages(
        self,
        max_messages=6,
        max_chars=3500,
    ):

        if max_messages <= 0:
            return []

        if max_chars <= 0:
            return []

        source = list(
            self.messages
        )

        selected = []

        total_chars = 0

        # Walk backwards so the newest context has priority.
        for message in reversed(source):

            if len(selected) >= max_messages:
                break

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

            if content is None:
                continue

            content = str(
                content
            ).strip()

            if not content:
                continue

            # Prevent one enormous assistant response from
            # consuming the entire context budget.
            remaining = (
                max_chars
                - total_chars
            )

            if remaining <= 0:
                break

            if len(content) > remaining:

                # Keep the beginning because it normally
                # contains the actual answer/topic.
                content = (
                    content[:remaining]
                    .rstrip()
                )

            if not content:
                continue

            item = {
                "role": role,
                "content": content,
            }

            selected.append(
                item
            )

            total_chars += len(
                content
            )

            if total_chars >= max_chars:
                break

        # We collected newest -> oldest.
        # Reverse back into chronological order.
        selected.reverse()

        return selected

    # ========================================================
    # RECENT HUMAN-READABLE CONTEXT
    # ========================================================

    def get_recent(
        self,
        limit=10,
    ):

        items = []

        if limit <= 0:
            return items

        for message in list(
            self.messages
        )[-limit:]:

            if not isinstance(
                message,
                dict,
            ):
                continue

            role = message.get(
                "role",
                "",
            )

            content = message.get(
                "content",
                "",
            )

            if not content:
                continue

            content = str(
                content
            ).strip()

            if role == "user":

                items.append(
                    f"You: {content}"
                )

            elif role == "assistant":

                items.append(
                    f"JARVIS: {content}"
                )

        return items

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(self):

        self.messages.clear()

    # ========================================================
    # SIZE INFORMATION
    #
    # Useful for diagnostics.
    # ========================================================

    def stats(self):

        messages = list(
            self.messages
        )

        characters = 0

        for message in messages:

            content = message.get(
                "content",
                "",
            )

            characters += len(
                str(content)
            )

        return {
            "messages": len(
                messages
            ),
            "characters": characters,
        }