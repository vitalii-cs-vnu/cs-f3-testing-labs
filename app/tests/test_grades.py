import pytest

from student_portal.exceptions import InvalidGradeError
from student_portal.grades import Grade, ects_grade


def test_excellent_score_is_a():
    assert ects_grade(95) == "A"


def test_failing_score_is_fx():
    assert ects_grade(40) == "Fx"


def test_grade_exposes_ects_letter():
    assert Grade("Python", 85).ects == "B"


def test_score_above_maximum_is_rejected():
    with pytest.raises(InvalidGradeError):
        Grade("Python", 101)
