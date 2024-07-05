from dataclasses import dataclass
from models.segment import TheorySegment, QuestionSegment, MCQuestionSegment
from typing import Union


@dataclass
class LecturePath:
    module_name: str
    segments: list[Union[TheorySegment, QuestionSegment, MCQuestionSegment]]

    @staticmethod
    def from_dict(data: dict) -> "LecturePath":
        lecture_path = LecturePath(module_name=data.get("module_name"), segments=[])
        segments = data.get("segments")
        for segment in segments:
            if segment["type"] == "theory":
                theory_segment = TheorySegment(**segment)
                lecture_path.segments.append(theory_segment)
            elif segment["type"] == "question":
                question_segment = QuestionSegment.from_dict(segment)
                lecture_path.segments.append(question_segment)
        return lecture_path
