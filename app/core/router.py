from app.commands.registry import CommandRegistry

from app.commands.time_date import (
    is_time_command,
    is_date_command,
    handle_time,
    handle_date,
)

from app.commands.browser import (
    is_browser_command,
    handle_browser_command,
)

from app.commands.apps import (
    is_app_command,
    handle_app_command,
)

from app.commands.folders import (
    is_folder_command,
    handle_folder_command,
)

from app.commands.window import (
    is_window_command,
    handle_window_command,
)

from app.commands.news import (
    is_news_command,
    handle_news,
)

from app.commands.memory import (
    is_memory_command,
    handle_memory_command,
)

from weather import get_weather, DEFAULT_CITY

import re


def is_weather_command(command):
    if not command:
        return False

    return "weather" in command.lower()


def handle_weather(command):
    if not command:
        return None

    c = command.lower().strip()

    city = DEFAULT_CITY

    match = re.search(
        r"weather\s+(?:in|for|at)?\s+([a-z ]+?)(?:\s*\?|$)",
        c,
    )

    if match:
        city = match.group(1).strip()

    return get_weather(city)


class CommandRouter:
    def __init__(self):
        self.registry = CommandRegistry()
        self._register_commands()

    def _register_commands(self):

        self.registry.register(
            "memory",
            is_memory_command,
            handle_memory_command,
        )

        self.registry.register(
            "weather",
            is_weather_command,
            handle_weather,
        )

        self.registry.register(
            "news",
            is_news_command,
            handle_news,
        )

        self.registry.register(
            "time",
            is_time_command,
            handle_time,
        )

        self.registry.register(
            "date",
            is_date_command,
            handle_date,
        )

        self.registry.register(
            "browser",
            is_browser_command,
            handle_browser_command,
        )

        self.registry.register(
            "app",
            is_app_command,
            handle_app_command,
        )

        self.registry.register(
            "folder",
            is_folder_command,
            handle_folder_command,
        )

        self.registry.register(
            "window",
            is_window_command,
            handle_window_command,
        )

    def dispatch(self, command):
        return self.registry.dispatch(command)

    def get_commands(self):
        return self.registry.get_commands()


router = CommandRouter()