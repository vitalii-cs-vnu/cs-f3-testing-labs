import pytest

from student_portal.exceptions import DuplicateStudentError, StudentNotFoundError
from student_portal.grades import Grade
from student_portal.group import Group
from student_portal.people import Student


@pytest.fixture
def group():
    g = Group("КН-11")
    g.add(Student(1, "Олена", "Коваль", [Grade("Python", 95)]))
    g.add(Student(2, "Андрій", "Мельник", [Grade("Python", 61)]))
    g.add(Student(3, "Софія", "Ткачук"))
    return g


def test_ranking_puts_best_average_first_and_ungraded_last(group):
    assert [s.id for s in group.ranking()] == [1, 2, 3]


def test_duplicate_id_is_rejected(group):
    with pytest.raises(DuplicateStudentError):
        group.add(Student(1, "Іван", "Петренко"))


def test_missing_student_raises(group):
    with pytest.raises(StudentNotFoundError):
        group.get(42)


def test_find_ignores_case(group):
    assert [s.id for s in group.find("коваль")] == [1]
