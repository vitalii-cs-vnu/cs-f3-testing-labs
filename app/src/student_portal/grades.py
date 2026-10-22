"""Оцінки та шкала ECTS."""

from dataclasses import dataclass, field
from datetime import date

from student_portal.exceptions import InvalidGradeError

MIN_SCORE = 0
MAX_SCORE = 100
ECTS_LETTERS = ("A", "B", "C", "D", "E", "Fx")
ECTS_SCALE = ((90, "A"), (82, "B"), (75, "C"), (67, "D"), (60, "E"))


def ects_grade(points: int) -> str:
    """Переводить бали (0–100) у літеру шкали ECTS (вимога Р-05)."""
    if not MIN_SCORE <= points <= MAX_SCORE:
        raise InvalidGradeError(f"бали мають бути від {MIN_SCORE} до {MAX_SCORE}")
    for threshold, letter in ECTS_SCALE:
        if points > threshold:
            return letter
    return "Fx"


@dataclass(frozen=True, slots=True)
class Grade:
    """Оцінка з дисципліни за 100-бальною шкалою."""

    course: str
    score: int
    graded_on: date = field(default_factory=date.today)

    def __post_init__(self) -> None:
        if not MIN_SCORE <= self.score <= MAX_SCORE:
            raise InvalidGradeError(
                f"оцінка має бути від {MIN_SCORE} до {MAX_SCORE}, отримано {self.score}"
            )

    @property
    def ects(self) -> str:
        return ects_grade(self.score)
