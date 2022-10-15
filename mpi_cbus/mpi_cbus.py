"""Python implementation of MERG CBUS Protocol.

Current version comforms with CBUS Spec 6c.

"""
import re
import struct
from enum import Enum, unique
from typing import Optional, Type


class CBusError(Exception):
    """
    Generic CBUS Error.

    Attributes:
        _code (int): Exception error code.

    """

    def __init__(self, code: int, msg: str) -> None:
        """
        Instance initialization.

        Args:
            code (int): Exception error code.
            msg (str): Human readable string describing the exception.
        """
        super().__init__(msg)
        self._code = code

    @property
    def code(self):
        """Returns the exception error code."""
        return self._code


class CommadStationError(CBusError):
    """
    Command Station Error.
    """

    LOCO_STACK_FULL = 1
    LOCO_ADDRESS_TAKEN = 2
    SESSION_NOT_PRESENT = 3
    CONSIST_EMPTY = 4
    LOCO_NOT_FOUND = 5
    CAN_BUS_ERROR = 6
    INVALID_REQUEST = 7
    SESSION_CANCELLED = 8


class ErrorLocoStackFull(CommadStationError):
    """
    Loco Stack Full Error.
    """

    def __init__(self) -> None:
        super().__init__(self.LOCO_STACK_FULL, "CS: Loco stack full")


class ErrorLocoAddressTaken(CommadStationError):
    def __init__(self) -> None:
        super().__init__(self.LOCO_ADDRESS_TAKEN, "CS: Loco address taken")


class ErrorSessionNotPresent(CommadStationError):
    def __init__(self) -> None:
        super().__init__(self.SESSION_NOT_PRESENT, "CS: Session not present")


class ErrorConsistEmpty(CommadStationError):
    def __init__(self) -> None:
        super().__init__(self.CONSIST_EMPTY, "CS: Consist empty")


class ErrorLocoNotFound(CommadStationError):
    def __init__(self) -> None:
        super().__init__(self.LOCO_NOT_FOUND, "CS: Loco not found")


class ErrorCanBusError(CommadStationError):
    def __init__(self) -> None:
        super().__init__(self.CAN_BUS_ERROR, "CS: CAN bus error")


class ErrorInvalidRequest(CommadStationError):
    def __init__(self) -> None:
        super().__init__(self.INVALID_REQUEST, "CS: Invalid request")


class ErrorSessionCancelled(CommadStationError):
    def __init__(self) -> None:
        super().__init__(self.SESSION_CANCELLED, "CS: Session cancelled")


class ConfigError(CBusError):

    COMMAND_NOT_SUPPORTED = 1
    NOT_IN_LEARN_MODE = 2
    NOT_IN_SETUP_MODE = 3
    TOO_MANY_EVENTS = 4
    INVALID_EVENT_VARIABLE_INDEX = 6
    INVALID_EVENT = 7
    INVALID_PARAMETER_INDEX = 9
    INVALID_NODE_VARIABLE_INDEX = 10
    INVALID_EVENT_VARIABLE_VALUE = 11
    INVALID_NODE_VARIABLE_VALUE = 12


class ErrorCommandNotSupported(ConfigError):
    def __init__(self) -> None:
        super().__init__(self.COMMAND_NOT_SUPPORTED, "CBUS: Command not supported")


class ErrorNotInLearnMode(ConfigError):
    def __init__(self) -> None:
        super().__init__(self.NOT_IN_LEARN_MODE, "CBUS: Not in learn mode")


class ErrorNotInSetupMode(ConfigError):
    def __init__(self) -> None:
        super().__init__(self.NOT_IN_SETUP_MODE, "CBUS: Not in setup mode")


class ErrorTooManyEvents(ConfigError):
    def __init__(self) -> None:
        super().__init__(self.TOO_MANY_EVENTS, "CBUS: Too many events")


class ErrorInvalidEvent(ConfigError):
    def __init__(self) -> None:
        super().__init__(self.INVALID_EVENT, "CBUS: Invalid event")


class ErrorInvalidEventVariableIndex(ConfigError):
    def __init__(self) -> None:
        super().__init__(self.INVALID_EVENT_VARIABLE_INDEX, "CBUS: Invalid event variable index")


class ErrorInvalidEventVariableValue(ConfigError):
    def __init__(self) -> None:
        super().__init__(self.INVALID_EVENT_VARIABLE_VALUE, "CBUS: Invalid event variable value")


class ErrorInvalidNodeVariableIndex(ConfigError):
    def __init__(self) -> None:
        super().__init__(self.INVALID_NODE_VARIABLE_INDEX, "CBUS: Invalid node variable index")


class ErrorInvalidNodeVariableValue(ConfigError):
    def __init__(self) -> None:
        super().__init__(self.INVALID_NODE_VARIABLE_VALUE, "CBUS: Invalid node variable value")


class ErrorInvalidParameterIndex(ConfigError):
    def __init__(self) -> None:
        super().__init__(self.INVALID_PARAMETER_INDEX, "CBUS: Invalid parameter index")


class MajorPriority(Enum):
    # bits 10-9 of CAN Header
    EMERGENCY = 0
    HIGH = 1
    NORMAL = 2


class MinorPriority(Enum):
    # bits 8-7 of CAN Header
    HIGH = 0
    ABOVE_NORMAL = 1
    NORMAL = 2
    LOW = 3


class Header:
    @classmethod
    def parse(cls: Type["Header"], data: bytes) -> "Header":
        """
        _summary_

        :param cls: _description_
        :type cls: Type[&quot;Header&quot;]
        :param data: _description_
        :type data: bytes
        :return: _description_
        :rtype: Header
        """
        sidh = data[0]
        sidl = data[1]
        maj_prio = MajorPriority((sidh >> 6) & 0x03)
        min_prio = MinorPriority((sidh >> 4) & 0x03)
        can_id = (sidh & 0x0F) << 3 | ((sidl >> 5) & 0x07)
        return cls(maj_prio, min_prio, can_id)

    @classmethod
    def make_minor_priority(cls: Type["Header"], min_prio: MinorPriority, can_id: int) -> "Header":
        return cls(MajorPriority.NORMAL, min_prio, can_id)

    def __init__(self, maj_prio: MajorPriority, min_prio: MinorPriority, can_id: int) -> None:
        if can_id > 127:
            raise ValueError("CBUS: CAN ID must be <= 127.")
        self._major_prio: MajorPriority = maj_prio
        self._minor_prio: MinorPriority = min_prio
        self._can_id: int = can_id
        self._make_header()

    def __str__(self) -> str:
        return f"<{self.major_priority.value}><{self.minor_priority.value}><{self.can_id}>"

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Header):
            return False
        return (self.sidl == other.sidl) and (self.sidh == other.sidh)

    @property
    def major_priority(self) -> MajorPriority:
        return self._major_prio

    @property
    def minor_priority(self) -> MinorPriority:
        return self._minor_prio

    @property
    def can_id(self) -> int:
        return self._can_id

    @property
    def sidl(self) -> int:
        return self._sidl

    @property
    def sidh(self) -> int:
        return self._sidh

    @property
    def header(self) -> bytes:
        return bytes([self._sidh, self._sidl])

    @property
    def ascii_header(self) -> bytes:
        return bytes(self.header.hex(), "ascii")

    @property
    def can_header(self) -> bytes:
        return bytes([self._sidh >> 5, ((self._sidh & 0x1F) << 3) | ((self._sidl >> 5) & 0x07)])

    def _make_header(self) -> None:
        self._sidh = self._major_prio.value << 6
        self._sidh |= self._minor_prio.value << 4
        self._sidh |= self._can_id >> 3
        self._sidl = (self._can_id & 0x7) << 5


class OpCodeKind(Enum):
    GENERAL = 0
    CONFIG = 1
    ACCESORY = 2
    DCC = 3


@unique
class OpCode(bytes, Enum):
    def __init__(self, *args) -> None:
        super().__init__()
        self._minor_prio: MinorPriority = args[1]
        self._kind: OpCodeKind = args[2]

    def __new__(cls, value, *_args) -> "OpCode":
        obj = bytes.__new__(cls, [value])
        obj._value_ = value
        return obj

    @property
    def minor_priority(self) -> MinorPriority:
        return self._minor_prio

    # GENERAL
    ACK = (0x00, MinorPriority.NORMAL, OpCodeKind.GENERAL)  # General acknowledgement - affirmative
    NAK = (0x01, MinorPriority.NORMAL, OpCodeKind.GENERAL)  # General acknowledgement - negative
    HLT = (0x02, MinorPriority.HIGH, OpCodeKind.GENERAL)  # CAN bus not available / busy
    BON = (0x03, MinorPriority.ABOVE_NORMAL, OpCodeKind.GENERAL)  # CAN bus available
    ARST = (0x07, MinorPriority.HIGH, OpCodeKind.GENERAL)  # System reset
    DBG1 = (0x30, MinorPriority.NORMAL, OpCodeKind.GENERAL)  # Debug. For development only
    EXTC = (0x3F, MinorPriority.LOW, OpCodeKind.GENERAL)  # Extended OPC with no added bytes
    EXTC1 = (0x5F, MinorPriority.LOW, OpCodeKind.GENERAL)  # Extended OPC with one added byte
    EXTC2 = (0x7F, MinorPriority.LOW, OpCodeKind.GENERAL)  # Extended OPC with two added bytes
    EXTC3 = (0x9F, MinorPriority.LOW, OpCodeKind.GENERAL)  # Extended OPC with three added bytes
    EXTC4 = (0xBF, MinorPriority.LOW, OpCodeKind.GENERAL)  # Extended OPC with four added bytes
    EXTC5 = (0xDF, MinorPriority.LOW, OpCodeKind.GENERAL)  # Extended OPC with five added bytes
    EXTC6 = (0xFF, MinorPriority.LOW, OpCodeKind.GENERAL)  # Extended OPC with six added bytes
    # CONFIG
    RSTAT = (0x0C, MinorPriority.NORMAL, OpCodeKind.CONFIG)  # Query status of command station
    QNN = (0x0D, MinorPriority.LOW, OpCodeKind.CONFIG)  # Query node status x
    RQNP = (0x10, MinorPriority.LOW, OpCodeKind.CONFIG)  # Request node parameters x
    RQMN = (0x11, MinorPriority.NORMAL, OpCodeKind.CONFIG)  # Request module name x
    SNN = (0x42, MinorPriority.LOW, OpCodeKind.CONFIG)  # Set node number (node in 'setup') x
    RQNN = (0x50, MinorPriority.LOW, OpCodeKind.CONFIG)  # Request node number x
    NNREL = (0x51, MinorPriority.LOW, OpCodeKind.CONFIG)  # Node number release x
    NNACK = (0x52, MinorPriority.LOW, OpCodeKind.CONFIG)  # Node number acknowledge (node in 'setup') x
    NNLRN = (0x53, MinorPriority.LOW, OpCodeKind.CONFIG)  # Set node into learn mode x
    NNULN = (0x54, MinorPriority.LOW, OpCodeKind.CONFIG)  # Release node from learn mode x
    NNCLR = (0x55, MinorPriority.LOW, OpCodeKind.CONFIG)  # Clear all events from a node x
    NNEVN = (0x56, MinorPriority.LOW, OpCodeKind.CONFIG)  # Read number of events available x
    NERD = (0x57, MinorPriority.LOW, OpCodeKind.CONFIG)  # Read back all events in a node x
    RQEVN = (0x58, MinorPriority.LOW, OpCodeKind.CONFIG)  # Read number of stored events in node x
    WRACK = (0x59, MinorPriority.LOW, OpCodeKind.CONFIG)  # Write acknowledge. (Handshake) x
    BOOTM = (0x5C, MinorPriority.LOW, OpCodeKind.CONFIG)  # Put node into 'bootloader' mode
    ENUM = (0x5D, MinorPriority.LOW, OpCodeKind.CONFIG)  # Force self enumeration of CAN_ID
    CMDERR = (0x6F, MinorPriority.LOW, OpCodeKind.CONFIG)  # Error message during configuration x
    EVNLF = (0x70, MinorPriority.LOW, OpCodeKind.CONFIG)  # Event space left x
    NVRD = (0x71, MinorPriority.LOW, OpCodeKind.CONFIG)  # Request read of node variable x
    NENRD = (0x72, MinorPriority.LOW, OpCodeKind.CONFIG)  # Request read of events by index x
    RQNPN = (0x73, MinorPriority.LOW, OpCodeKind.CONFIG)  # Request read of node parameter by index
    NUMEV = (0x74, MinorPriority.LOW, OpCodeKind.CONFIG)  # Number of events stored in node x
    CANID = (0x75, MinorPriority.LOW, OpCodeKind.CONFIG)  # Force a specific CAN_ID
    EVULN = (0x95, MinorPriority.LOW, OpCodeKind.CONFIG)  # Unlearn an event in learn mode x
    NVSET = (0x96, MinorPriority.LOW, OpCodeKind.CONFIG)  # Set a node variable x
    NVANS = (0x97, MinorPriority.LOW, OpCodeKind.CONFIG)  # Node variable value response
    PARAN = (0x9B, MinorPriority.LOW, OpCodeKind.CONFIG)  # Parameter readback by index
    REVAL = (0x9C, MinorPriority.LOW, OpCodeKind.CONFIG)  # Request read of event variable
    REQEV = (0xB2, MinorPriority.LOW, OpCodeKind.CONFIG)  # Read event variable in learn mode
    NEVAL = (0xB5, MinorPriority.LOW, OpCodeKind.CONFIG)  # Read of EV value response
    PNN = (0xB6, MinorPriority.LOW, OpCodeKind.CONFIG)  # Response to query node x
    EVLRN = (0xD2, MinorPriority.LOW, OpCodeKind.CONFIG)  # Teach event in learn mode x
    EVANS = (0xD3, MinorPriority.LOW, OpCodeKind.CONFIG)  # Response to request for EV value in learn mode x
    NAME = (0xE2, MinorPriority.LOW, OpCodeKind.CONFIG)  # Response to request for node name x
    PARAMS = (0xEF, MinorPriority.LOW, OpCodeKind.CONFIG)  # Response to request for node parameters (in setup)
    ENRSP = (0xF2, MinorPriority.LOW, OpCodeKind.CONFIG)  # Response to request to read node events x
    EVLRNI = (0xF5, MinorPriority.LOW, OpCodeKind.CONFIG)  # Teach event in learn mode using event indexing x
    # ACCESORY
    RQDAT = (0x5A, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Request node data event
    RQDDS = (0x5B, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Request device data (short)
    ACON = (0x90, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory ON event (long)
    ACOF = (0x91, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory OFFevent (long)
    AREQ = (0x92, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory status request (long)
    ARON = (0x93, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory response ON (long)
    AROF = (0x94, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory response OFF (long)
    ASON = (0x98, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory ON event (short)
    ASOF = (0x99, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory OFFevent (short)
    ASRQ = (0x9A, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory status request (short)
    ARSON = (0x9D, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory response ON (short)
    ARSOF = (0x9E, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory response OFF (short)
    ACON1 = (0xB0, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory ON event with one added byte (long)
    ACOF1 = (0xB1, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory OFF event with one added byte (long)
    ARON1 = (0xB3, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory response event ON with one added byte (long)
    AROF1 = (0xB4, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory response event OFF with one added byte (long)
    ASON1 = (0xB8, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory ON event with one added byte (short)
    ASOF1 = (0xB9, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory OFF event with one added byte (short)
    ARSON1 = (0xBD, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory response ON with one added data byte (short)
    ARSOF1 = (0xBE, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory response OFF with one added data byte (short)
    FCLK = (0xCF, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Fast clock
    ACON2 = (0xD0, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory ON event with two added bytes (long)
    ACOF2 = (0xD1, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory OFF event with two added bytes (long)
    ARON2 = (0xD4, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory response event ON with two added bytes (long)
    AROF2 = (0xD5, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory response event OFF with two added bytes (long)
    ASON2 = (0xD8, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory ON event with two added bytes (short)
    ASOF2 = (0xD9, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory OFF event with two added bytes (short)
    ARSON2 = (0xDD, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory response ON with two added data bytes (short)
    ARSOF2 = (0xDE, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory response OFF with two added data bytes (short)
    ACON3 = (0xF0, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory ON event with three added bytes (long)
    ACOF3 = (0xF1, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory OFF event with three added bytes (long)
    ARON3 = (0xF3, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory response event ON with three added bytes (long)
    AROF3 = (0xF4, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory response event OFF with three added bytes (long)
    ACDAT = (0xF6, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory node data event. 5 data bytes (long)
    ARDAT = (0xF7, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory node data response. 5 data bytes (long)
    ASON3 = (0xF8, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory ON event with three added bytes (short)
    ASOF3 = (0xF9, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory OFF event with three added bytes (short)
    DDES = (0xFA, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory node data event. 5 data bytes (short)
    DDRS = (0xFB, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory node data response. 5 data bytes (short)
    ARSON3 = (0xFD, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory response ON with 3 added data bytes (short)
    ARSOF3 = (0xFE, MinorPriority.LOW, OpCodeKind.ACCESORY)  # Accessory response OFF with 3 added data bytes (short)
    # DCC
    TOF = (0x04, MinorPriority.ABOVE_NORMAL, OpCodeKind.DCC)  # DCC track off
    TON = (0x05, MinorPriority.ABOVE_NORMAL, OpCodeKind.DCC)  # DCC Track on
    ESTOP = (0x06, MinorPriority.ABOVE_NORMAL, OpCodeKind.DCC)  # Emergency stop all
    RTOF = (0x08, MinorPriority.ABOVE_NORMAL, OpCodeKind.DCC)  # Request track off
    RTON = (0x09, MinorPriority.ABOVE_NORMAL, OpCodeKind.DCC)  # Request track on
    RESTP = (0x0A, MinorPriority.HIGH, OpCodeKind.DCC)  # Request emergency stop all
    KLOC = (0x21, MinorPriority.NORMAL, OpCodeKind.DCC)  # Release engine
    QLOC = (0x22, MinorPriority.NORMAL, OpCodeKind.DCC)  # Query engine
    DKEEP = (0x23, MinorPriority.NORMAL, OpCodeKind.DCC)  # Session keepalive from CAB
    RLOC = (0x40, MinorPriority.NORMAL, OpCodeKind.DCC)  # Request engine session
    QCON = (0x41, MinorPriority.NORMAL, OpCodeKind.DCC)  # Query consist
    ALOC = (0x43, MinorPriority.NORMAL, OpCodeKind.DCC)  # Allocate loco to ‘assignment or activity’
    STMOD = (0x44, MinorPriority.NORMAL, OpCodeKind.DCC)  # Set CAB session mode
    PCON = (0x45, MinorPriority.NORMAL, OpCodeKind.DCC)  # Set loco into consist (advanced)
    KCON = (0x46, MinorPriority.NORMAL, OpCodeKind.DCC)  # Remove loco from consist
    DSPD = (0x47, MinorPriority.NORMAL, OpCodeKind.DCC)  # Set engine speed / direction
    DFLG = (0x48, MinorPriority.NORMAL, OpCodeKind.DCC)  # Set engine (session) flags
    DFNON = (0x49, MinorPriority.NORMAL, OpCodeKind.DCC)  # Set engine function ON
    DFNOF = (0x4A, MinorPriority.NORMAL, OpCodeKind.DCC)  # Set engine function OFF
    SSTAT = (0x4C, MinorPriority.NORMAL, OpCodeKind.DCC)  # Service mode status
    DFUN = (0x60, MinorPriority.NORMAL, OpCodeKind.DCC)  # Set engine functions (DCC format)
    GLOC = (0x61, MinorPriority.NORMAL, OpCodeKind.DCC)  # Get engine session – used in dispatching
    ERR = (0x63, MinorPriority.NORMAL, OpCodeKind.DCC)  # Command station error report
    RDCC3 = (0x80, MinorPriority.NORMAL, OpCodeKind.DCC)  # Request 3 byte DCC packet.
    WCVO = (0x82, MinorPriority.NORMAL, OpCodeKind.DCC)  # Write CV in OPS mode (byte)
    WCVB = (0x83, MinorPriority.NORMAL, OpCodeKind.DCC)  # Write CV in OPS mode (bit)
    QCVS = (0x84, MinorPriority.NORMAL, OpCodeKind.DCC)  # Request read CV (service mode)
    PCVS = (0x85, MinorPriority.NORMAL, OpCodeKind.DCC)  # Report CV  (sevice mode)
    RDCC4 = (0xA0, MinorPriority.NORMAL, OpCodeKind.DCC)  # Request 4 byte DCC packet.
    WCVS = (0xA2, MinorPriority.NORMAL, OpCodeKind.DCC)  # Write CV in service mode
    RDCC5 = (0xC0, MinorPriority.NORMAL, OpCodeKind.DCC)  # Request 5 byte DCC packet.
    WCVOA = (0xC1, MinorPriority.NORMAL, OpCodeKind.DCC)  # Write CV in OPS mode by address
    RDCC6 = (0xE0, MinorPriority.NORMAL, OpCodeKind.DCC)  # Request 6 byte DCC packet.
    PLOC = (0xE1, MinorPriority.NORMAL, OpCodeKind.DCC)  # Engine report from command station
    STAT = (0xE3, MinorPriority.NORMAL, OpCodeKind.DCC)  # Command station status report

    @property
    def byte_count(self):
        return self.value >> 5

    @property
    def is_general(self):
        return self._kind == OpCodeKind.GENERAL

    @property
    def is_config(self):
        return self._kind == OpCodeKind.CONFIG

    @property
    def is_accessory(self):
        return self._kind == OpCodeKind.ACCESORY

    @property
    def is_dcc(self):
        return self._kind == OpCodeKind.DCC


class Message:
    @classmethod
    def parse(cls: Type["Message"], data: bytes) -> "Message":
        try:
            opcode = OpCode(data[0])
        except IndexError as exc:
            raise ValueError("CBUS: Invalid opcode") from exc
        return cls(opcode, data[1:])

    @classmethod
    def make_acknowledge(cls: Type["Message"]) -> "Message":
        return cls(OpCode.ACK)

    @classmethod
    def make_accesory_long_event_on(cls: Type["Message"], node: int, event: int) -> "Message":
        return cls(OpCode.ACON, struct.pack("!2H", node, event))

    @classmethod
    def make_accesory_long_event_off(cls: Type["Message"], node: int, event: int) -> "Message":
        return cls(OpCode.ACOF, struct.pack("!2H", node, event))

    @classmethod
    def make_command_station_error(cls: Type["Message"], loco_address: int, error_code: int) -> "Message":
        return cls(OpCode.ERR, struct.pack("!HB", loco_address, error_code))

    @classmethod
    def make_config_error(cls: Type["Message"], node_number: int, error_code: int) -> "Message":
        return cls(OpCode.CMDERR, struct.pack("!HB", node_number, error_code))

    @classmethod
    def make_session_keep_alive(cls: Type["Message"], session: int) -> "Message":
        return cls(OpCode.DKEEP, struct.pack("!B", session))

    @classmethod
    def make_request_engine_session(cls: Type["Message"], loco_address: int) -> "Message":
        return cls(OpCode.RLOC, struct.pack("!H", loco_address))

    @classmethod
    def make_release_engine(cls: Type["Message"], session: int) -> "Message":
        return cls(OpCode.KLOC, struct.pack("!B", session))

    @classmethod
    def make_engine_report(
        cls: Type["Message"],
        session: int,
        loco_address: int,
        speed: int,
        direction: int,
        fns: Optional[list[int]] = None,
    ) -> "Message":
        if fns is None:
            fns = [0, 0, 0]
        speed_dir = (speed & 0x7F) | (direction << 7)
        return cls(OpCode.PLOC, struct.pack("!BH4B", session, loco_address, speed_dir, *fns))

    @classmethod
    def make_command_station_report(
        cls: Type["Message"],
        node_number: int,
        cs_number: int,
        flags: int,
        rev_major: int,
        rev_minor: int,
        build: int = 0,
    ) -> "Message":
        return cls(OpCode.STAT, struct.pack("!H5B", node_number, cs_number, flags, rev_major, rev_minor, build))

    @classmethod
    def make_query_node_response(
        cls: Type["Message"], node_number: int, manufacturer_id: int, module_id: int, flags: int
    ) -> "Message":
        return cls(OpCode.PNN, struct.pack("!H3B", node_number, manufacturer_id, module_id, flags))

    @classmethod
    def make_node_params(cls: Type["Message"], params: list[int]) -> "Message":
        return cls(OpCode.PARAMS, struct.pack("!7B", *params[:7]))

    @classmethod
    def make_parameter(cls: Type["Message"], node_number: int, param_number: int, param_value: int) -> "Message":
        return cls(OpCode.PARAN, struct.pack("!H2B", node_number, param_number, param_value))

    @classmethod
    def make_read_node_var(cls: Type["Message"], node_number: int, nv_number: int, nv_value: int) -> "Message":
        return cls(OpCode.NVANS, struct.pack("!H2B", node_number, nv_number, nv_value))

    @classmethod
    def make_node_number_ack(cls: Type["Message"], node_number: int) -> "Message":
        return cls(OpCode.NNACK, struct.pack("!H", node_number))

    @classmethod
    def make_write_ack(cls: Type["Message"], node_number: int) -> "Message":
        return cls(OpCode.WRACK, struct.pack("!H", node_number))

    @classmethod
    def make_module_name(cls: Type["Message"], name: str) -> "Message":
        return cls(OpCode.NAME, struct.pack("!7s", name[:7].encode("ascii")))

    @classmethod
    def make_stored_event_num(cls: Type["Message"], node_number: int, ev_num: int) -> "Message":
        return cls(OpCode.NUMEV, struct.pack("!HB", node_number, ev_num))

    @classmethod
    def make_emergency_stop(cls: Type["Message"]) -> "Message":
        return cls(OpCode.ESTOP)

    def __init__(self, opcode: OpCode, data: Optional[bytes] = None) -> None:
        self._opcode: OpCode = opcode
        byte_cnt = opcode.byte_count
        if data is not None and len(data) != byte_cnt:
            raise ValueError(f"CBUS: Invalid data for message {opcode.name}")
        self._data: bytes = bytes(byte_cnt) if data is None else data

    def __str__(self) -> str:
        return f"<{self._opcode.name}>" + "".join([f"<{self._data[k]:X}>" for k in range(len(self._data))])

    @property
    def ascii(self) -> str:
        return f"{self._opcode.value:02X}" + "".join([f"{self._data[k]:02X}" for k in range(len(self._data))])

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Message):
            return False
        return (self._opcode == other._opcode) and (self._data == other._data)

    @property
    def opcode(self) -> OpCode:
        return self._opcode

    @property
    def data(self) -> bytes:
        return self._data

    @property
    def message(self) -> bytes:
        return bytes([self._opcode.value]) + bytes(self.data)

    @property
    def is_dcc(self) -> bool:
        return self._opcode.is_dcc

    @property
    def is_config(self) -> bool:
        return self._opcode.is_config

    @property
    def has_data(self) -> bool:
        return len(self._data) != 0

    def unpack_data(self, fmt: str, idx: int = 0) -> tuple[int, ...]:
        size = struct.calcsize(fmt)
        return struct.unpack(fmt, self._data[idx : idx + size])


class Frame:

    FORMAT = b":S([0-9a-fA-F]{4})([NR])([0-9a-fA-F]+);"
    format = re.compile(FORMAT)

    @classmethod
    def make_emergency_stop(cls: Type["Frame"], can_id: int) -> "Frame":
        return cls(Header.make_minor_priority(OpCode.ESTOP.minor_priority, can_id), Message.make_emergency_stop())

    @classmethod
    def make_engine_report(
        cls: Type["Frame"],
        can_id: int,
        session: int,
        loco_address: int,
        speed: int,
        direction: int,
        fns: Optional[list[int]] = None,
    ) -> "Frame":
        if fns is None:
            fns = [0, 0, 0]
        return cls(
            Header.make_minor_priority(OpCode.PLOC.minor_priority, can_id),
            Message.make_engine_report(session, loco_address, speed, direction, fns),
        )

    @classmethod
    def make_command_station_error(cls: Type["Frame"], can_id: int, loco_address: int, error_code: int) -> "Frame":
        return cls(
            Header.make_minor_priority(OpCode.ERR.minor_priority, can_id),
            Message.make_command_station_error(loco_address, error_code),
        )

    @classmethod
    def make_command_station_report(
        cls: Type["Frame"],
        can_id: int,
        node_number: int,
        cs_number: int,
        flags: int,
        rev_major: int,
        rev_minor: int,
        build: int = 0,
    ) -> "Frame":
        return cls(
            Header.make_minor_priority(OpCode.STAT.minor_priority, can_id),
            Message.make_command_station_report(node_number, cs_number, flags, rev_major, rev_minor, build),
        )

    @classmethod
    def make_query_node_response(
        cls: Type["Frame"], can_id: int, node_number: int, manufacturer_id: int, module_id: int, flags: int
    ) -> "Frame":
        return cls(
            Header.make_minor_priority(OpCode.PNN.minor_priority, can_id),
            Message.make_query_node_response(node_number, manufacturer_id, module_id, flags),
        )

    @classmethod
    def make_node_params(cls: Type["Frame"], can_id: int, params: list[int]) -> "Frame":
        return cls(Header.make_minor_priority(OpCode.PARAMS.minor_priority, can_id), Message.make_node_params(params))

    @classmethod
    def make_node_number_ack(cls: Type["Frame"], can_id: int, node_number: int) -> "Frame":
        return cls(
            Header.make_minor_priority(OpCode.NNACK.minor_priority, can_id), Message.make_node_number_ack(node_number)
        )

    @classmethod
    def make_parameter(
        cls: Type["Frame"], can_id: int, node_number: int, param_number: int, param_value: int
    ) -> "Frame":
        return cls(
            Header.make_minor_priority(OpCode.PARAN.minor_priority, can_id),
            Message.make_parameter(node_number, param_number, param_value),
        )

    @classmethod
    def make_read_node_var(cls: Type["Frame"], can_id: int, node_number: int, nv_number: int, nv_value: int) -> "Frame":
        return cls(
            Header.make_minor_priority(OpCode.NVANS.minor_priority, can_id),
            Message.make_read_node_var(node_number, nv_number, nv_value),
        )

    @classmethod
    def make_config_error(cls: Type["Frame"], can_id: int, node_number: int, error_code: int) -> "Frame":
        return cls(
            Header.make_minor_priority(OpCode.CMDERR.minor_priority, can_id),
            Message.make_config_error(node_number, error_code),
        )

    @classmethod
    def make_module_name(cls: Type["Frame"], can_id: int, name: str) -> "Frame":
        return cls(Header.make_minor_priority(OpCode.NAME.minor_priority, can_id), Message.make_module_name(name))

    @classmethod
    def make_write_ack(cls: Type["Frame"], can_id: int, node_number: int) -> "Frame":
        return cls(Header.make_minor_priority(OpCode.WRACK.minor_priority, can_id), Message.make_write_ack(node_number))

    @classmethod
    def make_stored_event_num(cls: Type["Frame"], can_id: int, node_number: int, ev_num: int) -> "Frame":
        return cls(
            Header.make_minor_priority(OpCode.NUMEV.minor_priority, can_id),
            Message.make_stored_event_num(node_number, ev_num),
        )

    @classmethod
    def make_void(cls: Type["Frame"], can_id: int) -> "Frame":
        return cls(Header(MajorPriority.NORMAL, MinorPriority.LOW, can_id), None)

    @classmethod
    def parse_from_network(cls: Type["Frame"], data: bytes) -> list["Frame"]:
        frames_spec = cls.format.findall(data)
        frames = list()
        for frame in frames_spec:
            header = Header.parse(bytes.fromhex(frame[0].decode("ascii")))
            msg = Message.parse(bytes.fromhex(frame[2].decode("ascii")))
            frames.append(cls(header, msg, rtr=(frame[1] == "R")))
        return frames

    def __init__(self, header: Header, msg: Optional[Message], rtr: bool = False) -> None:
        self._header: Header = header
        self._message: Optional[Message] = msg
        self._rtr = rtr

    def __str__(self) -> str:
        return str(self._header) + str(self._message)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Frame):
            return False
        return (self._header == other._header) and (self._message == other._message)

    @property
    def is_rtr(self) -> bool:
        return self._rtr

    @property
    def is_normal(self) -> bool:
        return not self.is_rtr

    @property
    def message(self) -> Optional[Message]:
        return self._message

    @property
    def header(self) -> Header:
        return self._header

    @property
    def net_encoded_frame(self) -> bytes:
        typ = "N" if self.is_normal else "R"
        msg = self.message.ascii if self.message is not None else ""
        return f":S{self._header.ascii_header.decode('ascii').upper()}{typ}{msg};".encode("ascii")
