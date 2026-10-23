from student_portal.grades import Grade
from student_portal.people import Funding, Student
from student_portal.scholarship import Scholarship, scholarship


def test_excellent_student_gets_increased_scholarship():
    student = Student(1, "Олена", "Коваль", [Grade("Python", 95)])
    assert scholarship(student) is Scholarship.INCREASED


def test_good_student_gets_regular_scholarship():
    student = Student(2, "Андрій", "Мельник", [Grade("Python", 80)])
    assert scholarship(student) is Scholarship.REGULAR


def test_contract_student_gets_none():
    student = Student(
        3, "Ірина", "Шевчук", [Grade("Python", 95)], funding=Funding.CONTRACT
    )
    assert scholarship(student) is Scholarship.NONE
