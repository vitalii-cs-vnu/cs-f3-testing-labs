"""Оцінки та шкала ECTS."""

from dataclasses import dataclass, field
from datetime import date

from student_portal.exceptions import InvalidGradeError

MIN_SCORE = 0
MAX_SCORE = 100
ECTS_LETTERS = ("A", "B", "C", "D", "E", "Fx")


def ects_grade(points: int) -> str:
    """Переводить бали (0–100) у літеру шкали ECTS (вимога Р-05)."""
    if points < MIN_SCORE or points > MAX_SCORE:
        raise InvalidGradeError(f"бали мають бути від {MIN_SCORE} до {MAX_SCORE}")
    if points >= 90:
        return "A"
    if points >= 82:
        return "B"
    if points >= 75:
        return "C"
    if points >= 67:
        return "D"
    if points >= 60:
        return "E"
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
