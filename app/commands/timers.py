
import os
import re
from datetime import datetime, timedelta, timezone

from app.timers.manager import timer_manager


# =========================================================
# DURATION
# =========================================================

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


# =========================================================
# USER
# =========================================================

def _user_id():
    value = os.getenv("SUPABASE_USER_ID")

    if not value:
        raise RuntimeError(
            "SUPABASE_USER_ID is missing from .env"
        )

    return value


# =========================================================
# DURATION HELPERS
# =========================================================

def _duration_seconds(text):
    if not text:
        return None

    text = text.lower().strip()

    total = 0.0
    found = False

    matches = re.findall(
        r"(\d+(?:\.\d+)?)\s*"
        r"(seconds?|secs?|sec|minutes?|mins?|min|hours?|hrs?|hr|days?)",
        text,
    )

    for number, unit in matches:
        total += (
            float(number)
            * _DURATION_UNIT[unit]
        )
        found = True

    if not found:
        return None

    return max(1, int(total))


def _format_duration(seconds):
    seconds = max(0, int(seconds))

    if seconds < 60:
        return (
            f"{seconds} second"
            + ("" if seconds == 1 else "s")
        )

    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)

    parts = []

    if days:
        parts.append(
            f"{days} day"
            + ("" if days == 1 else "s")
        )

    if hours:
        parts.append(
            f"{hours} hour"
            + ("" if hours == 1 else "s")
        )

    if minutes:
        parts.append(
            f"{minutes} minute"
            + ("" if minutes == 1 else "s")
        )

    if sec:
        parts.append(
            f"{sec} second"
            + ("" if sec == 1 else "s")
        )

    return " ".join(parts)


# =========================================================
# CLOCK PARSING
# =========================================================

def _parse_clock_time(value, base):
    value = value.strip().lower()
    value = re.sub(r"\s+", " ", value)

    match = re.fullmatch(
        r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?",
        value,
    )

    if not match:
        return None

    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    meridiem = match.group(3)

    if meridiem:
        if hour < 1 or hour > 12:
            return None

        if minute > 59:
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


# =========================================================
# REMINDER TIME PARSING
# =========================================================

def _parse_when(text):
    now = datetime.now().astimezone()
    lowered = text.lower().strip()

    # -----------------------------------------------------
    # RECURRING
    # -----------------------------------------------------

    recurring_match = re.search(
        r"\bevery\s+"
        r"(day|monday|tuesday|wednesday|thursday|"
        r"friday|saturday|sunday)"
        r"(?:\s+at\s+"
        r"(\d{1,2}(?::\d{2})?\s*(?:am|pm)?))?",
        lowered,
        re.IGNORECASE,
    )

    if recurring_match:

        period = recurring_match.group(1).lower()
        clock = recurring_match.group(2) or "09:00"

        parsed_clock = _parse_clock_time(
            clock,
            now,
        )

        if not parsed_clock:
            return None, None

        if period == "day":

            target = parsed_clock
            repeat_rule = "daily"

            return target, repeat_rule

        weekdays = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }

        wanted = weekdays[period]

        target = parsed_clock

        days_ahead = (
            wanted - target.weekday()
        ) % 7

        if days_ahead == 0 and target <= now:
            days_ahead = 7

        target += timedelta(
            days=days_ahead
        )

        return (
            target,
            f"weekly:{period}",
        )

    # -----------------------------------------------------
    # IN X MINUTES
    # -----------------------------------------------------

    duration_match = re.search(
        r"\bin\s+(.+?)(?=\s+to\b|$)",
        lowered,
        re.IGNORECASE,
    )

    if duration_match:

        seconds = _duration_seconds(
            duration_match.group(1)
        )

        if seconds:
            return (
                now + timedelta(seconds=seconds),
                None,
            )

    # -----------------------------------------------------
    # TOMORROW
    # -----------------------------------------------------

    tomorrow_match = re.search(
        r"\btomorrow"
        r"(?:\s+at\s+"
        r"(\d{1,2}(?::\d{2})?\s*(?:am|pm)?))?",
        lowered,
        re.IGNORECASE,
    )

    if tomorrow_match:

        clock = tomorrow_match.group(1)

        target = now + timedelta(days=1)

        if clock:

            parsed_clock = _parse_clock_time(
                clock,
                target,
            )

            if parsed_clock:

                parsed_clock = parsed_clock.replace(
                    year=target.year,
                    month=target.month,
                    day=target.day,
                )

                return parsed_clock, None

        return (
            target.replace(
                hour=9,
                minute=0,
                second=0,
                microsecond=0,
            ),
            None,
        )

    # -----------------------------------------------------
    # AT CLOCK TIME
    # -----------------------------------------------------

    clock_match = re.search(
        r"\bat\s+"
        r"(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b",
        lowered,
        re.IGNORECASE,
    )

    if clock_match:

        parsed = _parse_clock_time(
            clock_match.group(1),
            now,
        )

        if parsed:
            return parsed, None

    return None, None


# =========================================================
# ITEM HELPERS
# =========================================================

def _parse_id(text):

    match = re.search(
        r"\b(?:timer|reminder)"
        r"\s*#?\s*(\d+)\b",
        text,
        re.IGNORECASE,
    )

    return (
        int(match.group(1))
        if match
        else None
    )


def _get_item(
    items,
    item_id=None,
):
    if item_id is not None:

        for item in items:

            if str(item.get("id")) == str(item_id):
                return item

        return None

    if len(items) == 1:
        return items[0]

    return None


def _remaining_seconds(item):

    try:

        if item.get("status") == "paused":

            return int(
                item.get("remaining_seconds") or 0
            )

        due = datetime.fromisoformat(
            str(item["due_at"]).replace(
                "Z",
                "+00:00",
            )
        )

        now = datetime.now(timezone.utc)

        return max(
            0,
            int(
                (due - now).total_seconds()
            ),
        )

    except Exception:

        return 0


def _human_item(item):

    kind = (
        "timer"
        if item.get("type") == "timer"
        else "reminder"
    )

    item_id = item.get("id")

    title = (
        item.get("title")
        or (
            "Timer"
            if kind == "timer"
            else "Reminder"
        )
    )

    remaining = _remaining_seconds(item)

    remaining_text = _format_duration(
        remaining
    )

    status = item.get("status")

    if status == "paused":

        return (
            f"{kind} {item_id}: "
            f"{title}. "
            f"Paused with "
            f"{remaining_text} remaining."
        )

    return (
        f"{kind} {item_id}: "
        f"{title}. "
        f"{remaining_text} remaining."
    )


# =========================================================
# COMMAND DETECTION
# =========================================================

def is_timer_command(command):

    if not command:
        return False

    c = command.strip().lower()

    patterns = [

        # Creation
        r"\bset\b.*\btimer\b",
        r"\bstart\b.*\btimer\b",
        r"\bcreate\b.*\btimer\b",
        r"\btimer\b.*\b(?:for|in)\b",

        # Reminder creation
        r"\bset\b.*\breminder\b",
        r"\bremind\s+me\b",
        r"\bcreate\b.*\breminder\b",

        # Lists
        r"\b(?:show|list|display)\b.*\b"
        r"(?:my\s+)?(?:timers?|reminders?)\b",

        r"\b(?:what|which)\b.*\b"
        r"(?:my\s+)?(?:timers?|reminders?)\b",

        r"\bwhat\s+(?:timers?|reminders?)\b",

        r"\b(?:are|is)\b.*\b"
        r"(?:timers?|reminders?)\b.*\brunning\b",

        r"\b(?:active|running)\b.*\b"
        r"(?:timers?|reminders?)\b",

        r"\b(?:how\s+many)\b.*\b"
        r"(?:timers?|reminders?)\b",

        # Cancel
        r"\b(?:cancel|delete|remove|clear)\b.*\b"
        r"(?:timer|reminder)s?\b",

        # Pause/resume
        r"\b(?:pause|resume|continue)\b.*\b"
        r"(?:timer|reminder)\b",

        # Adjust
        r"\b(?:add|subtract|remove)\b.*\b"
        r"(?:minutes?|seconds?|hours?)\b.*\b"
        r"(?:timer|reminder)\b",

        # Remaining
        r"\bhow\s+(?:much\s+time|long)\b.*\b"
        r"(?:timer|reminder)\b",

        # ID-specific
        r"\btimer\s*#?\s*\d+\b",
        r"\breminder\s*#?\s*\d+\b",
    ]

    return any(
        re.search(pattern, c)
        for pattern in patterns
    )


# =========================================================
# LIST RESPONSE
# =========================================================

def _list_response(
    user_id,
    requested_type=None,
):
    items = timer_manager.list_active(
        user_id
    )

    if requested_type:
        items = [
            item
            for item in items
            if item.get("type") == requested_type
        ]

    # ---------------------------------------------
    # TIMER LIST
    # ---------------------------------------------

    if requested_type == "timer":

        if not items:
            return (
                "You have no active timers, Sir."
            )

        if len(items) == 1:

            return (
                "You have one active timer, Sir. "
                + _human_item(items[0])
            )

        lines = [
            f"You have {len(items)} active timers, Sir."
        ]

        for item in items:
            lines.append(
                _human_item(item)
            )

        return "\n".join(lines)

    # ---------------------------------------------
    # REMINDER LIST
    # ---------------------------------------------

    if requested_type == "reminder":

        if not items:
            return (
                "You have no active reminders, Sir."
            )

        if len(items) == 1:

            return (
                "You have one active reminder, Sir. "
                + _human_item(items[0])
            )

        lines = [
            f"You have {len(items)} active reminders, Sir."
        ]

        for item in items:
            lines.append(
                _human_item(item)
            )

        return "\n".join(lines)

    # ---------------------------------------------
    # BOTH
    # ---------------------------------------------

    if not items:

        return (
            "You have no active timers or reminders, Sir."
        )

    timers = [
        item
        for item in items
        if item.get("type") == "timer"
    ]

    reminders = [
        item
        for item in items
        if item.get("type") == "reminder"
    ]

    lines = []

    if timers:

        lines.append(
            f"{len(timers)} active "
            f"timer"
            f"{'' if len(timers) == 1 else 's'}:"
        )

        for item in timers:
            lines.append(
                _human_item(item)
            )

    if reminders:

        lines.append(
            f"{len(reminders)} active "
            f"reminder"
            f"{'' if len(reminders) == 1 else 's'}:"
        )

        for item in reminders:
            lines.append(
                _human_item(item)
            )

    return "\n".join(lines)


# =========================================================
# MAIN HANDLER
# =========================================================

def handle_timer_command(command):

    if not command:
        return None

    original = command.strip()
    c = original.lower()

    user_id = _user_id()

    # =====================================================
    # LIST / SHOW
    # =====================================================

    if re.search(
        r"\b(?:show|list|display|what|which)\b",
        c,
    ) and re.search(
        r"\b(?:timer|timers|reminder|reminders)\b",
        c,
    ):

        if re.search(
            r"\breminders?\b",
            c,
        ) and not re.search(
            r"\btimers?\b",
            c,
        ):

            return _list_response(
                user_id,
                requested_type="reminder",
            )

        if re.search(
            r"\btimers?\b",
            c,
        ) and not re.search(
            r"\breminders?\b",
            c,
        ):

            return _list_response(
                user_id,
                requested_type="timer",
            )

        return _list_response(
            user_id
        )

    # =====================================================
    # "WHAT TIMERS ARE RUNNING?"
    # =====================================================

    if (
        re.search(
            r"\b(?:running|active)\b",
            c,
        )
        and re.search(
            r"\btimers?\b",
            c,
        )
    ):

        return _list_response(
            user_id,
            requested_type="timer",
        )

    # =====================================================
    # "WHAT REMINDERS DO I HAVE?"
    # =====================================================

    if re.search(
        r"\b(?:my|active)\s+reminders?\b",
        c,
    ):

        return _list_response(
            user_id,
            requested_type="reminder",
        )

    # =====================================================
    # CANCEL
    # =====================================================

    if re.search(
        r"\b(?:cancel|delete|remove|clear)\b",
        c,
    ) and re.search(
        r"\b(?:timer|reminder)s?\b",
        c,
    ):

        if re.search(
            r"\ball\b",
            c,
        ):

            items = timer_manager.list_active(
                user_id
            )

            for item in items:

                timer_manager.cancel(
                    user_id,
                    item["id"],
                )

            return (
                f"Cancelled all {len(items)} "
                f"active timers and reminders, Sir."
            )

        item_id = _parse_id(
            original
        )

        items = timer_manager.list_active(
            user_id
        )

        item = _get_item(
            items,
            item_id=item_id,
        )

        if not item:

            return (
                "I couldn't find that active timer "
                "or reminder, Sir."
            )

        timer_manager.cancel(
            user_id,
            item["id"],
        )

        return (
            f"Cancelled {item.get('type', 'item')} "
            f"{item['id']}, Sir."
        )

    # =====================================================
    # PAUSE
    # =====================================================

    if (
        "pause" in c
        and "timer" in c
    ):

        item_id = _parse_id(
            original
        )

        items = timer_manager.list_active(
            user_id
        )

        timers = [
            item
            for item in items
            if item.get("type") == "timer"
            and item.get("status") == "active"
        ]

        item = _get_item(
            timers,
            item_id=item_id,
        )

        if not item:

            return (
                "I couldn't find that active timer, Sir."
            )

        remaining = _remaining_seconds(
            item
        )

        timer_manager.pause(
            user_id,
            item["id"],
            remaining,
        )

        return (
            f"Paused timer {item['id']}. "
            f"{_format_duration(remaining)} remained, Sir."
        )

    # =====================================================
    # RESUME
    # =====================================================

    if (
        re.search(
            r"\b(?:resume|continue)\b",
            c,
        )
        and "timer" in c
    ):

        item_id = _parse_id(
            original
        )

        items = timer_manager.list_active(
            user_id
        )

        paused = [
            item
            for item in items
            if item.get("type") == "timer"
            and item.get("status") == "paused"
        ]

        item = _get_item(
            paused,
            item_id=item_id,
        )

        if not item:

            return (
                "I couldn't find that paused timer, Sir."
            )

        remaining = int(
            item.get("remaining_seconds") or 0
        )

        due = (
            datetime.now(timezone.utc)
            + timedelta(seconds=remaining)
        )

        timer_manager.resume(
            user_id,
            item["id"],
            due.isoformat(),
        )

        return (
            f"Resumed timer {item['id']}, Sir."
        )

    # =====================================================
    # ADD / SUBTRACT
    # =====================================================

    adjust = re.search(
        r"\b(add|subtract|remove)\s+"
        r"(.+?)\s+"
        r"(?:to|from)\s+"
        r"(?:timer|reminder)\s*#?\s*(\d+)\b",
        c,
    )

    if adjust:

        action = adjust.group(1)

        seconds = _duration_seconds(
            adjust.group(2)
        )

        item_id = int(
            adjust.group(3)
        )

        if not seconds:

            return (
                "I couldn't determine the adjustment amount, Sir."
            )

        if action in {
            "subtract",
            "remove",
        }:

            seconds = -seconds

        item = timer_manager.adjust(
            user_id,
            item_id,
            seconds,
        )

        if not item:

            return (
                f"I couldn't adjust item "
                f"{item_id}, Sir."
            )

        return (
            f"Adjusted {item.get('type', 'item')} "
            f"{item_id} by "
            f"{_format_duration(abs(seconds))}, Sir."
        )

    # =====================================================
    # REMAINING TIME
    # =====================================================

    if re.search(
        r"\bhow\s+(?:much\s+time|long)\b",
        c,
    ):

        item_id = _parse_id(
            original
        )

        items = timer_manager.list_active(
            user_id
        )

        if item_id is not None:

            item = _get_item(
                items,
                item_id=item_id,
            )

            if not item:

                return (
                    f"I couldn't find timer or reminder "
                    f"{item_id}, Sir."
                )

            return (
                _human_item(item)
                + "."
            )

        timers = [
            item
            for item in items
            if item.get("type") == "timer"
        ]

        if not timers:

            return (
                "You have no active timers, Sir."
            )

        if len(timers) == 1:

            return (
                _human_item(timers[0])
                + "."
            )

        lines = [
            f"You have {len(timers)} active timers, Sir."
        ]

        for item in timers:
            lines.append(
                _human_item(item)
            )

        return "\n".join(lines)

    # =====================================================
    # TIMER CREATION
    # =====================================================

    if "timer" in c:

        duration = _duration_seconds(
            c
        )

        if not duration:

            return (
                "Tell me the timer duration, Sir. "
                "For example, "
                "\"set a timer for 15 minutes\"."
            )

        due = (
            datetime.now(timezone.utc)
            + timedelta(seconds=duration)
        )

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

    # =====================================================
    # REMINDER CREATION
    # =====================================================

    if re.search(
        r"\bremind\s+me\b|\breminder\b",
        c,
    ):

        when, repeat_rule = _parse_when(
            original
        )

        if not when:

            return (
                "Tell me when to remind you, Sir. "
                "For example, "
                "\"remind me in 30 minutes to call John\" "
                "or "
                "\"remind me tomorrow at 9 AM to send the email\"."
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

        title = re.sub(
            r"[.!?]+$",
            "",
            title,
        ).strip()

        item = timer_manager.create(
            user_id=user_id,
            item_type="reminder",
            title=title or "Reminder",
            due_at=when.astimezone(
                timezone.utc
            ).isoformat(),
            repeat_rule=repeat_rule,
        )

        if repeat_rule == "daily":

            schedule_text = "every day"

        elif (
            repeat_rule
            and repeat_rule.startswith("weekly:")
        ):

            schedule_text = (
                f"every "
                f"{repeat_rule.split(':', 1)[1]}"
            )

        else:

            schedule_text = (
                when.strftime("%A")
            )

        return (
            f"Reminder {item['id']} set for "
            f"{schedule_text} at "
            f"{when.strftime('%H:%M')}, Sir."
        )

    return None


# =========================================================
# DUE NOTIFICATIONS
# =========================================================

def get_due_notifications():

    user_id = _user_id()

    return timer_manager.claim_due(
        user_id
    )

