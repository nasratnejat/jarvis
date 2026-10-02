import os
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv(override=True)


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


class TimerManager:
    """Supabase-backed timers and reminders."""

    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_SERVICE_KEY")

        if not self.url:
            raise RuntimeError("SUPABASE_URL is missing from .env")
        if not self.key:
            raise RuntimeError("SUPABASE_SERVICE_KEY is missing from .env")

        self.client: Client = create_client(self.url, self.key)

    def _user_id(self, user_id=None):
        value = user_id or os.getenv("SUPABASE_USER_ID")
        if not value:
            raise RuntimeError("SUPABASE_USER_ID is missing from .env")
        return value

    def create(
        self,
        user_id,
        item_type,
        title,
        due_at,
        repeat_rule=None,
        duration_seconds=None,
    ):
        user_id = self._user_id(user_id)

        data = {
            "user_id": user_id,
            "type": item_type,
            "title": title,
            "due_at": due_at,
            "status": "active",
            "repeat_rule": repeat_rule,
            "duration_seconds": duration_seconds,
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        }

        result = (
            self.client
            .table("timers_reminders")
            .insert(data)
            .execute()
        )
        return result.data[0] if result.data else None

    def list_active(self, user_id):
        user_id = self._user_id(user_id)
        result = (
            self.client
            .table("timers_reminders")
            .select("*")
            .eq("user_id", user_id)
            .in_("status", ["active", "paused"])
            .order("due_at", desc=False)
            .execute()
        )
        return result.data or []

    def get(self, user_id, item_id):
        user_id = self._user_id(user_id)
        result = (
            self.client
            .table("timers_reminders")
            .select("*")
            .eq("user_id", user_id)
            .eq("id", item_id)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    def cancel(self, user_id, item_id):
        user_id = self._user_id(user_id)
        result = (
            self.client
            .table("timers_reminders")
            .update({
                "status": "cancelled",
                "updated_at": _now_iso(),
            })
            .eq("user_id", user_id)
            .eq("id", item_id)
            .execute()
        )
        return result.data[0] if result.data else None

    def pause(self, user_id, item_id, remaining_seconds):
        user_id = self._user_id(user_id)
        result = (
            self.client
            .table("timers_reminders")
            .update({
                "status": "paused",
                "remaining_seconds": max(0, int(remaining_seconds)),
                "updated_at": _now_iso(),
            })
            .eq("user_id", user_id)
            .eq("id", item_id)
            .eq("status", "active")
            .execute()
        )
        return result.data[0] if result.data else None

    def resume(self, user_id, item_id, due_at):
        user_id = self._user_id(user_id)
        result = (
            self.client
            .table("timers_reminders")
            .update({
                "status": "active",
                "due_at": due_at,
                "remaining_seconds": None,
                "updated_at": _now_iso(),
            })
            .eq("user_id", user_id)
            .eq("id", item_id)
            .eq("status", "paused")
            .execute()
        )
        return result.data[0] if result.data else None

    def adjust(self, user_id, item_id, seconds):
        item = self.get(user_id, item_id)
        if not item:
            return None

        due = datetime.fromisoformat(
            str(item["due_at"]).replace("Z", "+00:00")
        )
        due = due + timedelta(seconds=seconds)

        result = (
            self.client
            .table("timers_reminders")
            .update({
                "due_at": due.astimezone(timezone.utc).isoformat(),
                "updated_at": _now_iso(),
            })
            .eq("user_id", user_id)
            .eq("id", item_id)
            .eq("status", "active")
            .execute()
        )
        return result.data[0] if result.data else None

    def claim_due(self, user_id):
        """
        Move active due items to triggered and return them.
        Recurring items are advanced to their next occurrence.
        """
        user_id = self._user_id(user_id)
        now = _now_iso()

        due = (
            self.client
            .table("timers_reminders")
            .select("*")
            .eq("user_id", user_id)
            .eq("status", "active")
            .lte("due_at", now)
            .order("due_at", desc=False)
            .execute()
        ).data or []

        triggered = []

        for item in due:
            repeat = item.get("repeat_rule")

            if repeat:
                next_due = self._next_occurrence(
                    item["due_at"],
                    repeat,
                )
                updated = (
                    self.client
                    .table("timers_reminders")
                    .update({
                        "due_at": next_due,
                        "last_triggered_at": now,
                        "updated_at": now,
                    })
                    .eq("user_id", user_id)
                    .eq("id", item["id"])
                    .eq("status", "active")
                    .execute()
                )
            else:
                updated = (
                    self.client
                    .table("timers_reminders")
                    .update({
                        "status": "triggered",
                        "last_triggered_at": now,
                        "updated_at": now,
                    })
                    .eq("user_id", user_id)
                    .eq("id", item["id"])
                    .eq("status", "active")
                    .execute()
                )

            if updated.data:
                triggered.append(updated.data[0])

        return triggered

    def recent_triggered(self, user_id, seconds=120):
        user_id = self._user_id(user_id)
        cutoff = datetime.now(timezone.utc).timestamp() - seconds
        cutoff_iso = datetime.fromtimestamp(
            cutoff, timezone.utc
        ).isoformat()

        result = (
            self.client
            .table("timers_reminders")
            .select("*")
            .eq("user_id", user_id)
            .eq("status", "triggered")
            .gte("last_triggered_at", cutoff_iso)
            .order("last_triggered_at", desc=False)
            .execute()
        )
        return result.data or []

    def _next_occurrence(self, due_at, repeat_rule):
        due = datetime.fromisoformat(
            str(due_at).replace("Z", "+00:00")
        )

        if repeat_rule == "daily":
            from datetime import timedelta
            return (due + timedelta(days=1)).isoformat()

        if repeat_rule.startswith("weekly:"):
            from datetime import timedelta
            return (due + timedelta(days=7)).isoformat()

        return due.isoformat()


timer_manager = TimerManager()
