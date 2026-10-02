from datetime import datetime


TIME_COMMANDS = {
    "what time is it",
    "what's the time",
    "whats the time",
    "tell me the time",
    "current time",
    "time",
    "what is the time",
}


DATE_COMMANDS = {
    "what date is it",
    "what's the date",
    "whats the date",
    "tell me the date",
    "current date",
    "date",
    "what is the date",
    "what day is it",
}


def get_current_time():
    return datetime.now().strftime("%H:%M")


def get_current_date():
    return datetime.now().strftime("%A, %d %B %Y")


def is_time_command(command):
    return command.lower().strip() in TIME_COMMANDS


def is_date_command(command):
    return command.lower().strip() in DATE_COMMANDS


def handle_time(command):
    return f"It's {get_current_time()}, Sir."


def handle_date(command):
    return f"Today is {get_current_date()}, Sir."