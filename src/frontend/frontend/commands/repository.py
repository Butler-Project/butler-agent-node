from enum import Enum
from typing import Dict


class CommandID(Enum):
    """
    Canonical IDs for all executable high-level commands.
    These IDs are used by the CommandExecutor and tracker.
    """

    MOVE = "CMD_MOVE"
    TURN = "CMD_TURN"
    STOP = "CMD_STOP"
    SPEAK = "CMD_SPEAK"
    SCAN = "CMD_SCAN"
    PICKUP = "CMD_PICKUP"
    DROP = "CMD_DROP"
    STATUS = "CMD_STATUS"


# Map: LLM command name (string) -> CommandID
# This is the single source of truth for command resolution.
COMMAND_NAME_TO_ID: Dict[str, CommandID] = {
    "MOVE": CommandID.MOVE,
    "TURN": CommandID.TURN,
    "STOP": CommandID.STOP,
    "SPEAK": CommandID.SPEAK,
    "SCAN": CommandID.SCAN,
    "PICKUP": CommandID.PICKUP,
    "DROP": CommandID.DROP,
    "STATUS": CommandID.STATUS,
}
