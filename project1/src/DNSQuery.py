import struct

from Header import Header
from Question import Question
from ResourceRecord import ResourceRecord


class DNSQuery:
    @staticmethod
    def create_query(questions, recursion=False):
        query = DNSQuery()
        query.header = Header.create_header(len(questions), recursion)

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

            if length >> 6 == 0b11:  # a pointer
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
        position = 12

        query.questions = []
        for i in range(query.header.QDCOUNT):
            question, position = Question.from_bytes(byte_data, position)
            query.questions.append(question)

        query.answers = []
        for i in range(query.header.ANCOUNT):
            rr, position = ResourceRecord.from_bytes(byte_data, position)
            query.answers.append(rr)

        query.authorities = []
        for i in range(query.header.NSCOUNT):
            rr, position = ResourceRecord.from_bytes(byte_data, position)
            query.authorities.append(rr)

        query.additionals = []
        for i in range(query.header.ARCOUNT):
            rr, position = ResourceRecord.from_bytes(byte_data, position)
            query.additionals.append(rr)

        return query

    def to_bytes(self):
        out = bytearray()
        out.extend(self.header.to_bytes())

        for question in self.questions:
            out.extend(question.to_bytes())

        return out

    def __str__(self):
        out = ''

        out += 'Questions:\n' if len(self.questions) > 0 else ''
        for question in self.questions:
            out += f"\tName: {question.qname}\n"

        out += 'Answers:\n' if len(self.answers) > 0 else ''
        for answer in self.answers:
            out += f"\tName: {answer.NAME}, Answer: {answer.get_data()}\n"

        out += 'Authorities:\n' if len(self.authorities) > 0 else ''
        for auth in self.authorities:
            out += f"\tName: {auth.NAME}, Address: {auth.get_data()}\n"

        out += 'Additionals:\n' if len(self.additionals) > 0 else ''
        for additional in self.additionals:
            out += f"\tName: {additional.NAME}, Address: {additional.get_data()}\n"

        return out
