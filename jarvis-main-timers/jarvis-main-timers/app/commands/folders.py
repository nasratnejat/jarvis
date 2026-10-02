import os
import subprocess


# ============================================================
# J.A.R.V.I.S. — FOLDER COMMANDS
# ============================================================


FOLDERS = {
    "downloads": os.path.join(
        os.path.expanduser("~"),
        "Downloads",
    ),

    "desktop": os.path.join(
        os.path.expanduser("~"),
        "Desktop",
    ),

    "documents": os.path.join(
        os.path.expanduser("~"),
        "Documents",
    ),

    "pictures": os.path.join(
        os.path.expanduser("~"),
        "Pictures",
    ),
}


# ============================================================
# NORMALIZATION
# ============================================================


def normalize(command):
    return command.lower().strip()


# ============================================================
# COMMAND DETECTION
# ============================================================


def is_folder_command(command):
    if not command:
        return False

    c = normalize(command)

    # Bare folder name
    if c in FOLDERS:
        return True

    # "open downloads"
    for name in FOLDERS:
        if c == f"open {name}":
            return True

    return False


# ============================================================
# OPEN FOLDER
# ============================================================


def handle_folder_command(command):
    if not command:
        return None

    c = normalize(command)

    target = None

    # --------------------------------------------------------
    # Bare folder
    # --------------------------------------------------------

    if c in FOLDERS:
        target = c

    # --------------------------------------------------------
    # "open <folder>"
    # --------------------------------------------------------

    if target is None:
        for name in FOLDERS:
            if c == f"open {name}":
                target = name
                break

    if target is None:
        return None

    # --------------------------------------------------------
    # Resolve actual Windows path
    # --------------------------------------------------------

    folder_path = FOLDERS[target]

    print(
        f"[FOLDER] Requested : {target}"
    )

    print(
        f"[FOLDER] Path      : {folder_path}"
    )

    # --------------------------------------------------------
    # Verify the folder exists
    # --------------------------------------------------------

    if not os.path.isdir(folder_path):
        print(
            f"[FOLDER ERROR] Folder does not exist: "
            f"{folder_path}"
        )

        return (
            f"I couldn't find your {target} folder, Sir."
        )

    # --------------------------------------------------------
    # Open using explorer.exe directly
    # --------------------------------------------------------

    try:
        subprocess.Popen(
            [
                "explorer.exe",
                folder_path,
            ],
            shell=False,
        )

        return (
            f"Opening {target.title()}, Sir."
        )

    except Exception as e:
        print(
            "[FOLDER ERROR]",
            repr(e),
        )

        return None