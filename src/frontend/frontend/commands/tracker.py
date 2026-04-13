from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Dict, List, Tuple

from frontend.commands.states import CommandState

class CommandTrackingError(RuntimeError):
    pass


@dataclass(frozen=True)
class TrackingEntry:
    command_id: str
    state: CommandState


class CommandExecutionTracker:
    """
    Tracks commands by (COMMAND_ID, EXECUTION_STATE).

    Rules:
      - No duplicate command_id can be enqueued.
      - Only ONE command may be in EXECUTING at a time.
      - When a command transitions to EXECUTED, it is removed from tracking.
    """

    def __init__(self) -> None:
        self._lock = RLock()
        self._entries: Dict[str, CommandState] = {}

    def enqueue(self, command_id: str, state: CommandState) -> None:
        """
        Enqueue a command into tracking.

        - Rejects duplicate command_id.
        - Rejects enqueueing EXECUTING if another command is already EXECUTING.
        """
        if not command_id or not command_id.strip():
            raise CommandTrackingError("command_id must be a non-empty string")

        with self._lock:
            if command_id in self._entries:
                raise CommandTrackingError(f"command_id '{command_id}' is already tracked")

            if state == CommandState.EXECUTING and self._has_executing_locked():
                existing = self._current_executing_locked()
                raise CommandTrackingError(
                    f"Cannot start '{command_id}' because '{existing}' is already EXECUTING"
                )

            self._entries[command_id] = state

            # If enqueued directly as EXECUTED, remove immediately (rare, but consistent)
            if state == CommandState.EXECUTED:
                self._entries.pop(command_id, None)

    def update(self, command_id: str, new_state: CommandState) -> None:
        """
        Update the state of a tracked command.

        - If new_state is EXECUTING and another command is EXECUTING, reject.
        - If new_state becomes EXECUTED, remove from tracking automatically.
        """
        with self._lock:
            if command_id not in self._entries:
                raise CommandTrackingError(f"command_id '{command_id}' is not tracked")

            if new_state == CommandState.EXECUTING:
                # Allow if it is the same command already executing; otherwise prevent concurrency
                current_executing = self._current_executing_locked()
                if current_executing is not None and current_executing != command_id:
                    raise CommandTrackingError(
                        f"Cannot set '{command_id}' to EXECUTING because '{current_executing}' is EXECUTING"
                    )

            if new_state == CommandState.EXECUTED:
                # Remove when executed
                self._entries.pop(command_id, None)
                return

            self._entries[command_id] = new_state

    def get(self, command_id: str) -> CommandState:
        """Return the current state for a tracked command."""
        with self._lock:
            if command_id not in self._entries:
                raise CommandTrackingError(f"command_id '{command_id}' is not tracked")
            return self._entries[command_id]

    def snapshot(self) -> List[Tuple[str, CommandState]]:
        """
        Returns a snapshot list of (COMMAND_ID, EXECUTION_STATE).
        """
        with self._lock:
            return list(self._entries.items())

    def _has_executing_locked(self) -> bool:
        return any(state == CommandState.EXECUTING for state in self._entries.values())

    def _current_executing_locked(self) -> str | None:
        for cid, state in self._entries.items():
            if state == CommandState.EXECUTING:
                return cid
        return None
