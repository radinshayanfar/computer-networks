import struct

import DNSQuery
from Question import Question


class ResourceRecord:
    @staticmethod
    def from_bytes(byte_data, position):
        RR = ResourceRecord()
        RR.byte_data = byte_data

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
        RR.position = position
        position += RR.RDLENGTH

        return RR, position

    def get_data(self):
        if self.TYPE == Question.QTYPE_A:
            return self.__parse_a()
        elif self.TYPE == Question.QTYPE_AAAA:
            return self.__parse_aaaa()
        elif self.TYPE == Question.QTYPE_NS:
            return self.__parse_ns()
        elif self.TYPE == Question.QTYPE_CNAME:
            pass
        elif self.TYPE == Question.QTYPE_MX:
            return self.__parse_mx()
        elif self.TYPE == Question.QTYPE_TXT:
            return self.__parse_txt()

    def __parse_a(self):
        ip_address = struct.unpack("!BBBB", self.RDATA)
        return ".".join(map(str, ip_address))

    def __parse_ns(self):
        return DNSQuery.DNSQuery.bytes_to_name(self.byte_data, self.position)[0]

    def __parse_aaaa(self):
        ip_address = struct.unpack("!HHHHHHHH", self.RDATA)
        return ":".join([format(part, 'x') for part in ip_address])

    def __parse_txt(self):
        return self.RDATA.decode('ascii')

    def __parse_mx(self):
        return DNSQuery.DNSQuery.bytes_to_name(self.byte_data, self.position + 2)[0]
