import pytest

from student_portal.exceptions import InvalidTransitionError
from student_portal.grades import Grade
from student_portal.people import Student
from student_portal.status import Event, Status


def test_new_student_is_active():
    assert Student(1, "Олена", "Коваль").status is Status.ACTIVE


def test_student_returns_from_leave():
    student = Student(1, "Олена", "Коваль")
    student.change_status(Event.TAKE_LEAVE)
    assert student.change_status(Event.RETURN) is Status.ACTIVE


def test_student_with_fx_cannot_graduate():
    student = Student(1, "Олена", "Коваль", [Grade("Python", 40)])
    with pytest.raises(InvalidTransitionError):
        student.change_status(Event.GRADUATE)
    assert student.status is Status.ACTIVE
