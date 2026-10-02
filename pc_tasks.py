from app.core.router import router


def run_pc_task(command):
    """
    Run a PC command through the central router.

    Returns the result so JARVIS can speak it.
    """

    if not command:
        return None

    command = command.strip()

    if not command:
        return None

    try:

        print(
            f"[PC TASK] Processing: {command!r}"
        )

        result = router.dispatch(
            command
        )

        if result is not None:

            print(
                f"[PC TASK] Result: {result!r}"
            )

            return result

        print(
            f"[PC TASK] No PC command matched: "
            f"{command!r}"
        )

        return None

    except Exception as e:

        print(
            "[PC TASK ERROR]",
            repr(e),
        )

        return None


def get_state():

    return {
        "online": True,
        "command_registry": True,
        "commands": router.get_commands(),
    }


def get_available_commands():

    return router.get_commands()