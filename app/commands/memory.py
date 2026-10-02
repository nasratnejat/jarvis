
import os
import re

from dotenv import load_dotenv

from app.memory.manager import memory_manager


load_dotenv()


# -------------------------------------------------------------
# USER ID
# -------------------------------------------------------------

def _get_user_id():
    user_id = os.getenv("SUPABASE_USER_ID")

    if not user_id:
        raise RuntimeError(
            "SUPABASE_USER_ID is missing from .env"
        )

    return user_id


# -------------------------------------------------------------
# KEY CLEANING
# -------------------------------------------------------------

def _clean_key(key):
    if not key:
        return ""

    key = key.strip().lower()

    key = re.sub(
        r"^(my|the)\s+",
        "",
        key,
    )

    key = key.replace(
        "favourite",
        "favorite",
    )

    key = re.sub(
        r"\s+",
        " ",
        key,
    )

    return key.strip()


# -------------------------------------------------------------
# MEMORY FORMATTING
# -------------------------------------------------------------

def _format_memories(memories):
    if not memories:
        return "Your memory is currently empty, Sir."

    lines = [
        f"Your memory contains {len(memories)} stored entries, Sir."
    ]

    for memory in memories:
        key = memory.get("key", "unknown")
        value = memory.get("value", "")

        lines.append(
            f"- {key}: {value}"
        )

    return "\n".join(lines)


# -------------------------------------------------------------
# COMMAND DETECTION
# -------------------------------------------------------------

def is_memory_command(command):
    """
    IMPORTANT:
    This function must be conservative.

    Memory is only activated when the user clearly refers
    to memory, remembering, storing, forgetting, etc.

    Normal questions such as:
        tell me a joke
        tell me the weather
        what's 2 + 2
        what is the time
        offline

    MUST NOT enter the memory system.
    """

    if not command:
        return False

    c = command.strip().lower()

    patterns = [

        # -----------------------------------------------------
        # STORE
        # -----------------------------------------------------

        r"^remember\b",
        r"^store\b",
        r"^save\b",
        r"^keep\b",
        r"^make\s+a\s+note\b",
        r"^add\s+.+\s+to\s+my\s+memory\b",

        # -----------------------------------------------------
        # EXPLICIT MEMORY STORE PHRASES
        # -----------------------------------------------------

        r"^remember\s+that\b",
        r"^remember\s+this\b",
        r"^save\s+this\s+to\s+my\s+memory\b",
        r"^save\s+this\s+in\s+my\s+memory\b",
        r"^store\s+this\s+in\s+my\s+memory\b",
        r"^keep\s+this\s+in\s+my\s+memory\b",

        # -----------------------------------------------------
        # VIEW
        # -----------------------------------------------------

        r"^memories$",
        r"^my\s+memories$",
        r"^memory$",
        r"^my\s+memory$",

        r"^show\s+my\s+memories$",
        r"^show\s+me\s+my\s+memories$",
        r"^show\s+my\s+memory$",
        r"^show\s+me\s+my\s+memory$",

        r"^show\s+me\s+what\s+i\s+have\s+stored$",
        r"^what\s+do\s+i\s+have\s+stored$",

        r"^what\s+do\s+i\s+currently\s+have\s+in\s+memory$",
        r"^what\s+do\s+i\s+remember\s+about\s+myself$",
        r"^what\s+do\s+i\s+remember\s+about\s+me$",

        r"^tell\s+me\s+my\s+memories$",
        r"^tell\s+me\s+what\s+i\s+have\s+stored$",

        # -----------------------------------------------------
        # SEARCH
        # -----------------------------------------------------

        r"^search\s+my\s+memory\b",
        r"^search\s+my\s+memories\b",

        r"^look\s+through\s+my\s+memory\b",
        r"^look\s+through\s+my\s+memories\b",

        r"^find\s+anything\s+in\s+my\s+memory\b",
        r"^find\s+anything\s+in\s+my\s+memories\b",

        # -----------------------------------------------------
        # RECALL
        # -----------------------------------------------------

        r"^what\s+do\s+i\s+remember\s+about\b",
        r"^what\s+do\s+i\s+have\s+in\s+my\s+memory\s+about\b",
        r"^bring\s+up\s+what\s+i\s+remember\s+about\b",
        r"^check\s+my\s+memory\s+for\b",

        r"^do\s+you\s+remember\b",

        # -----------------------------------------------------
        # DELETE
        # -----------------------------------------------------

        r"^(forget|remove|erase|delete|clear)\b",

        # -----------------------------------------------------
        # COMPLETE MEMORY ANNIHILATION
        # -----------------------------------------------------

        r"^initiate\s+memory\s+system\s+annihilation$",

        # -----------------------------------------------------
        # BARE MEMORY KEYS
        # -----------------------------------------------------

        r"^favorite\b",
        r"^favourite\b",
        r"^preferred\b",
        r"^birthday$",
    ]

    return any(
        re.match(
            pattern,
            c,
            re.IGNORECASE,
        )
        for pattern in patterns
    )


# -------------------------------------------------------------
# COMMAND HANDLER
# -------------------------------------------------------------

def handle_memory_command(command):
    if not command:
        return None

    command = command.strip()

    if not command:
        return None

    c = command.lower().strip()

    user_id = _get_user_id()

    # =========================================================
    # 1. STORE / UPDATE MEMORY
    # =========================================================

    remember_match = re.match(
        r"^(?:remember|store|save|keep)\s+"
        r"(?:this\s+)?"
        r"(?:for\s+me\s+)?"
        r"(?:in\s+my\s+memory\s+)?"
        r"(?:that\s+)?"
        r"(.+?)\s*(?:is|=|:)\s*(.+)$",
        c,
        re.IGNORECASE,
    )

    if remember_match:
        raw_key = remember_match.group(1).strip()
        value = remember_match.group(2).strip()

        key = _clean_key(raw_key)

        if not key or not value:
            return (
                "I need both the memory key and the value, Sir."
            )

        memory_manager.save_memory(
            user_id=user_id,
            category="personal",
            key=key,
            value=value,
            importance=5,
        )

        return (
            f"I've stored {key} as {value} in your memory, Sir."
        )

    # =========================================================
    # 2. STORE USING "REMEMBER X"
    # =========================================================

    simple_remember = re.match(
        r"^(?:remember|store|save|keep)\s+(.+)$",
        c,
        re.IGNORECASE,
    )

    if simple_remember:
        text = simple_remember.group(1).strip()

        if text.startswith("that "):
            text = text[5:].strip()

        parts = re.split(
            r"\s+(?:is|as|=|:)\s+",
            text,
            maxsplit=1,
            flags=re.IGNORECASE,
        )

        if len(parts) == 2:
            raw_key = parts[0].strip()
            value = parts[1].strip()

            key = _clean_key(raw_key)

            if key and value:
                memory_manager.save_memory(
                    user_id=user_id,
                    category="personal",
                    key=key,
                    value=value,
                    importance=5,
                )

                return (
                    f"I've stored {key} as {value} in your memory, Sir."
                )

    # =========================================================
    # 3. MEMORY SYSTEM ANNIHILATION
    # =========================================================

    annihilation_phrases = [
        "initiate memory system annihilation",
    ]

    normalized_command = re.sub(
        r"[.!?]+$",
        "",
        c,
    ).strip()

    if normalized_command in annihilation_phrases:

        memories = memory_manager.get_all_memories(
            user_id=user_id,
        )

        if not memories:
            return (
                "Your memory system is already empty, Sir."
            )

        deleted = memory_manager.delete_all_memories(
            user_id=user_id,
        )

        deleted_count = len(deleted)

        return (
            f"Memory system annihilated, Sir. "
            f"{deleted_count} memory entries permanently deleted."
        )

    # =========================================================
    # 4. SHOW ALL MEMORY
    # =========================================================

    view_patterns = [
        r"^memories$",
        r"^my memories$",
        r"^memory$",
        r"^my memory$",
        r"^show my memories$",
        r"^show me my memories$",
        r"^show my memory$",
        r"^show me my memory$",
        r"^show me what i have stored$",
        r"^what do i have stored$",
        r"^what do i currently have in memory$",
        r"^what do i remember about myself$",
        r"^what do i remember about me$",
        r"^tell me my memories$",
        r"^tell me what i have stored$",
    ]

    if any(
        re.match(
            pattern,
            c,
            re.IGNORECASE,
        )
        for pattern in view_patterns
    ):
        memories = memory_manager.get_all_memories(
            user_id=user_id,
        )

        return _format_memories(memories)

    # =========================================================
    # 5. SEARCH MEMORY
    # =========================================================

    search_match = re.match(
        r"^(?:search my memory|"
        r"search my memories|"
        r"look through my memory|"
        r"look through my memories|"
        r"find anything in my memory|"
        r"find anything in my memories)"
        r"\s+(?:for\s+)?(.+)$",
        c,
        re.IGNORECASE,
    )

    if search_match:
        query = search_match.group(1).strip()

        memories = memory_manager.search_memories(
            user_id=user_id,
            query=query,
            limit=20,
        )

        if not memories:
            return (
                f"I found nothing in your memory about {query}, Sir."
            )

        return _format_memories(memories)

    # =========================================================
    # 6. MEMORY ABOUT SOMETHING
    # =========================================================

    about_match = re.match(
        r"^(?:what do i remember about|"
        r"what do i have in my memory about|"
        r"bring up what i remember about|"
        r"check my memory for)"
        r"\s+(.+)$",
        c,
        re.IGNORECASE,
    )

    if about_match:
        query = about_match.group(1).strip()

        memories = memory_manager.search_memories(
            user_id=user_id,
            query=query,
            limit=20,
        )

        if not memories:
            return (
                f"I found nothing in your memory about {query}, Sir."
            )

        return _format_memories(memories)

    # =========================================================
    # 7. DELETE ONE MEMORY
    # =========================================================

    delete_match = re.match(
        r"^(?:forget|remove|erase|delete|clear)"
        r"\s+(?:my\s+)?"
        r"(?:memory\s+of\s+)?(.+)$",
        c,
        re.IGNORECASE,
    )

    if delete_match:
        target = delete_match.group(1).strip()

        if target in {
            "memories",
            "memory",
            "all memories",
            "everything",
            "everything in memory",
        }:
            return (
                "For complete memory destruction, use "
                "\"Initiate memory system annihilation.\", Sir."
            )

        key = _clean_key(target)

        memory = memory_manager.get_memory(
            user_id=user_id,
            key=key,
        )

        if memory:
            memory_manager.delete_memory(
                user_id=user_id,
                memory_id=memory["id"],
            )

            return (
                f"I've removed {key} from your memory, Sir."
            )

        matches = memory_manager.search_memories(
            user_id=user_id,
            query=target,
            limit=10,
        )

        if matches:
            memory = matches[0]

            memory_manager.delete_memory(
                user_id=user_id,
                memory_id=memory["id"],
            )

            return (
                f"I've removed "
                f"{memory.get('key', target)} "
                f"from your memory, Sir."
            )

        return (
            f"I don't have a memory entry for {target}, Sir."
        )

    # =========================================================
    # 8. DO YOU REMEMBER
    # =========================================================

    remember_query = re.match(
        r"^do you remember\s+(.+)$",
        c,
        re.IGNORECASE,
    )

    if remember_query:
        query = remember_query.group(1).strip()

        memories = memory_manager.search_memories(
            user_id=user_id,
            query=query,
            limit=10,
        )

        if not memories:
            return (
                f"I don't have anything stored about {query}, Sir."
            )

        return _format_memories(memories)

    # =========================================================
    # 9. BARE MEMORY KEY
    # =========================================================

    bare_key = _clean_key(c)

    if bare_key:
        memory = memory_manager.get_memory(
            user_id=user_id,
            key=bare_key,
        )

        if memory:
            return (
                f"Your {bare_key} is "
                f"{memory['value']}, Sir."
            )

    # ---------------------------------------------------------
    # IMPORTANT:
    # If nothing explicitly matched, return None.
    #
    # This allows the normal JARVIS assistant to handle it.
    # ---------------------------------------------------------

    return None
