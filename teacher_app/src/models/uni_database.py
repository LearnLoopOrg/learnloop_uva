from dataclasses import dataclass
from typing import List


@dataclass
class Lecture:
    title: str
    description: str


@dataclass
class Course:
    title: str
    description: str
    lectures: List[Lecture]


@dataclass
class CourseCatalog:
    courses: List[Course]
