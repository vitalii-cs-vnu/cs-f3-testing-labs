from datetime import date

from student_portal.course_report import course_report
from student_portal.grades import Grade
from student_portal.group import Group
from student_portal.people import Student


def test_report_for_course_where_everyone_passed():
    group = Group("КН-11")
    group.add(Student(1, "Олена", "Коваль", [Grade("Python", 95, date(2026, 10, 1))]))
    group.add(Student(2, "Андрій", "Мельник", [Grade("Python", 75, date(2026, 10, 2))]))

    report = course_report(group, "Python")

    assert report.graded == 2
    assert report.average == 85.0
    assert report.pass_rate == 100
    assert report.distribution == {"A": 1, "C": 1}
    assert report.debtors == []
