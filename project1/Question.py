import re
import struct


class Question:
    CLASS_IN = 1

    QTYPE_A = 1
    QTYPE_NS = 2
    QTYPE_CNAME = 5
    QTYPE_MX = 15
    QTYPE_TXT = 16
    QTYPE_AAAA = 28

    def __init__(self, qname, qtype, qclass):
        self.qname = qname
        self.qtype = qtype
        self.qclass = qclass

    def name_to_bytes(self):
        qname = self.qname

        valid_name = r"^([A-Za-z0-9\-]+\.)*[A-Za-z0-9\-]+\.?$"
        if not bool(re.match(valid_name, qname)):
            raise Exception("Entered QName is not valid name")

        if qname[-1] != '.':
            qname += '.'

        out = bytearray()
        labels = qname.split(".")
        for label in labels:
            size = len(label)
            out.extend(struct.pack("!B", size))
            out.extend(label.encode("ascii"))

        return out

    def to_bytes(self):
        out = bytearray()

        out.extend(self.name_to_bytes())
        out.extend(struct.pack("!H", self.qtype))
        out.extend(struct.pack("!H", self.qclass))

        return out
