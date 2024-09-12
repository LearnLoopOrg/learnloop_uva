from dataclasses import dataclass


@dataclass
class TheorySegment:
    type: str
    title: str
    text: str
    image: str
    tag: str


@dataclass
class QuestionSegment:
    type: str
    question: str
    answer: dict
    image: str
    tag: str

    @classmethod
    def from_dict(self, data) -> "QuestionSegment":
        self.question = data.get("question")
        self.answer = data.get("answer")
        self.image = data.get("image")
        self.tag = data.get("tag")
        return self


@dataclass
class MCQuestionSegment:
    type: str
    question: str
    answers: dict
    image: str
    tag: str

    @classmethod
    def from_dict(self, data) -> "MCQuestionSegment":
        self.question = data.get("question")
        answers = data.get("answers")
        for answer in answers:
            self.answers.append(MCAnswer(**answer))
        self.image = data.get("image")
        self.tag = data.get("tag")
        return self


@dataclass
class MCAnswer:
    correct_answer: str
    wrong_answers: list[str]
