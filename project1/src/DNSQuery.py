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
    def from_bytes(byte_data):
        pass

    def to_bytes(self):
        out = bytearray()
        out.extend(self.header.to_bytes())

        for question in self.questions:
            out.extend(question.to_bytes())

        return out

