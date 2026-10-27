from datetime import date

from student_portal.grades import Grade
from student_portal.group import Group
from student_portal.people import Student
from student_portal.reminders import SUBJECT, ReminderReport, send_debt_reminders


class FakeMailer:
    def __init__(self):
        self.outbox = []

    def send(self, to, subject, body):
        self.outbox.append((to, subject, body))


def test_debtor_gets_reminder_with_deadline():
    group = Group("КН-11")
    group.add(Student(1, "Максим", "Бондар", [Grade("Python", 45)], "m@example.edu"))
    group.add(Student(2, "Олена", "Коваль", [Grade("Python", 95)], "o@example.edu"))
    mailer = FakeMailer()

    report = send_debt_reminders(group, mailer, today=date(2026, 11, 2))

    assert report == ReminderReport(sent=["m@example.edu"])
    [(to, subject, body)] = mailer.outbox
    assert (to, subject) == ("m@example.edu", SUBJECT)
    assert "Python" in body and "02.12.2026" in body
