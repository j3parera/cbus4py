"""Tests of cbus4py module."""
from unittest import TestCase, main

import cbus4py as cbus


class TestHeader(TestCase):
    """Tests of CBUS :obj:Header class."""

    def test_constructor(self):
        """Test constructor."""
        with self.assertRaises(ValueError):
            cbus.Header(cbus.MajorPriority.NORMAL, cbus.MinorPriority.NORMAL, can_id=256)
        header = cbus.Header(cbus.MajorPriority.NORMAL, cbus.MinorPriority.NORMAL, can_id=127)
        self.assertIsNotNone(header)

    def test_from_bytes(self):
        """Test factory from bytes."""
        header_1 = cbus.Header.from_bytes(b"\x74\x20")
        header_2 = cbus.Header(cbus.MajorPriority.HIGH, cbus.MinorPriority.LOW, can_id=33)
        self.assertEqual(header_1, header_2)

    def test_str(self):
        """Test string representation of instances."""
        header = cbus.Header(cbus.MajorPriority.EMERGENCY, cbus.MinorPriority.HIGH, can_id=99)
        self.assertEqual(str(header), "<0><0><99>")

    def test_properties(self):
        """Test properties of instances."""
        header = cbus.Header(cbus.MajorPriority.HIGH, cbus.MinorPriority.ABOVE_NORMAL, can_id=66)
        self.assertEqual(header.major_priority, cbus.MajorPriority.HIGH)
        self.assertEqual(header.minor_priority, cbus.MinorPriority.ABOVE_NORMAL)
        self.assertEqual(header.can_id, 66)

    def test_values(self):
        """Test values as registers, CAN and ASCII."""
        header = cbus.Header(cbus.MajorPriority.HIGH, cbus.MinorPriority.LOW, can_id=33)
        self.assertEqual(header.sidh, 0x74)
        self.assertEqual(header.sidl, 0x20)
        self.assertEqual(header.reg_header, bytes([0x7420 >> 8, 0x7420 & 0xFF]))
        self.assertEqual(header.can_header, bytes([(0x7420 >> 5) >> 8, (0x7420 >> 5) & 0xFF]))
        self.assertEqual(header.ascii_header.upper(), b"7420")


class TestOpcode(TestCase):
    """Test of CBUS :obj:OpCode class."""

    def test_byte_count(self):
        """Test byte count property."""
        self.assertEqual(cbus.OpCode.RESTP.byte_count, 0)
        self.assertEqual(cbus.OpCode.DBG1.byte_count, 1)
        self.assertEqual(cbus.OpCode.ALOC.byte_count, 2)
        self.assertEqual(cbus.OpCode.ERR.byte_count, 3)
        self.assertEqual(cbus.OpCode.ACON.byte_count, 4)
        self.assertEqual(cbus.OpCode.ACON1.byte_count, 5)
        self.assertEqual(cbus.OpCode.ACON2.byte_count, 6)
        self.assertEqual(cbus.OpCode.ACON3.byte_count, 7)


class TestMessage(TestCase):
    """Test of CBUS :obj:Message class."""

    def test_constructor_and_str(self):
        """Test constructor and string representation of instances."""
        msg = cbus.Message(cbus.OpCode.ACK)
        self.assertEqual(str(msg), "<ACK>")
        msg = cbus.Message(cbus.OpCode.ACON, bytes([0x01, 0x10, 0x20, 0x30]))
        self.assertEqual(str(msg), "<ACON><1><10><20><30>")
        with self.assertRaises(ValueError):
            cbus.Message(cbus.OpCode.ACK, bytes([0x01, 0x10, 0x20, 0x30]))

    def test_from_bytes(self):
        """Test factory from bytes."""
        msg_1 = cbus.Message.from_bytes(bytes([0x99, 0x00, 0x00, 0x00, 0x12]))
        msg_2 = cbus.Message(cbus.OpCode.ASOF, bytes([0x00, 0x00, 0x00, 0x12]))
        self.assertEqual(msg_1, msg_2)

    def test_accessory_messages(self):
        """Test factories."""
        msg = cbus.Message.make_accesory_long_event_on(10, 64321)
        self.assertEqual(str(msg).casefold(), "<ACON><0><a><fb><41>".casefold())

    def test_properties(self):
        """Test properties of instances."""
        msg = cbus.Message(cbus.OpCode.ACK)
        self.assertEqual(msg.opcode.name, "ACK")
        self.assertEqual(msg.data, bytes(0))
        msg = cbus.Message(cbus.OpCode.ACON, bytes([0x01, 0x10, 0x20, 0x30]))
        self.assertEqual(msg.opcode, cbus.OpCode.ACON)
        self.assertEqual(msg.data, bytes([0x01, 0x10, 0x20, 0x30]))
        msg = cbus.Message(cbus.OpCode.ACK)
        self.assertEqual(msg.message, bytes([cbus.OpCode.ACK.value]))
        msg = cbus.Message(cbus.OpCode.ACON, bytes([0x01, 0x10, 0x20, 0x30]))
        self.assertEqual(msg.message, bytes([cbus.OpCode.ACON.value, 0x01, 0x10, 0x20, 0x30]))


class FrameTest(TestCase):
    """Test of CBUS :obj:Frame class."""

    def test_constructor(self):
        """Test constructor."""
        header = cbus.Header(cbus.MajorPriority.EMERGENCY, cbus.MinorPriority.ABOVE_NORMAL, can_id=0x55)
        msg = cbus.Message.make_accesory_long_event_on(10, 127)
        frame = cbus.Frame(header, msg)
        self.assertEqual(header, frame.header)
        self.assertEqual(msg, frame.message)

    def test_from_network_bytes(self):
        """Test factory from network bytes."""
        header = cbus.Header(cbus.MajorPriority.EMERGENCY, cbus.MinorPriority.HIGH, can_id=127)
        msg_0 = cbus.Message.make_request_engine_session(10)
        frame_0 = cbus.Frame(header, msg_0)
        net_str = b":S0FE0N40000A;"
        frames = cbus.Frame.from_network_bytes(net_str)
        self.assertEqual(len(frames), 1)
        self.assertEqual(frames, [frame_0])
        net_str = b":S0FE0N40000A;:S0FE0N2310;"
        msg_1 = cbus.Message.make_session_keep_alive(16)
        frame_1 = cbus.Frame(header, msg_1)
        frames = cbus.Frame.from_network_bytes(net_str)
        self.assertEqual(len(frames), 2)
        self.assertEqual(frames, [frame_0, frame_1])


if __name__ == "__main__":
    main()
