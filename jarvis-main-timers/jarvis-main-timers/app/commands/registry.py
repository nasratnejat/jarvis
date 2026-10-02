class CommandRegistry:
    def __init__(self):
        self._handlers = []

    def register(self, name, matcher, handler):
        self._handlers.append({
            "name": name,
            "matcher": matcher,
            "handler": handler,
        })

    def dispatch(self, command):
        if not command:
            return None

        for item in self._handlers:
            try:
                if item["matcher"](command):
                    result = item["handler"](command)

                    if result is not None:
                        return result

            except Exception as e:
                print(
                    f"[COMMAND ERROR] "
                    f"{item['name']}: {e!r}"
                )

        return None

    def get_commands(self):
        return [
            item["name"]
            for item in self._handlers
        ]