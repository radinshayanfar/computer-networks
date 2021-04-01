import struct


class Header:
    last_id = 0

    @staticmethod
    def create_header(questions_count, recursion):
        header = Header()
        header.ID = Header.last_id

        header.QR = 0b0
        header.OPCODE = 0x0
        header.AA = 0b0
        header.TC = 0b0
        header.RD = 0b1 if recursion else 0b0
        header.RA = 0b0
        header.Z = 0b000
        header.RCODE = 0x0

        header.QDCOUNT = questions_count
        header.ANCOUNT = 0x00
        header.NSCOUNT = 0x00
        header.ARCOUNT = 0x00

        Header.last_id += 1

        return header

    @staticmethod
    def from_bytes(byte_data):
        header = Header()
        header.ID, options, header.QDCOUNT, header.ANCOUNT, header.NSCOUNT, header.ARCOUNT = struct.unpack("!HHHHHH",
                                                                                                           byte_data)

        header.QR = (options & 0x8000) >> 15
        header.OPCODE = (options & 0x3800) >> 11
        header.AA = (options & 0x0400) >> 10
        header.TC = (options & 0x0200) >> 9
        header.RD = (options & 0x0100) >> 8
        header.RA = (options & 0x0080) >> 7
        header.Z = (options & 0x0070) >> 4
        header.RCODE = options & 0x000F

        return header

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
