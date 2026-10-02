from collections import deque


class ConversationContext:

    def __init__(self, limit=20):
        self.messages = deque(maxlen=limit)

    def add_user(self, content):
        self.messages.append({
            "role": "user",
            "content": content
        })

    def add_assistant(self, content):
        self.messages.append({
            "role": "assistant",
            "content": content
        })

    def get_messages(self):
        return list(self.messages)

    def clear(self):
        self.messages.clear()

    def get_recent(self, limit=10):
        items = []

        for message in list(self.messages)[-limit:]:
            role = message.get("role", "")
            content = message.get("content", "")

            if role == "user":
                items.append(
                    f"You: {content}"
                )

            elif role == "assistant":
                items.append(
                    f"JARVIS: {content}"
                )

        return items