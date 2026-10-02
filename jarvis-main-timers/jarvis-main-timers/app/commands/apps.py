import subprocess


APPS = {
    "chrome": "chrome",
    "firefox": "firefox",
    "edge": "msedge",
    "notepad": "notepad",
    "calc": "calc",
    "calculator": "calc",
    "terminal": "cmd",
    "powershell": "powershell",
    "task manager": "taskmgr",
    "settings": "ms-settings:",
    "code": "code",
    "vscode": "code",
    "teams": "teams",
    "discord": "discord",
    "steam": "steam",
    "obs": "obs64",
    "vlc": "vlc",
    "spotify": "spotify",
}


def normalize(command):
    return command.lower().strip()


def is_app_command(command):
    if not command:
        return False

    c = normalize(command)

    # Bare app name:
    # "notepad", "chrome", "discord"
    if c in APPS:
        return True

    # Explicit launch:
    # "open notepad", "start chrome"
    for name in APPS:
        if c == f"open {name}":
            return True

        if c == f"start {name}":
            return True

    return False


def handle_app_command(command):
    if not command:
        return None

    c = normalize(command)

    target = None

    # Bare name
    if c in APPS:
        target = c

    # open/start name
    if target is None:
        for name in APPS:
            if c in (
                f"open {name}",
                f"start {name}",
            ):
                target = name
                break

    if target is None:
        return None

    executable = APPS[target]

    try:
        subprocess.Popen(
            executable,
            shell=True
        )

        return f"Opening {target.title()}, Sir."

    except Exception as e:
        print("[APP ERROR]", repr(e))
        return None


def get_app_process_name(name):
    name = name.lower().strip()

    process_names = {
        "chrome": "chrome",
        "firefox": "firefox",
        "edge": "msedge",
        "notepad": "notepad",
        "calc": "CalculatorApp",
        "calculator": "CalculatorApp",
        "terminal": "WindowsTerminal",
        "powershell": "powershell",
        "task manager": "Taskmgr",
        "code": "Code",
        "vscode": "Code",
        "teams": "Teams",
        "discord": "Discord",
        "steam": "steam",
        "obs": "obs64",
        "vlc": "vlc",
        "spotify": "Spotify",
    }

    return process_names.get(name)