import re
import socket
import subprocess
import urllib.request


def _run(command, timeout=5):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
            encoding="utf-8",
            errors="replace",
        )

        return result.returncode, result.stdout.strip()

    except Exception:
        return -1, ""


def _local_ip():
    try:
        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
        )

        try:
            sock.connect(("1.1.1.1", 80))
            return sock.getsockname()[0]
        finally:
            sock.close()

    except Exception:
        try:
            ip = socket.gethostbyname(
                socket.gethostname()
            )

            if not ip.startswith("127."):
                return ip

        except Exception:
            pass

    return None


def _public_ip():
    try:
        with urllib.request.urlopen(
            "https://api.ipify.org",
            timeout=4,
        ) as response:

            return response.read().decode().strip()

    except Exception:
        return None


def _wifi_name():
    code, output = _run(
        [
            "netsh",
            "wlan",
            "show",
            "interfaces",
        ]
    )

    if code != 0:
        return None

    match = re.search(
        r"^\s*SSID\s*:\s*(.+)$",
        output,
        re.MULTILINE | re.IGNORECASE,
    )

    if match:
        return match.group(1).strip()

    return None


def _internet_working():
    code, _ = _run(
        [
            "ping",
            "-n",
            "1",
            "-w",
            "2500",
            "1.1.1.1",
        ],
        timeout=4,
    )

    return code == 0


def _ping(host):
    code, output = _run(
        [
            "ping",
            "-n",
            "1",
            "-w",
            "3000",
            host,
        ],
        timeout=5,
    )

    if code != 0:
        return f"Ping to {host} failed, Sir."

    match = re.search(
        r"time[=<]\s*(\d+(?:\.\d+)?)\s*ms",
        output,
        re.IGNORECASE,
    )

    if match:
        return (
            f"Ping to {host} is "
            f"{match.group(1)} milliseconds, Sir."
        )

    return f"{host} is reachable, Sir."


def is_network_command(command):
    if not command:
        return False

    c = command.lower().strip()

    return any(
        re.search(pattern, c)
        for pattern in (
            r"\bwhat(?:'s| is) my ip\b",
            r"\bmy local ip\b",
            r"\bpublic ip\b",
            r"\bwhat(?:'s| is) my public ip\b",
            r"\bwhat(?:'s| is) my wifi\b",
            r"\bwhat wifi\b",
            r"\bwhat wi-fi\b",
            r"\bwhich wifi\b",
            r"\bwhich wi-fi\b",
            r"\bwhat(?:'s| is) my ssid\b",
            r"\bis the internet working\b",
            r"\bis my internet working\b",
            r"\bis the internet down\b",
            r"\bam i connected to the internet\b",
            r"\bping\b",
        )
    )


def handle_network_command(command):
    if not command:
        return None

    c = command.lower().strip()

    if re.search(
        r"\bpublic ip\b",
        c,
    ):
        ip = _public_ip()

        if ip:
            return f"Your public IP is {ip}, Sir."

        return (
            "I could not retrieve your public IP, Sir."
        )

    if re.search(
        r"\b(?:wifi|wi-fi|ssid)\b",
        c,
    ):
        wifi = _wifi_name()

        if wifi:
            return (
                f"You are connected to "
                f"{wifi}, Sir."
            )

        return (
            "I could not determine your Wi-Fi network, Sir."
        )

    if re.search(
        r"\b(?:internet working|internet down|"
        r"connected to the internet)\b",
        c,
    ):
        if _internet_working():
            return "Yes, Sir. The internet is reachable."

        return "It appears the internet is unavailable, Sir."

    if re.search(
        r"\bping\b",
        c,
    ):
        match = re.search(
            r"\bping\s+(.+?)\s*$",
            c,
            re.IGNORECASE,
        )

        host = (
            match.group(1).strip(" .?")
            if match
            else "google.com"
        )

        if host in {"google", "google.com"}:
            host = "google.com"

        return _ping(host)

    ip = _local_ip()

    if ip:
        return f"Your local IP is {ip}, Sir."

    return (
        "I could not determine your local IP, Sir."
    )