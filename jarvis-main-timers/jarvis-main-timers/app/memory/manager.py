import os

from dotenv import load_dotenv
from supabase import create_client, Client


load_dotenv()


class MemoryManager:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_SERVICE_KEY")

        if not self.url:
            raise RuntimeError(
                "SUPABASE_URL is missing from .env"
            )

        if not self.key:
            raise RuntimeError(
                "SUPABASE_SERVICE_KEY is missing from .env"
            )

        self.client: Client = create_client(
            self.url,
            self.key,
        )

    # ---------------------------------------------------------
    # SAVE / UPDATE
    # ---------------------------------------------------------

    def save_memory(
        self,
        user_id: str,
        category: str,
        key: str,
        value: str,
        importance: int = 5,
    ):
        if not user_id:
            raise ValueError("user_id is required")

        if not category:
            raise ValueError("category is required")

        if not key:
            raise ValueError("memory key is required")

        if not value:
            raise ValueError("memory value is required")

        importance = max(
            1,
            min(int(importance), 10),
        )

        existing = (
            self.client
            .table("memories")
            .select("*")
            .eq("user_id", user_id)
            .eq("category", category)
            .eq("key", key)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        data = {
            "user_id": user_id,
            "category": category,
            "key": key,
            "value": value,
            "importance": importance,
        }

        # Update existing memory instead of creating duplicates.
        if existing.data:
            memory_id = existing.data[0]["id"]

            result = (
                self.client
                .table("memories")
                .update(data)
                .eq("id", memory_id)
                .eq("user_id", user_id)
                .execute()
            )

            return result.data

        # Create new memory.
        result = (
            self.client
            .table("memories")
            .insert(data)
            .execute()
        )

        return result.data

    # ---------------------------------------------------------
    # GET ONE MEMORY
    # ---------------------------------------------------------

    def get_memory(
        self,
        user_id: str,
        key: str,
    ):
        result = (
            self.client
            .table("memories")
            .select("*")
            .eq("user_id", user_id)
            .eq("key", key)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if not result.data:
            return None

        return result.data[0]

    # ---------------------------------------------------------
    # SEARCH MEMORIES
    # ---------------------------------------------------------

    def search_memories(
        self,
        user_id: str,
        query: str,
        limit: int = 10,
    ):
        if not query:
            return []

        limit = max(
            1,
            min(int(limit), 50),
        )

        result = (
            self.client
            .table("memories")
            .select("*")
            .eq("user_id", user_id)
            .or_(
                f"key.ilike.%{query}%,"
                f"value.ilike.%{query}%"
            )
            .order("importance", desc=True)
            .limit(limit)
            .execute()
        )

        return result.data

    # ---------------------------------------------------------
    # GET CATEGORY
    # ---------------------------------------------------------

    def get_category(
        self,
        user_id: str,
        category: str,
        limit: int = 100,
    ):
        limit = max(
            1,
            min(int(limit), 1000),
        )

        result = (
            self.client
            .table("memories")
            .select("*")
            .eq("user_id", user_id)
            .eq("category", category)
            .order("importance", desc=True)
            .limit(limit)
            .execute()
        )

        return result.data

    # ---------------------------------------------------------
    # GET ALL MEMORIES
    # ---------------------------------------------------------

    def get_all_memories(
        self,
        user_id: str,
        limit: int = 1000,
    ):
        limit = max(
            1,
            min(int(limit), 5000),
        )

        result = (
            self.client
            .table("memories")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=False)
            .limit(limit)
            .execute()
        )

        return result.data

    # ---------------------------------------------------------
    # DELETE ONE MEMORY BY ID
    # ---------------------------------------------------------

    def delete_memory(
        self,
        user_id: str,
        memory_id: int,
    ):
        result = (
            self.client
            .table("memories")
            .delete()
            .eq("user_id", user_id)
            .eq("id", memory_id)
            .execute()
        )

        return result.data

    # ---------------------------------------------------------
    # DELETE BY KEY
    # ---------------------------------------------------------

    def delete_by_key(
        self,
        user_id: str,
        key: str,
    ):
        result = (
            self.client
            .table("memories")
            .delete()
            .eq("user_id", user_id)
            .eq("key", key)
            .execute()
        )

        return result.data

    # ---------------------------------------------------------
    # DELETE CATEGORY
    # ---------------------------------------------------------

    def delete_category(
        self,
        user_id: str,
        category: str,
    ):
        result = (
            self.client
            .table("memories")
            .delete()
            .eq("user_id", user_id)
            .eq("category", category)
            .execute()
        )

        return result.data

    # ---------------------------------------------------------
    # COMPLETE MEMORY SYSTEM ANNIHILATION
    # ---------------------------------------------------------

    def delete_all_memories(
        self,
        user_id: str,
    ):
        if not user_id:
            raise ValueError("user_id is required")

        result = (
            self.client
            .table("memories")
            .delete()
            .eq("user_id", user_id)
            .execute()
        )

        return result.data


memory_manager = MemoryManager()