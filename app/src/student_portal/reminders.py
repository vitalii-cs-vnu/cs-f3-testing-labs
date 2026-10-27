"""Нагадування про академічну заборгованість (вимога Р-20)."""

from dataclasses import dataclass, field
from datetime import date, timedelta
from email.message import EmailMessage
from smtplib import SMTP
from typing import Protocol

from student_portal.group import Group
from student_portal.people import Student
from student_portal.status import Status

REPAY_DAYS = 30
SUBJECT = "Академічна заборгованість"


class Mailer(Protocol):
    def send(self, to: str, subject: str, body: str) -> None: ...


class SmtpMailer:
    """Надсилає листи через поштовий сервер університету."""

    def __init__(
        self,
        host: str,
        port: int = 587,
        sender: str = "dekanat@vnu.example.edu",
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.sender = sender
        self.username = username
        self.password = password

    def send(self, to: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = self.sender
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        with SMTP(self.host, self.port, timeout=10) as smtp:
            smtp.starttls()
            if self.username:
                smtp.login(self.username, self.password or "")
            smtp.send_message(message)


class ConsoleMailer:
    """Друкує листи замість надсилання: для роботи без поштового сервера."""

    def send(self, to: str, subject: str, body: str) -> None:
        print(f"Кому: {to}\nТема: {subject}\n\n{body}\n")


@dataclass
class ReminderReport:
    sent: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)


def debt_courses(student: Student) -> list[str]:
    return sorted({grade.course for grade in student.grades if grade.ects == "Fx"})


def reminder_text(student: Student, courses: list[str], deadline: date) -> str:
    return (
        f"Шановна (шановний) {student.first_name} {student.last_name}!\n"
        f"Ви маєте академічну заборгованість з дисциплін: {', '.join(courses)}.\n"
        f"Ліквідуйте її до {deadline:%d.%m.%Y}."
    )


def send_debt_reminders(
    group: Group, mailer: Mailer, today: date | None = None
) -> ReminderReport:
    """Надсилає нагадування боржникам групи і повертає звіт про розсилку."""
    deadline = (today or date.today()) + timedelta(days=REPAY_DAYS)
    report = ReminderReport()
    for student in group:
        if not student.email or student.status is Status.EXPELLED:
            continue
        courses = debt_courses(student)
        if not courses:
            continue
        for course in courses:
            mailer.send(
                student.email, SUBJECT, reminder_text(student, [course], deadline)
            )
        report.sent.append(student.email)
    return report
