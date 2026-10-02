import os
import re
from datetime import datetime, timedelta, timezone

from dateutil import parser as date_parser

from app.timers.manager import timer_manager


_DURATION_UNIT = {
    "second": 1,
    "seconds": 1,
    "sec": 1,
    "secs": 1,
    "minute": 60,
    "minutes": 60,
    "min": 60,
    "mins": 60,
    "hour": 3600,
    "hours": 3600,
    "hr": 3600,
    "hrs": 3600,
    "day": 86400,
    "days": 86400,
}


def _user_id():
    value = os.getenv("SUPABASE_USER_ID")
    if not value:
        raise RuntimeError("SUPABASE_USER_ID is missing from .env")
    return value


def _duration_seconds(text):
    if not text:
        return None

    text = text.lower().strip()
    total = 0.0
    found = False

    for number, unit in re.findall(
        r"(\d+(?:\.\d+)?)\s*(seconds?|secs?|sec|minutes?|mins?|min|hours?|hrs?|hr|days?)",
        text,
    ):
        total += float(number) * _DURATION_UNIT[unit]
        found = True

    if not found:
        return None

    return max(1, int(total))


def _format_duration(seconds):
    seconds = max(0, int(seconds))
    if seconds < 60:
        return f"{seconds} second" + ("" if seconds == 1 else "s")

    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)

    parts = []
    if days:
        parts.append(f"{days} day" + ("" if days == 1 else "s"))
    if hours:
        parts.append(f"{hours} hour" + ("" if hours == 1 else "s"))
    if minutes:
        parts.append(f"{minutes} minute" + ("" if minutes == 1 else "s"))
    if sec:
        parts.append(f"{sec} second" + ("" if sec == 1 else "s"))

    return " ".join(parts)


def _parse_clock_time(value, base):
    value = value.strip().lower()
    value = re.sub(r"\s+", " ", value)

    m = re.fullmatch(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", value)
    if not m:
        return None

    hour = int(m.group(1))
    minute = int(m.group(2) or 0)
    meridiem = m.group(3)

    if meridiem:
        if hour < 1 or hour > 12 or minute > 59:
            return None
        if meridiem == "pm" and hour != 12:
            hour += 12
        if meridiem == "am" and hour == 12:
            hour = 0
    elif hour > 23 or minute > 59:
        return None

    result = base.replace(
        hour=hour,
        minute=minute,
        second=0,
        microsecond=0,
    )

    if result <= base:
        result += timedelta(days=1)

    return result


def _parse_when(text):
    """
    Parse useful spoken reminder forms:
      in 20 minutes
      in 1 hour
      at 18:30
      at 6 PM
      tomorrow at 9 AM
      tomorrow
      every day at 8 AM
      every monday at 9 AM
    """
    now = datetime.now().astimezone()
    lowered = text.lower().strip()

    # Recurring daily / weekly schedules.
    recurring = None
    recurring_match = re.search(
        r"\bevery\s+(day|monday|tuesday|wednesday|thursday|friday|saturday|sunday)"
        r"(?:\s+at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?))?",
        lowered,
        re.IGNORECASE,
    )
    if recurring_match:
        period = recurring_match.group(1).lower()
        clock = recurring_match.group(2) or "09:00"

        target_base = now
        parsed_clock = _parse_clock_time(
            clock,
            target_base,
        )
        if not parsed_clock:
            return None, None

        if period == "day":
            target = parsed_clock
            recurring = "daily"
        else:
            weekdays = {
                "monday": 0,
                "tuesday": 1,
                "wednesday": 2,
                "thursday": 3,
                "friday": 4,
                "saturday": 5,
                "sunday": 6,
            }
            target = parsed_clock
            wanted = weekdays[period]
            days_ahead = (wanted - target.weekday()) % 7
            if days_ahead == 0 and target <= now:
                days_ahead = 7
            target += timedelta(days=days_ahead)
            recurring = f"weekly:{period}"

        return target, recurring

    # "in X" must stop before "to <message>".
    duration_match = re.search(
        r"\bin\s+(.+?)(?=\s+to\b|$)",
        lowered,
        re.IGNORECASE,
    )
    if duration_match:
        seconds = _duration_seconds(duration_match.group(1))
        if seconds:
            return now + timedelta(seconds=seconds), None

    # "tomorrow at 9 AM" without swallowing the reminder message.
    tomorrow_match = re.search(
        r"\btomorrow(?:\s+at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?))?",
        lowered,
        re.IGNORECASE,
    )
    if tomorrow_match:
        clock = tomorrow_match.group(1)
        target = now + timedelta(days=1)
        if clock:
            parsed_clock = _parse_clock_time(clock, target)
            if parsed_clock:
                # _parse_clock_time can roll forward a day; for tomorrow
                # we want the explicit tomorrow date.
                parsed_clock = parsed_clock.replace(
                    year=target.year,
                    month=target.month,
                    day=target.day,
                )
                return parsed_clock, None

        return target.replace(
            hour=9,
            minute=0,
            second=0,
            microsecond=0,
        ), None

    clock_match = re.search(
        r"\bat\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b",
        lowered,
        re.IGNORECASE,
    )
    if clock_match:
        parsed = _parse_clock_time(clock_match.group(1), now)
        if parsed:
            return parsed, None

    return None, None


def _next_item(items, item_id=None, item_type=None):
    if item_id is not None:
        for item in items:
            if str(item.get("id")) == str(item_id):
                return item
        return None

    filtered = [
        x for x in items
        if not item_type or x.get("type") == item_type
    ]

    return filtered[0] if len(filtered) == 1 else None


def _parse_id(text):
    m = re.search(r"\b(?:timer|reminder)\s*#?\s*(\d+)\b", text, re.I)
    return int(m.group(1)) if m else None


def _human_item(item):
    kind = "timer" if item.get("type") == "timer" else "reminder"
    item_id = item.get("id")
    title = item.get("title") or "Untitled"

    try:
        due = datetime.fromisoformat(
            str(item["due_at"]).replace("Z", "+00:00")
        )
        now = datetime.now(timezone.utc)
        remaining = int((due - now).total_seconds())
        remaining_text = _format_duration(remaining)
    except Exception:
        remaining_text = "an unknown amount of time"

    return f"{kind} {item_id}: {title} — {remaining_text} remaining"


def is_timer_command(command):
    if not command:
        return False

    c = command.strip().lower()

    patterns = [
        r"\bset\b.*\btimer\b",
        r"\bstart\b.*\btimer\b",
        r"\bcreate\b.*\btimer\b",
        r"\b(?:a\s+)?\d+\s+(?:seconds?|minutes?|mins?|hours?|hrs?|days?)\b.*\btimer\b",
        r"\btimer\b.*\b(?:for|in)\b",
        r"\bset\b.*\breminder\b",
        r"\bremind\s+me\b",
        r"\bcreate\b.*\breminder\b",
        r"\blist\b.*\b(?:timers?|reminders?)\b",
        r"\b(?:what|which)\b.*\b(?:timers?|reminders?)\b",
        r"\b(?:cancel|delete|remove|clear)\b.*\b(?:timer|reminder)s?\b",
        r"\b(?:pause|resume|continue)\b.*\b(?:timer|reminder)\b",
        r"\b(?:add|subtract|remove)\b.*\b(?:minutes?|seconds?|hours?)\b.*\b(?:timer|reminder)\b",
        r"\bhow\s+(?:much\s+time|long)\b.*\b(?:timer|reminder)\b",
    ]

    return any(re.search(p, c) for p in patterns)


def handle_timer_command(command):
    if not command:
        return None

    original = command.strip()
    c = original.lower()
    user_id = _user_id()

    # ---------------------------------------------------------
    # LIST
    # ---------------------------------------------------------
    if re.search(r"\b(?:list|show|what|which)\b", c) and re.search(
        r"\b(?:timers?|reminders?)\b", c
    ):
        items = timer_manager.list_active(user_id)

        if not items:
            return "You have no active timers or reminders, Sir."

        lines = [
            f"You have {len(items)} active timer"
            + ("" if len(items) == 1 else "s")
            + " or reminder"
            + ("" if len(items) == 1 else "s")
            + ", Sir."
        ]
        for item in items:
            lines.append(_human_item(item))
        return "\n".join(lines)

    # ---------------------------------------------------------
    # CANCEL
    # ---------------------------------------------------------
    if re.search(r"\b(?:cancel|delete|remove|clear)\b", c) and re.search(
        r"\b(?:timer|reminder)s?\b", c
    ):
        if re.search(r"\ball\b", c):
            items = timer_manager.list_active(user_id)
            for item in items:
                timer_manager.cancel(user_id, item["id"])
            return (
                f"Cancelled all {len(items)} active timers and reminders, Sir."
            )

        item_id = _parse_id(original)
        items = timer_manager.list_active(user_id)

        item = _next_item(
            items,
            item_id=item_id,
            item_type="timer" if "timer" in c and "reminder" not in c else None,
        )

        if not item:
            return (
                "Tell me which timer or reminder to cancel, Sir. "
                "For example, \"cancel timer 2\"."
            )

        timer_manager.cancel(user_id, item["id"])
        return (
            f"Cancelled {item.get('type', 'item')} "
            f"{item['id']}, Sir."
        )

    # ---------------------------------------------------------
    # PAUSE
    # ---------------------------------------------------------
    if re.search(r"\b(?:pause)\b", c) and "timer" in c:
        item_id = _parse_id(original)
        items = timer_manager.list_active(user_id)
        item = _next_item(items, item_id=item_id, item_type="timer")

        if not item:
            return "Tell me which timer to pause, Sir."

        due = datetime.fromisoformat(
            str(item["due_at"]).replace("Z", "+00:00")
        )
        remaining = max(
            0,
            int(
                (
                    due - datetime.now(timezone.utc)
                ).total_seconds()
            ),
        )

        timer_manager.pause(user_id, item["id"], remaining)
        return (
            f"Paused timer {item['id']}. "
            f"{_format_duration(remaining)} remained, Sir."
        )

    # ---------------------------------------------------------
    # RESUME
    # ---------------------------------------------------------
    if re.search(r"\b(?:resume|continue)\b", c) and "timer" in c:
        item_id = _parse_id(original)
        items = timer_manager.list_active(user_id)
        paused = [x for x in items if x.get("status") == "paused"]

        item = _next_item(paused, item_id=item_id, item_type="timer")
        if not item:
            return "Tell me which paused timer to resume, Sir."

        remaining = int(item.get("remaining_seconds") or 0)
        due = datetime.now(timezone.utc) + timedelta(seconds=remaining)

        timer_manager.resume(
            user_id,
            item["id"],
            due.isoformat(),
        )
        return f"Resumed timer {item['id']}, Sir."

    # ---------------------------------------------------------
    # ADJUST
    # ---------------------------------------------------------
    adjust = re.search(
        r"\b(add|subtract|remove)\s+(.+?)\s+(?:to|from)\s+(?:timer|reminder)\s*#?\s*(\d+)\b",
        c,
    )
    if adjust:
        action = adjust.group(1)
        seconds = _duration_seconds(adjust.group(2))
        item_id = int(adjust.group(3))

        if not seconds:
            return "I couldn't determine the adjustment amount, Sir."

        if action in {"subtract", "remove"}:
            seconds = -seconds

        item = timer_manager.adjust(user_id, item_id, seconds)
        if not item:
            return f"I couldn't adjust item {item_id}, Sir."

        return (
            f"Adjusted {item.get('type', 'item')} {item_id} "
            f"by {_format_duration(abs(seconds))}, Sir."
        )

    # ---------------------------------------------------------
    # "HOW MUCH TIME LEFT"
    # ---------------------------------------------------------
    if re.search(r"\bhow\s+(?:much\s+time|long)\b", c):
        item_id = _parse_id(original)
        items = timer_manager.list_active(user_id)

        item = _next_item(items, item_id=item_id)
        if not item:
            return "I need a timer or reminder number, Sir."

        return _human_item(item) + "."

    # ---------------------------------------------------------
    # TIMER CREATION
    # ---------------------------------------------------------
    if "timer" in c:
        duration = _duration_seconds(c)

        if not duration:
            return (
                "Tell me the timer duration, Sir. "
                "For example, \"set a timer for 15 minutes\"."
            )

        due = datetime.now(timezone.utc) + timedelta(seconds=duration)

        item = timer_manager.create(
            user_id=user_id,
            item_type="timer",
            title="Timer",
            due_at=due.isoformat(),
            duration_seconds=duration,
        )

        return (
            f"Timer {item['id']} set for "
            f"{_format_duration(duration)}, Sir."
        )

    # ---------------------------------------------------------
    # REMINDER CREATION
    # ---------------------------------------------------------
    if re.search(r"\bremind\s+me\b|\breminder\b", c):
        when, repeat_rule = _parse_when(original)

        if not when:
            return (
                "Tell me when to remind you, Sir. "
                "For example, \"remind me in 30 minutes to call John\" "
                "or \"remind me tomorrow at 9 AM to send the email\"."
            )

        title_match = re.search(
            r"\b(?:to|that)\s+(.+)$",
            original,
            re.IGNORECASE,
        )
        title = (
            title_match.group(1).strip()
            if title_match
            else "Reminder"
        )
        title = re.sub(r"[.!?]+$", "", title).strip()

        item = timer_manager.create(
            user_id=user_id,
            item_type="reminder",
            title=title or "Reminder",
            due_at=when.astimezone(timezone.utc).isoformat(),
            repeat_rule=repeat_rule,
        )

        if repeat_rule == "daily":
            schedule_text = "every day"
        elif repeat_rule and repeat_rule.startswith("weekly:"):
            schedule_text = f"every {repeat_rule.split(':', 1)[1]}"
        else:
            schedule_text = when.strftime("%A")

        return (
            f"Reminder {item['id']} set for "
            f"{schedule_text} at {when.strftime('%H:%M')}, Sir."
        )

    return None


def get_due_notifications():
    """Used by the API/browser to claim and deliver due items."""
    user_id = _user_id()
    return timer_manager.claim_due(user_id)
