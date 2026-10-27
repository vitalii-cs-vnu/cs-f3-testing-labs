from pathlib import Path

import pytest

from student_portal.exceptions import ImportFormatError
from student_portal.group import Group
from student_portal.importer import import_students
from student_portal.people import Funding, Student
from student_portal.status import Status

SAMPLE = Path(__file__).parent.parent / "data" / "students-import.csv"


@pytest.fixture
def group():
    g = Group("КН-11")
    g.add(Student(1, "Олена", "Коваль", email="o.koval@students.example.edu"))
    return g


def test_sample_file_adds_three_active_students(group):
    assert import_students(group, SAMPLE) == 3
    added = group.get(3)
    assert (added.last_name, added.funding, added.status) == (
        "Дем’яненко",
        Funding.CONTRACT,
        Status.ACTIVE,
    )


def test_empty_funding_means_budget(group):
    import_students(group, SAMPLE)
    assert group.get(4).funding is Funding.BUDGET


def test_wrong_header_is_rejected(group, tmp_path):
    path = tmp_path / "students.csv"
    path.write_text("прізвище;ім’я;email\n", encoding="utf-8")
    with pytest.raises(ImportFormatError, match="заголовок"):
        import_students(group, path)
