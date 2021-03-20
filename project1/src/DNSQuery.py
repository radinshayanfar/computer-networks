from Header import Header
from Question import Question


class DNSQuery:
    def __init__(self, questions):
        self.header = Header(len(questions))

        self.questions = []
        for question in questions:
            self.questions.append(Question(**question))

    def to_bytes(self):
        out = bytearray()
        out.extend(self.header.to_bytes())

        for question in self.questions:
            out.extend(question.to_bytes())

        return out
