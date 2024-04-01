"""
Python implementation of MERG CBUS Protocol.
Current version comforms with CBUS Spec 6c.

Error defnitions.

Attributes:
    __version__ : The current version of the module.

"""


# ----- Exceptions -----------------------------------------------------------------------------------------------------
class CBusError(Exception):
    """
    Generic CBUS Error.
    All CBUS errors have a integer code that can be accessed using the :obj:`code` property of the exception.

    """

    def __init__(self, message: str, code: int) -> None:
        super().__init__(message)
        self._code = code

    @property
    def code(self):
        """Returns the exception error code."""
        return self._code


class CommadStationError(CBusError):
    """Command Station Error."""

    #: Error code for :class:`LocoStackFullError`.
    LOCO_STACK_FULL = 1
    #: Error code for :class:`LocoAddressTakenError`.
    LOCO_ADDRESS_TAKEN = 2
    #: Error code for :class:`SessionNotPresentError`.
    SESSION_NOT_PRESENT = 3
    #: Error code for :class:`ConsistEmptyError`.
    CONSIST_EMPTY = 4
    #: Error code for :class:`LocoNotFoundError`.
    LOCO_NOT_FOUND = 5
    #: Error code for :class:`CanBusError`.
    CAN_BUS_ERROR = 6
    #: Error code for :class:`InvalidRequestError`.
    INVALID_REQUEST = 7
    #: Error code for :class:`SessionCancelledError`.
    SESSION_CANCELLED = 8


class LocoStackFullError(CommadStationError):
    """Loco Stack Full Error. Error code :const:`CommadStationError.LOCO_STACK_FULL`."""

    def __init__(self) -> None:
        super().__init__("CS: Loco stack full.", self.LOCO_STACK_FULL)


class LocoAddressTakenError(CommadStationError):
    """Loco Address Taken Error. Error code :const:`CommadStationError.LOCO_ADDRESS_TAKEN`."""

    def __init__(self) -> None:
        super().__init__("CS: Loco address taken.", self.LOCO_ADDRESS_TAKEN)


class SessionNotPresentError(CommadStationError):
    """Session Not Present Error. Error code :const:`CommadStationError.SESSION_NOT_PRESENT`."""

    def __init__(self) -> None:
        super().__init__("CS: Session not present.", self.SESSION_NOT_PRESENT)


class ConsistEmptyError(CommadStationError):
    """Consist Empty Error. Error code :const:`CommadStationError.CONSIST_EMPTY`."""

    def __init__(self) -> None:
        super().__init__("CS: Consist empty.", self.CONSIST_EMPTY)


class LocoNotFoundError(CommadStationError):
    """Loco Not Found Error. Error code :const:`CommadStationError.LOCO_NOT_FOUND`."""

    def __init__(self) -> None:
        super().__init__("CS: Loco not found.", self.LOCO_NOT_FOUND)


class CanBusError(CommadStationError):
    """CAN Bus Error. Error code :const:`CommadStationError.CAN_BUS_ERROR`."""

    def __init__(self) -> None:
        super().__init__("CS: CAN bus error.", self.CAN_BUS_ERROR)


class InvalidRequestError(CommadStationError):
    """Invalid Request Error. Error code :const:`CommadStationError.INVALID_REQUEST`."""

    def __init__(self) -> None:
        super().__init__("CS: Invalid request.", self.INVALID_REQUEST)


class SessionCancelledError(CommadStationError):
    """Session Cancelled Error. Error code :const:`CommadStationError.SESSION_CANCELLED`."""

    def __init__(self) -> None:
        super().__init__("CS: Session cancelled.", self.SESSION_CANCELLED)


class ConfigError(CBusError):
    """Configuration Error."""

    #: Error code for :class:`CommandNotSupportedError`.
    COMMAND_NOT_SUPPORTED = 1
    #: Error code for :class:`NotInLearnModeError`.
    NOT_IN_LEARN_MODE = 2
    #: Error code for :class:`NotInSetupModeError`.
    NOT_IN_SETUP_MODE = 3
    #: Error code for :class:`TooManyEventsError`.
    TOO_MANY_EVENTS = 4
    #: Error code for :class:`InvalidEventVariableIndexError`.
    INVALID_EVENT_VARIABLE_INDEX = 6
    #: Error code for :class:`InvalidEventError`.
    INVALID_EVENT = 7
    #: Error code for :class:`InvalidParameterIndexError`.
    INVALID_PARAMETER_INDEX = 9
    #: Error code for :class:`InvalidNodeVariableIndexError`.
    INVALID_NODE_VARIABLE_INDEX = 10
    #: Error code for :class:`InvalidEventVariableValueError`.
    INVALID_EVENT_VARIABLE_VALUE = 11
    #: Error code for :class:`InvalidNodeVariableValueError`.
    INVALID_NODE_VARIABLE_VALUE = 12


class CommandNotSupportedError(ConfigError):
    """Command Not Supported Error. Error code :const:`CommadStationError.COMMAND_NOT_SUPPORTED`."""

    def __init__(self) -> None:
        super().__init__("CFG: Command not supported.", self.COMMAND_NOT_SUPPORTED)


class NotInLearnModeError(ConfigError):
    """Not In Learn Mode Error. Error code :const:`CommadStationError.NOT_IN_LEARN_MODE`."""

    def __init__(self) -> None:
        super().__init__("CFG: Not in learn mode.", self.NOT_IN_LEARN_MODE)


class NotInSetupModeError(ConfigError):
    """Not In Setup Mode Error. Error code :const:`CommadStationError.NOT_IN_SETUP_MODE`."""

    def __init__(self) -> None:
        super().__init__("CFG: Not in setup mode.", self.NOT_IN_SETUP_MODE)


class TooManyEventsError(ConfigError):
    """Too Many Events Error. Error code :const:`CommadStationError.TOO_MANY_EVENTS`."""

    def __init__(self) -> None:
        super().__init__("CFG: Too many events", self.TOO_MANY_EVENTS)


class InvalidEventError(ConfigError):
    """Invalid Event Error. Error code :const:`CommadStationError.INVALID_EVENT`."""

    def __init__(self) -> None:
        super().__init__("CFG: Invalid event.", self.INVALID_EVENT)


class InvalidEventVariableIndexError(ConfigError):
    """Invalid Event Variable Index Error. Error code :const:`CommadStationError.INVALID_EVENT_VARIABLE_INDEX`."""

    def __init__(self) -> None:
        super().__init__("CFG: Invalid event variable index.", self.INVALID_EVENT_VARIABLE_INDEX)


class InvalidEventVariableValueError(ConfigError):
    """Invalid Event Variable Value Error. Error code :const:`CommadStationError.INVALID_EVENT_VARIABLE_VALUE`."""

    def __init__(self) -> None:
        super().__init__("CFG: Invalid event variable value.", self.INVALID_EVENT_VARIABLE_VALUE)


class InvalidNodeVariableIndexError(ConfigError):
    """Invalid Node Variable Index Error. Error code :const:`CommadStationError.INVALID_NODE_VARIABLE_INDEX`."""

    def __init__(self) -> None:
        super().__init__("CFG: Invalid node variable index.", self.INVALID_NODE_VARIABLE_INDEX)


class InvalidNodeVariableValueError(ConfigError):
    """Invalid Node Variable Value Error. Error code :const:`CommadStationError.INVALID_NODE_VARIABLE_VALUE`."""

    def __init__(self) -> None:
        super().__init__("CFG: Invalid node variable value.", self.INVALID_NODE_VARIABLE_VALUE)


class InvalidParameterIndexError(ConfigError):
    """Invalid Parameter Index Error. Error code :const:`CommadStationError.INVALID_PARAMETER_INDEX`."""

    def __init__(self) -> None:
        super().__init__("CFG: Invalid parameter index.", self.INVALID_PARAMETER_INDEX)
