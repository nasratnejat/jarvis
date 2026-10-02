import ctypes
import re

from pycaw.pycaw import AudioUtilities


VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF

VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3

KEYEVENTF_KEYUP = 0x0002


def _press_key(key):
    try:
        ctypes.windll.user32.keybd_event(
            key,
            0,
            0,
            0,
        )

        ctypes.windll.user32.keybd_event(
            key,
            0,
            KEYEVENTF_KEYUP,
            0,
        )

        return True

    except Exception:
        return False


def _get_volume_interface():
    try:
        devices = AudioUtilities.GetSpeakers()

        if not devices:
            return None

        return devices.EndpointVolume

    except Exception:
        return None


def _get_volume():
    try:
        endpoint = _get_volume_interface()

        if endpoint is None:
            return None

        level = endpoint.GetMasterVolumeLevelScalar()

        return max(
            0.0,
            min(
                1.0,
                float(level),
            ),
        )

    except Exception:
        return None


def _set_volume(percent):
    try:
        percent = max(
            0.0,
            min(
                100.0,
                float(percent),
            ),
        )

        endpoint = _get_volume_interface()

        if endpoint is None:
            return False

        endpoint.SetMasterVolumeLevelScalar(
            percent / 100.0,
            None,
        )

        return True

    except Exception:
        return False


def _volume_response(percent):
    percent = round(percent)

    if percent <= 0:
        return "Volume set to 0%, Sir."

    if percent >= 100:
        return "Volume set to maximum, Sir."

    return f"Volume set to {percent}%, Sir."


def _adjust_volume(delta):
    current = _get_volume()

    if current is None:
        return (
            "I could not access the Windows "
            "volume control, Sir."
        )

    current_percent = current * 100

    new_percent = current_percent + delta

    new_percent = max(
        0,
        min(
            100,
            new_percent,
        ),
    )

    if not _set_volume(new_percent):
        return (
            "I could not change the Windows "
            "volume, Sir."
        )

    return _volume_response(new_percent)


def _extract_percentage(command):
    match = re.search(
        r"\b(\d+(?:\.\d+)?)\s*%",
        command,
        re.IGNORECASE,
    )

    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None

    match = re.search(
        r"\b(?:volume|set\s+volume(?:\s+to)?)\s+"
        r"(\d+(?:\.\d+)?)\b",
        command,
        re.IGNORECASE,
    )

    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None

    return None


def _handle_volume(command):
    c = command.lower().strip()

    # --------------------------------------------------------
    # MAXIMUM
    # --------------------------------------------------------

    if re.search(
        r"\b(?:volume\s+)?(?:max|maximum|full)\b",
        c,
        re.IGNORECASE,
    ):
        if _set_volume(100):
            return "Volume set to maximum, Sir."

        return "I could not set the volume, Sir."

    # --------------------------------------------------------
    # MINIMUM
    # --------------------------------------------------------

    if re.search(
        r"\b(?:volume\s+)?(?:min|minimum|zero)\b",
        c,
        re.IGNORECASE,
    ):
        if _set_volume(0):
            return "Volume set to minimum, Sir."

        return "I could not set the volume, Sir."

    # --------------------------------------------------------
    # SET VOLUME
    # --------------------------------------------------------

    if re.search(
        r"\b(?:set\s+)?volume\b",
        c,
        re.IGNORECASE,
    ):
        percent = _extract_percentage(c)

        if percent is not None:
            percent = max(
                0,
                min(
                    100,
                    percent,
                ),
            )

            if _set_volume(percent):
                return _volume_response(percent)

            return "I could not set the volume, Sir."

    # --------------------------------------------------------
    # INCREASE BY PERCENT
    # --------------------------------------------------------

    match = re.search(
        r"\b(?:increase|raise|boost|turn\s+up)\s+"
        r"(?:the\s+)?volume\s+"
        r"(?:by\s+)?"
        r"(\d+(?:\.\d+)?)\s*%",
        c,
        re.IGNORECASE,
    )

    if match:
        amount = float(match.group(1))

        return _adjust_volume(amount)

    # --------------------------------------------------------
    # DECREASE BY PERCENT
    # --------------------------------------------------------

    match = re.search(
        r"\b(?:decrease|lower|reduce|turn\s+down)\s+"
        r"(?:the\s+)?volume\s+"
        r"(?:by\s+)?"
        r"(\d+(?:\.\d+)?)\s*%",
        c,
        re.IGNORECASE,
    )

    if match:
        amount = float(match.group(1))

        return _adjust_volume(-amount)

    # --------------------------------------------------------
    # INCREASE DEFAULT
    # --------------------------------------------------------

    if re.search(
        r"\b(?:increase|raise|boost|turn\s+up)\s+"
        r"(?:the\s+)?volume\b",
        c,
        re.IGNORECASE,
    ):
        return _adjust_volume(10)

    # --------------------------------------------------------
    # DECREASE DEFAULT
    # --------------------------------------------------------

    if re.search(
        r"\b(?:decrease|lower|reduce|turn\s+down)\s+"
        r"(?:the\s+)?volume\b",
        c,
        re.IGNORECASE,
    ):
        return _adjust_volume(-10)

    # --------------------------------------------------------
    # VOLUME UP
    # --------------------------------------------------------

    if re.search(
        r"\bvolume\s+up\b",
        c,
        re.IGNORECASE,
    ):
        return _adjust_volume(10)

    # --------------------------------------------------------
    # VOLUME DOWN
    # --------------------------------------------------------

    if re.search(
        r"\bvolume\s+down\b",
        c,
        re.IGNORECASE,
    ):
        return _adjust_volume(-10)

    # --------------------------------------------------------
    # CURRENT VOLUME
    # --------------------------------------------------------

    if re.search(
        r"\b(?:what(?:'s| is)|check|show)\s+"
        r"(?:the\s+)?(?:current\s+)?volume\b",
        c,
        re.IGNORECASE,
    ):
        current = _get_volume()

        if current is None:
            return "I could not read the Windows volume, Sir."

        return (
            f"The current volume is "
            f"{round(current * 100)}%, Sir."
        )

    return None


def _handle_mute(command):
    c = command.lower().strip()

    if re.search(
        r"\b(?:unmute|sound\s+on|turn\s+sound\s+on)\b",
        c,
        re.IGNORECASE,
    ):
        if _press_key(VK_VOLUME_MUTE):
            return "Unmuted, Sir."

        return "I could not change the mute state, Sir."

    if re.search(
        r"\b(?:mute|silence|sound\s+off|"
        r"turn\s+sound\s+off)\b",
        c,
        re.IGNORECASE,
    ):
        if _press_key(VK_VOLUME_MUTE):
            return "Muted, Sir."

        return "I could not change the mute state, Sir."

    if re.search(
        r"\btoggle\s+(?:mute|sound)\b",
        c,
        re.IGNORECASE,
    ):
        if _press_key(VK_VOLUME_MUTE):
            return "Mute toggled, Sir."

        return "I could not change the mute state, Sir."

    return None


def _handle_media(command):
    c = command.lower().strip()

    # --------------------------------------------------------
    # PLAY / PAUSE
    # --------------------------------------------------------

    if re.search(
        r"^(?:play|pause|play\s+pause|"
        r"toggle\s+playback)$",
        c,
        re.IGNORECASE,
    ):
        if _press_key(VK_MEDIA_PLAY_PAUSE):
            return "Playback toggled, Sir."

        return "I could not control playback, Sir."

    # --------------------------------------------------------
    # NEXT TRACK
    # --------------------------------------------------------

    if re.search(
        r"^(?:next|next\s+track|next\s+song|"
        r"skip|skip\s+track|skip\s+song)$",
        c,
        re.IGNORECASE,
    ):
        if _press_key(VK_MEDIA_NEXT_TRACK):
            return "Skipping to the next track, Sir."

        return "I could not skip the track, Sir."

    # --------------------------------------------------------
    # PREVIOUS TRACK
    # --------------------------------------------------------

    if re.search(
        r"^(?:previous|previous\s+track|"
        r"previous\s+song|prev|prev\s+track|"
        r"back\s+track)$",
        c,
        re.IGNORECASE,
    ):
        if _press_key(VK_MEDIA_PREV_TRACK):
            return "Going to the previous track, Sir."

        return "I could not control the previous track, Sir."

    # --------------------------------------------------------
    # STOP
    # --------------------------------------------------------

    if re.search(
        r"^(?:stop|stop\s+(?:the\s+)?"
        r"(?:music|media|playback|track))$",
        c,
        re.IGNORECASE,
    ):
        if _press_key(VK_MEDIA_STOP):
            return "Media stopped, Sir."

        return "I could not stop the media, Sir."

    return None


def _is_external_media_request(command):
    """
    Prevent generic Windows media handling from stealing
    commands intended for YouTube or other services.
    """

    if not command:
        return False

    c = command.lower().strip()

    service_patterns = (
        r"\byoutube\b",
        r"\bspotify\b",
        r"\bapple\s+music\b",
        r"\bamazon\s+music\b",
        r"\bdeezer\b",
        r"\btidal\b",
    )

    return any(
        re.search(
            pattern,
            c,
            re.IGNORECASE,
        )
        for pattern in service_patterns
    )


def is_media_command(command):
    if not command:
        return False

    c = command.lower().strip()

    if not c:
        return False

    # Do not intercept service-specific commands.
    if _is_external_media_request(c):
        return False

    patterns = (
        r"\bvolume\b",
        r"\b(?:mute|unmute)\b",
        r"\b(?:sound\s+on|sound\s+off)\b",

        # Generic play/pause only.
        r"^(?:play|pause|play\s+pause|"
        r"toggle\s+playback)$",

        r"^(?:next|next\s+track|next\s+song)$",
        r"^(?:previous|previous\s+track|"
        r"previous\s+song|prev|prev\s+track)$",

        r"^(?:skip|skip\s+track|skip\s+song)$",

        r"^stop(?:\s+(?:music|media|"
        r"playback|track))?$",
    )

    return any(
        re.search(
            pattern,
            c,
            re.IGNORECASE,
        )
        for pattern in patterns
    )


def handle_media_command(command):
    if not command:
        return None

    result = _handle_volume(command)

    if result is not None:
        return result

    result = _handle_mute(command)

    if result is not None:
        return result

    result = _handle_media(command)

    if result is not None:
        return result

    return None