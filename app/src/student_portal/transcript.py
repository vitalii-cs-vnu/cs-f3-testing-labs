"""Академічна довідка студента (вимога Р-28).

Перенесено з системи деканату попередньої версії (2019) майже без змін.
"""

from student_portal.people import Funding

# кредити ЄКТС; інші дисципліни - 3 кредити
CREDITS = {"Python": 5, "Бази даних": 4, "Алгоритми": 5, "Веброзробка": 4}
W = 50


def transcript(student, group_name=""):  # noqa: C901 - технічний борг, див. Р-28
    s = ""
    s = s + "АКАДЕМІЧНА ДОВІДКА\n"
    s = s + "Студент: " + student.last_name + " " + student.first_name
    s = s + " (id " + str(student.id) + ")"
    if group_name != "":
        s = s + ", група " + group_name
    s = s + "\n"
    f = "контракт"
    if student.funding == Funding.BUDGET:
        f = "державне замовлення"
    s = s + "Форма навчання: " + f + "\n"
    if len(student.grades) == 0:
        s = s + "Оцінок немає\n"
        return s
    s = s + "-" * W + "\n"
    s = s + "Дисципліна".ljust(22) + "Кредити".rjust(8) + "Бали".rjust(6)
    s = s + "ECTS".rjust(6) + "  Оцінка\n"
    courses = []
    for g in student.grades:
        if g.course not in courses:
            courses.append(g.course)
    courses.sort()
    total = 0
    cr = 0
    debts = []
    for c in courses:
        # зараховується остання оцінка з дисципліни
        last = None
        for g in student.grades:
            if g.course == c and (last is None or g.graded_on >= last.graded_on):
                last = g
        k = CREDITS.get(c, 3)
        p = last.score
        if p >= 90:
            e = "A"
        elif p >= 82:
            e = "B"
        elif p >= 75:
            e = "C"
        elif p >= 67:
            e = "D"
        elif p >= 60:
            e = "E"
        elif p >= 35:
            e = "FX"
        else:
            e = "F"
        if p >= 90:
            n = "відмінно"
        elif p >= 74:
            n = "добре"
        elif p >= 60:
            n = "задовільно"
        else:
            n = "незадовільно"
            debts.append(c)
        total = total + p * k
        cr = cr + k
        s = s + c.ljust(22) + str(k).rjust(8) + str(p).rjust(6) + e.rjust(6)
        s = s + "  " + n + "\n"
    s = s + "-" * W + "\n"
    s = s + "Усього кредитів: " + str(cr) + "\n"
    avg = int(total / cr * 10 + 0.5) / 10
    s = s + "Середній бал (зважений за кредитами): " + str(avg).replace(".", ",")
    s = s + "\n"
    if len(debts) > 0:
        s = s + "Борги: " + ", ".join(debts) + "\n"
    else:
        s = s + "Боргів немає\n"
    return s
