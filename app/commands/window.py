import re
import subprocess


# ============================================================
# J.A.R.V.I.S. — WINDOW COMMANDS
# ============================================================


WEBSITES = {
    "youtube",
    "google",
    "github",
    "gmail",
    "chatgpt",
    "reddit",
    "instagram",
    "facebook",
    "linkedin",
    "discord",
    "spotify",
    "netflix",
    "amazon",
    "drive",
    "docs",
    "sheets",
    "notion",
}


NEW_TAB_COMMANDS = {
    "new tab",
    "a new tab",
    "open new tab",
    "open a new tab",
    "create new tab",
    "create a new tab",
    "tab",
}


CLOSE_TAB_COMMANDS = {
    "close tab",
    "close the tab",
    "close current tab",
}


REFRESH_COMMANDS = {
    "refresh",
    "refresh page",
    "refresh the page",
    "refresh tab",
    "refresh the tab",
    "reload",
    "reload page",
    "reload the page",
}


CLOSE_WINDOW_COMMANDS = {
    "close window",
    "close the window",
    "close this window",
    "close current window",
}


# ============================================================
# NORMALIZATION
# ============================================================


def normalize(command):
    return command.lower().strip()


# ============================================================
# COMMAND DETECTION
# ============================================================


def is_window_command(command):
    if not command:
        return False

    c = normalize(command)

    if c in NEW_TAB_COMMANDS:
        return True

    if c in CLOSE_TAB_COMMANDS:
        return True

    if c in REFRESH_COMMANDS:
        return True

    if c in CLOSE_WINDOW_COMMANDS:
        return True

    # Websites
    if re.match(
        r"^close\s+(youtube|google|github|gmail|chatgpt|"
        r"reddit|instagram|facebook|linkedin|discord|spotify|"
        r"netflix|amazon|drive|docs|sheets|notion)$",
        c,
    ):
        return True

    # File Explorer folders
    if re.match(
        r"^close\s+(downloads|documents?|pictures?|photos?|"
        r"videos?|music|desktop|file explorer|explorer)"
        r"(?:\s+folder)?$",
        c,
    ):
        return True

    return False


# ============================================================
# POWERSHELL
# ============================================================


def run_powershell(script):
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script,
            ],
            capture_output=True,
            text=True,
            timeout=8,
        )

        if result.returncode != 0:
            print(
                "[WINDOW POWERSHELL ERROR]",
                result.stderr.strip(),
            )
            return False

        return True

    except Exception as e:
        print(
            "[WINDOW POWERSHELL ERROR]",
            repr(e),
        )
        return False


# ============================================================
# KEYBOARD HOTKEY
# ============================================================


def press_hotkey(*keys):
    key_string = "".join(keys)

    script = (
        "$wshell = New-Object -ComObject WScript.Shell; "
        f"$wshell.SendKeys('{key_string}')"
    )

    return run_powershell(script)


# ============================================================
# NEW TAB
# ============================================================


def open_new_tab():
    return press_hotkey("^t")


# ============================================================
# CLOSE BROWSER TAB
# ============================================================


def close_browser_tab():
    return press_hotkey("^w")


# ============================================================
# REFRESH PAGE
# ============================================================


def refresh_page():
    return press_hotkey("{F5}")


# ============================================================
# CLOSE ACTIVE WINDOW
# ============================================================


def close_window():
    return press_hotkey("%{F4}")


# ============================================================
# CLOSE WINDOW BY HWND
# ============================================================


def close_window_by_hwnd(hwnd):
    """
    Closes an exact Windows window using its HWND.

    This is used for File Explorer windows so that:
        close downloads

    closes Downloads specifically instead of whichever window
    happens to have keyboard focus.
    """

    try:
        hwnd = int(hwnd)

        # WM_CLOSE = 0x0010
        script = f"""
Add-Type @"
using System;
using System.Runtime.InteropServices;

public class JarvisWindow {{
    [DllImport("user32.dll")]
    public static extern bool PostMessage(
        IntPtr hWnd,
        uint Msg,
        IntPtr wParam,
        IntPtr lParam
    );
}}
"@

$result = [JarvisWindow]::PostMessage(
    [IntPtr]{hwnd},
    0x0010,
    [IntPtr]::Zero,
    [IntPtr]::Zero
)

if ($result) {{
    exit 0
}}
else {{
    exit 1
}}
"""

        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script,
            ],
            capture_output=True,
            text=True,
            timeout=8,
        )

        if result.returncode == 0:
            print(
                f"[WINDOW] Closed HWND {hwnd}"
            )
            return True

        print(
            "[WINDOW CLOSE ERROR]",
            result.stderr.strip(),
        )
        return False

    except Exception as e:
        print(
            "[WINDOW HANDLE ERROR]",
            repr(e),
        )
        return False


# ============================================================
# FIND EXPLORER WINDOW
# ============================================================


def find_explorer_window(target):
    """
    Finds the HWND of a File Explorer window.

    Windows reports Explorer windows as:
        CabinetWClass

    Examples:
        Downloads - File Explorer
        Documents - File Explorer
        JARVIS_BATCH1_V2 - File Explorer
    """

    target = target.lower().strip()

    target = re.sub(
        r"\s+folder$",
        "",
        target,
    ).strip()

    folder_titles = {
        "downloads": "downloads",
        "documents": "documents",
        "document": "documents",
        "pictures": "pictures",
        "picture": "pictures",
        "photos": "pictures",
        "videos": "videos",
        "video": "videos",
        "music": "music",
        "desktop": "desktop",
    }

    if target not in folder_titles:
        return None

    wanted = folder_titles[target]

    # Escape PowerShell single quotes safely.
    wanted_ps = wanted.replace("'", "''")

    script = f"""
Add-Type @"
using System;
using System.Text;
using System.Runtime.InteropServices;

public class JarvisEnumWindows {{
    public delegate bool EnumWindowsProc(
        IntPtr hWnd,
        IntPtr lParam
    );

    [DllImport("user32.dll")]
    public static extern bool EnumWindows(
        EnumWindowsProc lpEnumFunc,
        IntPtr lParam
    );

    [DllImport("user32.dll")]
    public static extern int GetWindowText(
        IntPtr hWnd,
        StringBuilder lpString,
        int nMaxCount
    );

    [DllImport("user32.dll")]
    public static extern int GetClassName(
        IntPtr hWnd,
        StringBuilder lpClassName,
        int nMaxCount
    );

    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(
        IntPtr hWnd
    );
}}
"@

$wanted = '{wanted_ps}'

[JarvisEnumWindows]::EnumWindows({{
    param($hWnd, $lParam)

    if (-not [JarvisEnumWindows]::IsWindowVisible($hWnd)) {{
        return $true
    }}

    $title = New-Object System.Text.StringBuilder 512
    $class = New-Object System.Text.StringBuilder 512

    [JarvisEnumWindows]::GetWindowText(
        $hWnd,
        $title,
        512
    ) | Out-Null

    [JarvisEnumWindows]::GetClassName(
        $hWnd,
        $class,
        512
    ) | Out-Null

    $windowClass = $class.ToString()
    $windowTitle = $title.ToString()

    if ($windowClass -eq 'CabinetWClass') {{
        if ($windowTitle -like "$wanted*") {{
            Write-Output $hWnd
            return $false
        }}
    }}

    return $true
}}, [IntPtr]::Zero)
"""

    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script,
            ],
            capture_output=True,
            text=True,
            timeout=8,
        )

        if result.returncode != 0:
            print(
                "[EXPLORER FIND ERROR]",
                result.stderr.strip(),
            )
            return None

        output = result.stdout.strip()

        if not output:
            return None

        # Take the last non-empty line and make sure it is numeric.
        lines = [
            line.strip()
            for line in output.splitlines()
            if line.strip()
        ]

        if not lines:
            return None

        hwnd_text = lines[-1]

        if not hwnd_text.isdigit():
            return None

        return int(hwnd_text)

    except Exception as e:
        print(
            "[EXPLORER FIND ERROR]",
            repr(e),
        )
        return None


# ============================================================
# CLOSE SPECIFIC EXPLORER FOLDER
# ============================================================


def close_explorer_folder(target):
    hwnd = find_explorer_window(target)

    if hwnd is None:
        print(
            f"[WINDOW] Explorer window not found: {target}"
        )
        return False

    print(
        f"[WINDOW] Found {target}: HWND={hwnd}"
    )

    return close_window_by_hwnd(hwnd)


# ============================================================
# CLOSE ANY EXPLORER WINDOW
# ============================================================


def close_explorer():
    """
    Finds the first visible CabinetWClass window and closes it.
    """

    script = r"""
Add-Type @"
using System;
using System.Text;
using System.Runtime.InteropServices;

public class JarvisExplorer {
    public delegate bool EnumWindowsProc(
        IntPtr hWnd,
        IntPtr lParam
    );

    [DllImport("user32.dll")]
    public static extern bool EnumWindows(
        EnumWindowsProc lpEnumFunc,
        IntPtr lParam
    );

    [DllImport("user32.dll")]
    public static extern int GetClassName(
        IntPtr hWnd,
        StringBuilder lpClassName,
        int nMaxCount
    );

    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(
        IntPtr hWnd
    );
}
"@

[JarvisExplorer]::EnumWindows({
    param($hWnd, $lParam)

    if (-not [JarvisExplorer]::IsWindowVisible($hWnd)) {
        return $true
    }

    $class = New-Object System.Text.StringBuilder 512

    [JarvisExplorer]::GetClassName(
        $hWnd,
        $class,
        512
    ) | Out-Null

    if ($class.ToString() -eq 'CabinetWClass') {
        Write-Output $hWnd
        return $false
    }

    return $true

}, [IntPtr]::Zero)
"""

    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script,
            ],
            capture_output=True,
            text=True,
            timeout=8,
        )

        if result.returncode != 0:
            return False

        lines = [
            line.strip()
            for line in result.stdout.splitlines()
            if line.strip()
        ]

        if not lines:
            return False

        hwnd = lines[-1]

        if not hwnd.isdigit():
            return False

        return close_window_by_hwnd(int(hwnd))

    except Exception as e:
        print(
            "[EXPLORER CLOSE ERROR]",
            repr(e),
        )
        return False


# ============================================================
# CLOSE WEBSITE
# ============================================================


def close_browser_target(target):
    target = target.lower().strip()

    if target not in WEBSITES:
        return False

    return close_browser_tab()


# ============================================================
# MAIN HANDLER
# ============================================================


def handle_window_command(command):
    if not command:
        return None

    c = normalize(command)

    # --------------------------------------------------------
    # New tab
    # --------------------------------------------------------

    if c in NEW_TAB_COMMANDS:
        if open_new_tab():
            return "Opening a new tab, Sir."

        return "I couldn't open a new tab, Sir."

    # --------------------------------------------------------
    # Close browser tab
    # --------------------------------------------------------

    if c in CLOSE_TAB_COMMANDS:
        if close_browser_tab():
            return "Closing the tab, Sir."

        return "I couldn't close the tab, Sir."

    # --------------------------------------------------------
    # Refresh
    # --------------------------------------------------------

    if c in REFRESH_COMMANDS:
        if refresh_page():
            return "Refreshing the page, Sir."

        return "I couldn't refresh the page, Sir."

    # --------------------------------------------------------
    # Generic active window
    # --------------------------------------------------------

    if c in CLOSE_WINDOW_COMMANDS:
        if close_window():
            return "Closing the window, Sir."

        return "I couldn't close the window, Sir."

    # --------------------------------------------------------
    # Specific close command
    # --------------------------------------------------------

    match = re.match(
        r"^close\s+(.+)$",
        c,
    )

    if not match:
        return None

    target = match.group(1).strip()

    # --------------------------------------------------------
    # Specific website
    # --------------------------------------------------------

    if close_browser_target(target):
        return f"Closing {target.title()}, Sir."

    # --------------------------------------------------------
    # Specific Explorer folder
    # --------------------------------------------------------

    if target in {
        "downloads",
        "documents",
        "document",
        "pictures",
        "picture",
        "photos",
        "videos",
        "video",
        "music",
        "desktop",
    }:
        if close_explorer_folder(target):
            return f"Closing {target.title()}, Sir."

        return f"I couldn't find the {target} window, Sir."

    # --------------------------------------------------------
    # File Explorer
    # --------------------------------------------------------

    if target in {
        "file explorer",
        "explorer",
    }:
        if close_explorer():
            return "Closing File Explorer, Sir."

        return "I couldn't find File Explorer, Sir."

    return None