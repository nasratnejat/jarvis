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

from weather import (
    get_weather,
    DEFAULT_CITY,
)

import re


# ============================================================
# WEATHER
# ============================================================

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


# ============================================================
# NEWS
# ============================================================

def is_news_router_command(command):
    """
    Dedicated news check.

    This exists so NEWS is caught before the command can
    fall through to the AI assistant.
    """

    if not command:
        return False

    return is_news_command(command.strip())


def handle_news_router_command(command):
    """
    Dedicated news handler.
    """

    if not command:
        return None

    return handle_news(command.strip())


# ============================================================
# COMMAND ROUTER
# ============================================================

class CommandRouter:

    def __init__(self):

        self.registry = CommandRegistry()

        self._register_commands()


    def _register_commands(self):

        # ----------------------------------------------------
        # NEWS
        # ----------------------------------------------------

        self.registry.register(
            "news",
            is_news_router_command,
            handle_news_router_command,
        )

        # ----------------------------------------------------
        # WEATHER
        # ----------------------------------------------------

        self.registry.register(
            "weather",
            is_weather_command,
            handle_weather,
        )

        # ----------------------------------------------------
        # TIME
        # ----------------------------------------------------

        self.registry.register(
            "time",
            is_time_command,
            handle_time,
        )

        # ----------------------------------------------------
        # DATE
        # ----------------------------------------------------

        self.registry.register(
            "date",
            is_date_command,
            handle_date,
        )

        # ----------------------------------------------------
        # BROWSER
        # ----------------------------------------------------

        self.registry.register(
            "browser",
            is_browser_command,
            handle_browser_command,
        )

        # ----------------------------------------------------
        # APPS
        # ----------------------------------------------------

        self.registry.register(
            "app",
            is_app_command,
            handle_app_command,
        )

        # ----------------------------------------------------
        # FOLDERS
        # ----------------------------------------------------

        self.registry.register(
            "folder",
            is_folder_command,
            handle_folder_command,
        )

        # ----------------------------------------------------
        # WINDOWS
        # ----------------------------------------------------

        self.registry.register(
            "window",
            is_window_command,
            handle_window_command,
        )


    def dispatch(self, command):

        if not command:
            return None

        command = command.strip()

        if not command:
            return None

        # ----------------------------------------------------
        # HARD NEWS ROUTE
        #
        # Prevents:
        #
        # news
        #
        # from falling through to AI.
        # ----------------------------------------------------

        if is_news_router_command(command):

            print(
                f"[ROUTER] NEWS COMMAND -> {command!r}"
            )

            return handle_news_router_command(command)

        # ----------------------------------------------------
        # NORMAL COMMAND REGISTRY
        # ----------------------------------------------------

        return self.registry.dispatch(command)


    def get_commands(self):

        return self.registry.get_commands()


# ============================================================
# GLOBAL ROUTER
# ============================================================

router = CommandRouter()