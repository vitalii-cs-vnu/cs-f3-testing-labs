"""Імпорт студентів із CSV (вимога Р-19)."""

import csv
from pathlib import Path

from student_portal.exceptions import ImportFormatError, StorageError
from student_portal.group import Group
from student_portal.people import Funding, Student

FIELDS = ["last_name", "first_name", "email", "funding"]
FUNDING = {
    "": Funding.BUDGET,
    "бюджет": Funding.BUDGET,
    "контракт": Funding.CONTRACT,
}


def import_students(group: Group, path: Path) -> int:
    """Додає до групи студентів з файлу CSV і повертає їхню кількість."""
    try:
        file = path.open(encoding="utf-8", newline="")
    except FileNotFoundError as error:
        raise StorageError(f"файл не знайдено: {path}") from error
    with file:
        reader = csv.DictReader(file, delimiter=";")
        if reader.fieldnames != FIELDS:
            raise ImportFormatError(f"заголовок має бути: {';'.join(FIELDS)}")
        emails = {s.email for s in group if s.email}
        count = 0
        for row in reader:
            student = _parse_row(row, reader.line_num, group.next_id())
            if student.email in emails:
                raise ImportFormatError(
                    f"рядок {reader.line_num}: email {student.email} уже є в групі"
                )
            group.add(student)
            emails.add(student.email)
            count += 1
    return count


def _parse_row(row: dict[str, str | None], line: int, student_id: int) -> Student:
    last_name = row["last_name"] or ""
    first_name = row["first_name"] or ""
    email = (row["email"] or "").strip()
    if not last_name.strip() or not first_name.strip() or not email:
        raise ImportFormatError(f"рядок {line}: прізвище, ім’я та email обов’язкові")
    funding = FUNDING.get((row["funding"] or "").strip().lower())
    if funding is None:
        raise ImportFormatError(
            f"рядок {line}: фінансування має бути «бюджет» або «контракт»"
        )
    return Student(student_id, first_name, last_name, email=email, funding=funding)
