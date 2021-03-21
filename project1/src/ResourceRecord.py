import struct

import DNSQuery


class ResourceRecord:
    @staticmethod
    def from_bytes(byte_data, position):
        RR = ResourceRecord()

        RR.NAME, position = DNSQuery.DNSQuery.bytes_to_name(byte_data, position)

        RR.TYPE = struct.unpack("!H", byte_data[position: position + 2])[0]
        position += 2

        RR.CLASS = struct.unpack("!H", byte_data[position: position + 2])[0]
        position += 2

        RR.TTL = struct.unpack("!I", byte_data[position: position + 4])[0]
        position += 4

        RR.RDLENGTH = struct.unpack("!H", byte_data[position: position + 2])[0]
        position += 2

        RR.RDATA = byte_data[position: position + RR.RDLENGTH]
        position += RR.RDLENGTH

        return RR, position
