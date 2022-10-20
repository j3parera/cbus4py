from unittest import TestCase, main

import src.mpi_cbus.mpi_cbus as cbus


class TestStandardHeader(TestCase):
    def test_constructor(self):
        with self.assertRaises(ValueError):
            cbus.Header(cbus.MajorPriority.NORMAL, cbus.MinorPriority.NORMAL, can_id=256)
        sh = cbus.Header(cbus.MajorPriority.NORMAL, cbus.MinorPriority.NORMAL, can_id=127)
        self.assertIsNotNone(sh)

    def test_properties(self):
        sh = cbus.Header(cbus.MajorPriority.HIGH, cbus.MinorPriority.ABOVE_NORMAL, can_id=66)
        self.assertEqual(sh.major_priority, cbus.MajorPriority.HIGH)
        self.assertEqual(sh.minor_priority, cbus.MinorPriority.ABOVE_NORMAL)
        self.assertEqual(sh.can_id, 66)

    def test_str(self):
        sh = cbus.Header(cbus.MajorPriority.EMERGENCY, cbus.MinorPriority.HIGH, can_id=99)
        self.assertEqual(str(sh), "<0><0><99>")

    def test_header(self):
        sh = cbus.Header(cbus.MajorPriority.HIGH, cbus.MinorPriority.LOW, can_id=33)
        self.assertEqual(sh.sidh, 0x74)
        self.assertEqual(sh.sidl, 0x20)
        self.assertEqual(sh.header, bytes([0x7420 >> 8, 0x7420 & 0xFF]))
        self.assertEqual(sh.can_header, bytes([(0x7420 >> 5) >> 8, (0x7420 >> 5) & 0xFF]))
        self.assertEqual(sh.ascii_header.upper(), b"7420")

    def test_from_bytes(self):
        sh1 = cbus.Header.from_bytes(b"\x74\x20")
        sh2 = cbus.Header(cbus.MajorPriority.HIGH, cbus.MinorPriority.LOW, can_id=33)
        self.assertEqual(sh1, sh2)


class TestOpcode(TestCase):
    def test_byte_count(self):
        self.assertEqual(cbus.OpCode.RESTP.byte_count, 0)
        self.assertEqual(cbus.OpCode.DBG1.byte_count, 1)
        self.assertEqual(cbus.OpCode.ALOC.byte_count, 2)
        self.assertEqual(cbus.OpCode.ERR.byte_count, 3)
        self.assertEqual(cbus.OpCode.ACON.byte_count, 4)
        self.assertEqual(cbus.OpCode.ACON1.byte_count, 5)
        self.assertEqual(cbus.OpCode.ACON2.byte_count, 6)
        self.assertEqual(cbus.OpCode.ACON3.byte_count, 7)


class TestMessage(TestCase):
    def test_constructor_and_str(self):
        m = cbus.Message(cbus.OpCode.ACK)
        self.assertEqual(str(m), "<ACK>")
        m = cbus.Message(cbus.OpCode.ACON, bytes([0x01, 0x10, 0x20, 0x30]))
        self.assertEqual(str(m), "<ACON><1><10><20><30>")
        with self.assertRaises(ValueError):
            cbus.Message(cbus.OpCode.ACK, bytes([0x01, 0x10, 0x20, 0x30]))

    def test_properties(self):
        m = cbus.Message(cbus.OpCode.ACK)
        self.assertEqual(m.opcode.name, "ACK")
        self.assertEqual(m.data, bytes(0))
        m = cbus.Message(cbus.OpCode.ACON, bytes([0x01, 0x10, 0x20, 0x30]))
        self.assertEqual(m.opcode, cbus.OpCode.ACON)
        self.assertEqual(m.data, bytes([0x01, 0x10, 0x20, 0x30]))
        m = cbus.Message(cbus.OpCode.ACK)
        self.assertEqual(m.message, bytes([cbus.OpCode.ACK.value]))
        m = cbus.Message(cbus.OpCode.ACON, bytes([0x01, 0x10, 0x20, 0x30]))
        self.assertEqual(m.message, bytes([cbus.OpCode.ACON.value, 0x01, 0x10, 0x20, 0x30]))

    def test_parse(self):
        m1 = cbus.Message.parse(bytes([0x99, 0x00, 0x00, 0x00, 0x12]))
        m2 = cbus.Message(cbus.OpCode.ASOF, bytes([0x00, 0x00, 0x00, 0x12]))
        self.assertEqual(m1, m2)

    def test_accessory_messages(self):
        m = cbus.Message.make_accesory_long_event_on(10, 64321)
        self.assertEqual(str(m).casefold(), "<ACON><0><a><fb><41>".casefold())


class FrameTest(TestCase):
    def test_constructor(self):
        header = cbus.Header(cbus.MajorPriority.EMERGENCY, cbus.MinorPriority.ABOVE_NORMAL, can_id=0x55)
        msg = cbus.Message.make_accesory_long_event_on(10, 127)
        frame = cbus.Frame(header, msg)
        self.assertEqual(header, frame.header)
        self.assertEqual(msg, frame.message)

    def test_parse(self):
        header = cbus.Header(cbus.MajorPriority.EMERGENCY, cbus.MinorPriority.HIGH, can_id=127)
        msg0 = cbus.Message.make_request_engine_session(10)
        frame0 = cbus.Frame(header, msg0)
        s = b":S0FE0N40000A;"
        frames = cbus.Frame.parse_from_network(s)
        self.assertEqual(len(frames), 1)
        self.assertEqual(frames, [frame0])
        s = b":S0FE0N40000A;:S0FE0N2310;"
        msg1 = cbus.Message.make_session_keep_alive(16)
        frame1 = cbus.Frame(header, msg1)
        frames = cbus.Frame.parse_from_network(s)
        self.assertEqual(len(frames), 2)
        self.assertEqual(frames, [frame0, frame1])


if __name__ == "__main__":
    main()
