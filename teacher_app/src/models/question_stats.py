from dataclasses import dataclass


@dataclass
class QuestionStats:
    amount_of_tries: int
    total_score: float
    achieved_score: float

    # fuction to calculate percentage of correct answers
    @property
    def get_percentage_correct(self) -> float:
        return self.achieved_score / self.total_score * 100
