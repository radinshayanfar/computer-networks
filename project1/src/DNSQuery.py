import struct

from Header import Header
from Question import Question


class DNSQuery:
    @staticmethod
    def create_query(questions):
        query = DNSQuery()
        query.header = Header.create_header(len(questions))

        query.questions = []
        for question in questions:
            query.questions.append(Question.create_question(**question))

        return query

    @staticmethod
    def bytes_to_name(byte_data, position):
        qname = ''
        while True:
            length = struct.unpack("!B", byte_data[position:position + 1])[0]
            position += 1

            if length == 0:  # root label
                break

            if length >> 14 == 0b11:  # a pointer
                offset = struct.unpack("!H", byte_data[position - 1: position + 1])[0] & 0x3FFF
                ptr_star, _ = DNSQuery.bytes_to_name(byte_data, offset)
                qname += ptr_star
                position += 1
                break

            qname += byte_data[position:position + length].decode('ascii') + '.'
            position += length

        return qname, position

    @staticmethod
    def from_bytes(byte_data):
        query = DNSQuery()
        query.header = Header.from_bytes(byte_data[:12])

        query.questions = []
        position = 12
        for i in range(query.header.QDCOUNT):
            question, position = Question.from_bytes(byte_data, position)
            query.questions.append(question)

        return query

    def to_bytes(self):
        out = bytearray()
        out.extend(self.header.to_bytes())

        for question in self.questions:
            out.extend(question.to_bytes())

        return out
