"""Консоль деканату: імпорт студентів, статуси, стипендії, виправлення оцінок."""

from pathlib import Path

from student_portal.cli import DATA_FILE, format_average
from student_portal.corrections import correct_grade
from student_portal.exceptions import PortalError, StorageError
from student_portal.group import Group
from student_portal.importer import import_students
from student_portal.scholarship import scholarship
from student_portal.status import Event
from student_portal.storage import load_group, save_group

MENU = """
1 - список студентів (статус, фінансування, email)
2 - імпорт студентів з CSV
3 - змінити статус студента
4 - стипендії групи
5 - виправити оцінку
0 - зберегти і вийти"""

EVENTS = list(Event)


def list_students(group: Group) -> None:
    for s in group:
        print(
            f"{s.id:>3}  {s.full_name:<30}{s.status:<16}{s.funding:<20}{s.email or '-'}"
        )


def import_from_csv(group: Group) -> None:
    path = Path(input("Файл CSV: ").strip())
    print(f"Імпортовано студентів: {import_students(group, path)}")


def change_status(group: Group) -> None:
    student = group.get(int(input("ID студента: ")))
    print(f"Поточний статус: {student.status}")
    for number, event in enumerate(EVENTS, start=1):
        print(f"  {number} - {event}")
    event = EVENTS[int(input("Подія: ")) - 1]
    print(f"{student.full_name}: {student.change_status(event)}")


def show_scholarships(group: Group) -> None:
    for s in group:
        average = format_average(s.average())
        print(f"{s.id:>3}  {s.full_name:<30}{average:>6}  {scholarship(s)}")


def correct(group: Group) -> None:
    student = group.get(int(input("ID студента: ")))
    for number, grade in enumerate(student.grades, start=1):
        print(
            f"  {number} - {grade.course}: {grade.score} ({grade.graded_on:%d.%m.%Y})"
        )
    index = int(input("Номер оцінки: ")) - 1
    new_grade = correct_grade(student.grades[index], int(input("Нові бали: ")))
    student.grades[index] = new_grade
    print(
        f"{student.full_name}, {new_grade.course}: {new_grade.score} ({new_grade.ects})"
    )


ACTIONS = {
    "1": list_students,
    "2": import_from_csv,
    "3": change_status,
    "4": show_scholarships,
    "5": correct,
}


def run(group: Group) -> None:
    while True:
        print(MENU)
        choice = input("> ").strip()
        if choice == "0":
            return
        action = ACTIONS.get(choice)
        if action is None:
            print("Невідома команда")
            continue
        try:
            action(group)
        except (ValueError, IndexError) as error:
            print(f"Помилка введення: {error}")
        except PortalError as error:
            print(f"Помилка: {error}")


def main() -> None:
    try:
        group = load_group(DATA_FILE)
    except StorageError as error:
        raise SystemExit(f"Не вдалося завантажити дані: {error}") from error
    print(f"Консоль деканату. Група {group.name}: студентів - {len(group)}")
    run(group)
    save_group(group, DATA_FILE)
    print(f"Дані збережено у {DATA_FILE}")
