import re

import psutil


PROTECTED_NAMES = {
    "system",
    "system idle process",
    "smss.exe",
    "csrss.exe",
    "wininit.exe",
    "services.exe",
    "lsass.exe",
    "winlogon.exe",
}


# ---------------------------------------------------------
# PROCESS DATA
# ---------------------------------------------------------

def _process_list():
    processes = []

    for process in psutil.process_iter(
        [
            "pid",
            "name",
            "cpu_percent",
            "memory_info",
        ]
    ):
        try:
            info = process.info

            processes.append(
                {
                    "pid": info["pid"],
                    "name": info["name"] or "Unknown",
                    "cpu": float(
                        info.get("cpu_percent") or 0
                    ),
                    "memory": (
                        info["memory_info"].rss
                        if info.get("memory_info")
                        else 0
                    ),
                }
            )

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
        ):
            continue

    return processes


def _find_process(name):
    name = name.lower().strip()

    if name.endswith(".exe"):
        name = name[:-4]

    for process in _process_list():
        process_name = process["name"].lower()

        if process_name.endswith(".exe"):
            process_name = process_name[:-4]

        if (
            process_name == name
            or name in process_name
        ):
            return process

    return None


# ---------------------------------------------------------
# FORMATTING
# ---------------------------------------------------------

def _format_memory(value):
    if value >= 1024 ** 3:
        return f"{value / (1024 ** 3):.1f} GB"

    if value >= 1024 ** 2:
        return f"{value / (1024 ** 2):.0f} MB"

    return f"{value / 1024:.0f} KB"


# ---------------------------------------------------------
# SHOW RUNNING PROCESSES
# ---------------------------------------------------------

def _show_processes():
    processes = _process_list()

    if not processes:
        return (
            "I could not retrieve the running "
            "processes, Sir."
        )

    processes.sort(
        key=lambda process: process["cpu"],
        reverse=True,
    )

    top = processes[:8]

    result = []

    for process in top:
        result.append(
            f"{process['name']} "
            f"(PID {process['pid']}, "
            f"{process['cpu']:.0f}% CPU, "
            f"{_format_memory(process['memory'])})"
        )

    return (
        "Top running processes: "
        + ", ".join(result)
        + ", Sir."
    )


# ---------------------------------------------------------
# CHECK PROCESS
# ---------------------------------------------------------

def _is_running(name):
    process = _find_process(name)

    if process:
        return (
            f"Yes, Sir. {process['name']} "
            f"is running."
        )

    return (
        f"No, Sir. {name} is not running."
    )


# ---------------------------------------------------------
# KILL PROCESS
# ---------------------------------------------------------

def _kill_process(name):
    process = _find_process(name)

    if not process:
        return (
            f"I could not find {name} running, Sir."
        )

    process_name = process["name"]
    pid = process["pid"]

    if process_name.lower() in PROTECTED_NAMES:
        return (
            f"I will not terminate the protected "
            f"system process {process_name}, Sir."
        )

    try:
        target = psutil.Process(pid)

        target.terminate()

        try:
            target.wait(timeout=3)

        except psutil.TimeoutExpired:
            target.kill()
            target.wait(timeout=3)

        return (
            f"Terminated {process_name}, Sir."
        )

    except psutil.NoSuchProcess:
        return (
            f"{process_name} has already closed, Sir."
        )

    except psutil.AccessDenied:
        return (
            f"I could not terminate {process_name}. "
            f"Administrator privileges may be required, Sir."
        )

    except Exception:
        return (
            f"I could not terminate {process_name}, Sir."
        )


# ---------------------------------------------------------
# EXTRACT PROCESS NAME
# ---------------------------------------------------------

def _extract_process_name(command):
    match = re.search(
        r"\b(?:kill|terminate|stop)\s+"
        r"(?:the\s+)?"
        r"(?:process\s+)?"
        r"(.+?)\s*$",
        command,
        re.IGNORECASE,
    )

    if not match:
        return None

    return (
        match.group(1)
        .strip()
        .strip("\"'")
    )


# ---------------------------------------------------------
# COMMAND DETECTION
# ---------------------------------------------------------

def is_process_command(command):
    if not command:
        return False

    c = command.lower().strip()

    patterns = (
        # Running process lists
        r"\bshow\s+(?:the\s+)?running\s+process(?:es)?\b",
        r"\blist\s+(?:the\s+)?running\s+process(?:es)?\b",
        r"\bshow\s+(?:the\s+)?process(?:es)?\s+running\b",
        r"\blist\s+(?:the\s+)?process(?:es)?\s+running\b",
        r"\bshow\s+(?:top\s+)?process(?:es)?\b",
        r"\blist\s+(?:top\s+)?process(?:es)?\b",
        r"\btop\s+process(?:es)?\b",
        r"\brunning\s+process(?:es)?\b",

        # CPU usage
        r"\bwhat(?:'s| is)\s+using\s+the\s+most\s+cpu\b",
        r"\bwhich\s+process(?:es)?\s+(?:uses?|is\s+using)\s+the\s+most\s+cpu\b",
        r"\bhighest\s+cpu\s+process(?:es)?\b",

        # Check whether a specific process is running
        r"\bis\s+.+\s+running\b",

        # Process termination
        r"\b(?:kill|terminate|stop)\b",
    )

    return any(
        re.search(pattern, c, re.IGNORECASE)
        for pattern in patterns
    )


# ---------------------------------------------------------
# COMMAND HANDLER
# ---------------------------------------------------------

def handle_process_command(command):
    if not command:
        return None

    c = command.lower().strip()

    # -----------------------------------------------------
    # KILL / TERMINATE / STOP
    # -----------------------------------------------------

    if re.search(
        r"\b(?:kill|terminate|stop)\b",
        c,
        re.IGNORECASE,
    ):
        name = _extract_process_name(command)

        if not name:
            return (
                "Tell me which process to stop, Sir."
            )

        return _kill_process(name)

    # -----------------------------------------------------
    # CHECK SPECIFIC PROCESS
    # Example:
    # "is discord running"
    # -----------------------------------------------------

    running_match = re.search(
        r"\bis\s+(.+?)\s+running\b",
        c,
        re.IGNORECASE,
    )

    if running_match:
        name = (
            running_match.group(1)
            .strip()
            .strip("\"'")
        )

        return _is_running(name)

    # -----------------------------------------------------
    # DEFAULT
    # Show running processes
    # -----------------------------------------------------

    return _show_processes()