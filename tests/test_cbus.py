from unittest import TestCase, main

from cbus import MajorPriority, Message, MinorPriority, OpCode, Header, Frame, NetworkFrame


class TestStandardHeader(TestCase):
    def test_constructor(self):
        with self.assertRaises(ValueError):
            Header(MajorPriority.NORMAL, MinorPriority.NORMAL, can_id=256)
        sh = Header(MajorPriority.NORMAL, MinorPriority.NORMAL, can_id=127)
        self.assertIsNotNone(sh)

    def test_properties(self):
        sh = Header(MajorPriority.HIGH, MinorPriority.ABOVE_NORMAL, can_id=66)
        self.assertEqual(sh.major_priority, MajorPriority.HIGH)
        self.assertEqual(sh.minor_priority, MinorPriority.ABOVE_NORMAL)
        self.assertEqual(sh.can_id, 66)

    def test_str(self):
        sh = Header(MajorPriority.EMERGENCY, MinorPriority.HIGH, can_id=99)
        self.assertEqual(str(sh), "<MjPri=0><MinPri=0><CAN_ID=99>")

    def test_header(self):
        sh = Header(MajorPriority.HIGH, MinorPriority.LOW, can_id=33)
        self.assertEqual(sh.sidh, 0x74)
        self.assertEqual(sh.sidl, 0x20)
        self.assertEqual(sh.header, bytes([0x7420 >> 8, 0x7420 & 0xFF]))
        self.assertEqual(sh.can_header, bytes([(0x7420 >> 5) >> 8, (0x7420 >> 5) & 0xFF]))
        self.assertEqual(sh.ascii_header.upper(), b"7420")

    def test_parse(self):
        sh1 = Header.parse(bytes.fromhex("7420"))
        sh2 = Header(MajorPriority.HIGH, MinorPriority.LOW, can_id=33)
        self.assertEqual(sh1, sh2)


class TestOpcode(TestCase):
    def test_byte_count(self):
        self.assertEqual(OpCode.RESTP.byte_count, 0)
        self.assertEqual(OpCode.DBG1.byte_count, 1)
        self.assertEqual(OpCode.ALOC.byte_count, 2)
        self.assertEqual(OpCode.ERR.byte_count, 3)
        self.assertEqual(OpCode.ACON.byte_count, 4)
        self.assertEqual(OpCode.ACON1.byte_count, 5)
        self.assertEqual(OpCode.ACON2.byte_count, 6)
        self.assertEqual(OpCode.ACON3.byte_count, 7)


class TestMessage(TestCase):
    def test_constructor_and_str(self):
        m = Message(OpCode.ACK)
        self.assertEqual(str(m), "<ACK>")
        m = Message(OpCode.ACON, bytes([0x01, 0x10, 0x20, 0x30]))
        self.assertEqual(str(m), "<ACON><1><10><20><30>")
        with self.assertRaises(ValueError):
            Message(OpCode.ACK, bytes([0x01, 0x10, 0x20, 0x30]))

    def test_properties(self):
        m = Message(OpCode.ACK)
        self.assertEqual(m.opcode.name, "ACK")
        self.assertEqual(m.data, bytes(0))
        m = Message(OpCode.ACON, bytes([0x01, 0x10, 0x20, 0x30]))
        self.assertEqual(m.opcode, OpCode.ACON)
        self.assertEqual(m.data, bytes([0x01, 0x10, 0x20, 0x30]))
        m = Message(OpCode.ACK)
        self.assertEqual(m.message, bytes([OpCode.ACK.value]))
        m = Message(OpCode.ACON, bytes([0x01, 0x10, 0x20, 0x30]))
        self.assertEqual(m.message, bytes([OpCode.ACON.value, 0x01, 0x10, 0x20, 0x30]))

    def test_parse(self):
        m1 = Message.parse(bytes([0x99, 0x00, 0x00, 0x00, 0x12]))
        m2 = Message(OpCode.ASOF, bytes([0x00, 0x00, 0x00, 0x12]))
        self.assertEqual(m1, m2)

    def test_accessory_messages(self):
        m = Message.make_accesory_long_event_on(10, 64321)
        self.assertEqual(str(m), "<ACON><0><a><fb><41>")


class FrameTest(TestCase):
    def test_constructor(self):
        header = Header(MajorPriority.EMERGENCY, MinorPriority.ABOVE_NORMAL, can_id=0x55)
        msg = Message.make_accesory_long_event_on(10, 127)
        frame = Frame(header, msg)
        self.assertEqual(header, frame.header)
        self.assertEqual(msg, frame.message)

    def test_parse(self):
        header = Header(MajorPriority.EMERGENCY, MinorPriority.HIGH, can_id=127)
        msg0 = Message.make_request_engine_session(10)
        frame0 = Frame(header, msg0)
        s = b":S0FE0N40000A;"
        frames = NetworkFrame.parse(s)
        self.assertEqual(len(frames), 1)
        self.assertEqual(frames, [frame0])
        s = b":S0FE0N40000A;:S0FE0N2310;"
        msg1 = Message.make_session_keep_alive(16)
        frame1 = Frame(header, msg1)
        frames = NetworkFrame.parse(s)
        self.assertEqual(len(frames), 2)
        self.assertEqual(frames, [frame0, frame1])


if __name__ == "__main__":
    main()
