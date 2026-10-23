"""Виправлення оцінки (вимога Р-08)."""

from dataclasses import replace
from datetime import date, timedelta

from student_portal.exceptions import CorrectionPeriodError
from student_portal.grades import Grade

CORRECTION_DAYS = 14


def correct_grade(grade: Grade, new_score: int, today: date | None = None) -> Grade:
    """Повертає оцінку з новими балами, якщо строк виправлення не минув."""
    today = today or date.today()
    elapsed = (today - grade.graded_on).days
    if elapsed >= CORRECTION_DAYS:
        deadline = grade.graded_on + timedelta(days=CORRECTION_DAYS)
        raise CorrectionPeriodError(
            f"виправити оцінку можна до {deadline:%d.%m.%Y} включно"
        )
    return replace(grade, score=new_score)
