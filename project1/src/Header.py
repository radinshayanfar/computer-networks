import struct


class Header:
    last_id = 0

    def __init__(self, questions_count):
        self.ID = Header.last_id

        self.QR = 0b0
        self.OPCODE = 0x0
        self.AA = 0b0
        self.TC = 0b0
        self.RD = 0b0
        self.RA = 0b0
        self.Z = 0b000
        self.RCODE = 0x0

        self.QDCOUNT = questions_count
        self.ANCOUNT = 0x00
        self.NSCOUNT = 0x00
        self.ARCOUNT = 0x00

        Header.last_id += 1

    def to_bytes(self):
        out = bytearray()
        options = struct.pack("!BB", ((self.QR & 0b1) << 7) | ((self.OPCODE & 0xF) << 3) | ((self.AA & 0b1) << 2) | (
                (self.TC & 0b1) << 1) | (self.RD & 0b1),
                              ((self.RA & 0b1) << 7) | ((self.Z & 0x7) << 4) | ((self.RCODE & 0xF)))

        out.extend(struct.pack("!H", self.ID))
        out.extend(options)
        out.extend(struct.pack("!H", self.QDCOUNT))
        out.extend(struct.pack("!H", self.ANCOUNT))
        out.extend(struct.pack("!H", self.NSCOUNT))
        out.extend(struct.pack("!H", self.ARCOUNT))

        return out
