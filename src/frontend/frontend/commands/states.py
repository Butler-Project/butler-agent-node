from enum import Enum

class CommandState(Enum):
    EXECUTING = "EXECUTING"
    EXECUTED = "EXECUTED"
    EXECUTION_ERROR = "EXECUTION_ERROR"