from __future__ import annotations

from typing import Any, Dict, Tuple

from frontend.commands.repository import COMMAND_NAME_TO_ID, CommandID


class CommandPipelineError(RuntimeError):
    """High-level pipeline error for command processing."""


def execute_robot_command(
    cmd_obj: Dict[str, Any],
    *,
    tracker,
    executor,
) -> Tuple[CommandState, str]:
    """
    Pure pipeline: resolve name -> id, enforce tracker policy, call executor.

    - LLM provides ONLY command name (no IDs).
    - Uses repository as the single source of truth for command ID resolution.
    - Tracker enforces: no duplicates + only one EXECUTING at a time.
    - When state becomes EXECUTED, tracker removes the command automatically.

    Returns: (CommandState, user_message)
    """

    cmd = cmd_obj.get("command")
    if not isinstance(cmd, dict):
        raise CommandPipelineError("Invalid robot_command: missing 'command' object")

    command_name = str(cmd.get("name", "")).strip().upper()
    if not command_name:
        raise CommandPipelineError("Invalid robot_command: missing command name")

    command_id_enum: CommandID | None = COMMAND_NAME_TO_ID.get(command_name)
    if command_id_enum is None:
        raise CommandPipelineError(f"Unknown or unsupported command name: {command_name}")

    command_id = command_id_enum.value  # e.g. "CMD_MOVE"

    user_message = str(cmd_obj.get("message", f"Ok, I am executing this {command_name}")).strip()

    try:
        tracker.enqueue(command_id, CommandState.EXECUTING)

        exec_result = executor.Execute(command_id, CommandState.EXECUTING)

        final_state = (
            CommandState.EXECUTION_ERROR
            if exec_result == CommandState.EXECUTION_ERROR
            else CommandState.EXECUTED
        )

        tracker.update(command_id, final_state)
        return final_state, user_message

    except CommandTrackingError as e:
        return CommandState.EXECUTION_ERROR, f"Execution blocked: {e}"

    except Exception as e:
        # best-effort mark error
        try:
            tracker.update(command_id, CommandState.EXECUTION_ERROR)
        except Exception:
            pass
        return CommandState.EXECUTION_ERROR, f"Execution error: {e}"
