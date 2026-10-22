from student_portal.grades import Grade, ects_grade
from student_portal.group import Group
from student_portal.people import Student
from student_portal.report import course_report, export_csv, pass_rate


def make_group():
    g = Group("КН-11")
    g.add(Student(1, "Олена", "Коваль", [Grade("Python", 95)]))
    g.add(Student(2, "Андрій", "Мельник", [Grade("Python", 45)]))
    return g


def test_ects_grade_after_refactoring():
    scores = (95, 85, 78, 70, 63, 30)
    assert [ects_grade(s) for s in scores] == ["A", "B", "C", "D", "E", "Fx"]


def test_course_report():
    rows = course_report(make_group(), "Python")
    assert len(rows) > 0


def test_pass_rate():
    assert pass_rate(course_report(make_group(), "Python")) == 50


def test_export_csv():
    path = export_csv(course_report(make_group(), "Python"), "test")
    assert path.exists()
