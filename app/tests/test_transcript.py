"""Академічна довідка (вимога Р-28)."""

from datetime import date

from student_portal.grades import Grade
from student_portal.people import Student
from student_portal.transcript import transcript


def test_transcript_of_excellent_student():
    grades = [
        Grade("Python", 95, date(2026, 10, 1)),
        Grade("Бази даних", 90, date(2026, 10, 8)),
    ]
    student = Student(1, "Олена", "Коваль", grades)

    assert transcript(student, "КН-11").splitlines() == [
        "АКАДЕМІЧНА ДОВІДКА",
        "Студент: Коваль Олена (id 1), група КН-11",
        "Форма навчання: державне замовлення",
        "-" * 50,
        "Дисципліна             Кредити  Бали  ECTS  Оцінка",
        "Python                       5    95     A  відмінно",
        "Бази даних                   4    90     A  відмінно",
        "-" * 50,
        "Усього кредитів: 9",
        "Середній бал (зважений за кредитами): 92,8",
        "Боргів немає",
    ]


def test_transcript_without_grades():
    student = Student(5, "Софія", "Ткачук")

    assert transcript(student).splitlines()[-1] == "Оцінок немає"
