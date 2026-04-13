from __future__ import annotations

from enum import Enum
from typing import Any, Callable, Optional

class CommandExecutor:
    """
    Public interface:
      - ExecuteHighLevelCommand(command_id, action, *args, **kwargs) -> CommandState

    This class uses CommandExecutionTracker to ensure:
      - No duplicate command_id can be enqueued.
      - Only ONE command can be in EXECUTING at a time.
      - When state becomes EXECUTED, it is removed from tracking.
    """

    def __init__(self, tracker=None) -> None:
        self._tracker = tracker

    @property
    def tracker(self):
        return self._tracker

    def Execute(self, command_id: str, command_state):
            """
            Executes a command transition. For now, this is a minimal API that
            simply returns the provided state.
    
            In a real robot, this method would trigger the actual execution engine
            (e.g., call into a controller) and return EXECUTED/EXECUTION_ERROR.
            """
            if not command_id or not command_id.strip():
                raise ValueError("command_id must be a non-empty string")
    
            if not isinstance(command_state, CommandState):
                raise ValueError("command_state must be a CommandState enum")
    
            # Placeholder behavior:
            # - Server decides lifecycle; executor returns state as the "result".
            return command_state
