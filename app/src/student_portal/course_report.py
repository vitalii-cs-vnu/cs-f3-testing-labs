"""Звіт про дисципліну групи (вимога Р-26)."""

from collections import Counter
from dataclasses import dataclass, field
from statistics import fmean

from student_portal.grades import ECTS_LETTERS, Grade
from student_portal.group import Group
from student_portal.people import Student

PASS_SCORE = 60


@dataclass(frozen=True)
class CourseReport:
    course: str
    graded: int = 0
    average: float | None = None
    pass_rate: int | None = None
    distribution: dict[str, int] = field(default_factory=dict)
    debtors: list[str] = field(default_factory=list)


def final_grade(student: Student, course: str) -> Grade | None:
    """Оцінка, що зараховується з дисципліни: остання за датою."""
    grades = student.grades_for(course)
    if not grades:
        return None
    return max(grades, key=lambda grade: grade.graded_on)


def course_report(group: Group, course: str) -> CourseReport:
    finals = {}
    for student in group:
        grade = final_grade(student, course)
        if grade is not None:
            finals[student.id] = grade
    if not finals:
        return CourseReport(course)
    scores = [grade.score for grade in finals.values()]
    passed = sum(1 for score in scores if score > PASS_SCORE)
    counts = Counter(grade.ects for grade in finals.values())
    return CourseReport(
        course=course,
        graded=len(finals),
        average=round(fmean(scores), 1),
        pass_rate=100 * passed // len(group),
        distribution={
            letter: counts[letter] for letter in ECTS_LETTERS if counts[letter]
        },
        debtors=[
            group.get(student_id).full_name
            for student_id, grade in sorted(finals.items())
            if grade.ects == "Fx"
        ],
    )


def format_report(report: CourseReport) -> str:
    """Текст звіту для консолі деканату."""
    lines = [f"Дисципліна: {report.course}"]
    if not report.graded:
        lines.append("Оцінок немає")
        return "\n".join(lines)
    average = f"{report.average:.1f}".replace(".", ",")
    passed = f"склали: {report.pass_rate} %"
    lines.append(f"Оцінок: {report.graded}, середній бал: {average}, {passed}")
    lines.append(
        ", ".join(f"{letter}: {n}" for letter, n in report.distribution.items())
    )
    lines.append(f"Боржники: {', '.join(report.debtors) or 'немає'}")
    return "\n".join(lines)
