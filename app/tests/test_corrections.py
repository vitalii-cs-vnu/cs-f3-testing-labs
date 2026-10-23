from datetime import date

import pytest

from student_portal.corrections import correct_grade
from student_portal.exceptions import CorrectionPeriodError
from student_portal.grades import Grade


def test_grade_is_corrected_within_period():
    grade = Grade("Python", 70, date(2026, 10, 1))
    corrected = correct_grade(grade, 75, today=date(2026, 10, 5))
    assert corrected.score == 75
    assert corrected.graded_on == grade.graded_on


def test_late_correction_is_rejected():
    grade = Grade("Python", 70, date(2026, 10, 1))
    with pytest.raises(CorrectionPeriodError):
        correct_grade(grade, 75, today=date(2026, 11, 1))
