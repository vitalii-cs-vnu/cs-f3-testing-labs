"""Академічна стипендія (вимога Р-17)."""

from enum import StrEnum

from student_portal.people import Funding, Student

REGULAR_THRESHOLD = 75
INCREASED_THRESHOLD = 90


class Scholarship(StrEnum):
    NONE = "не призначено"
    REGULAR = "звичайна"
    INCREASED = "підвищена"


def scholarship(student: Student) -> Scholarship:
    """Визначає стипендію студента за результатами семестру."""
    if student.funding is not Funding.BUDGET:
        return Scholarship.NONE
    average = student.average()
    if average is None:
        return Scholarship.NONE
    if average >= INCREASED_THRESHOLD:
        return Scholarship.INCREASED
    if student.has_debts() or average < REGULAR_THRESHOLD:
        return Scholarship.NONE
    return Scholarship.REGULAR
