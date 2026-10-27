"""Інтеграційні тести StudentRepository на PostgreSQL у контейнері (потрібен Docker)."""

from datetime import date

import psycopg
import pytest

from student_portal.exceptions import StudentNotFoundError
from student_portal.grades import Grade
from student_portal.people import Funding, Student
from student_portal.repository import StudentRepository
from student_portal.status import Status


@pytest.fixture(scope="module")
def database_url():
    docker = pytest.importorskip("docker")
    from testcontainers.community.postgres import PostgresContainer

    try:
        container = PostgresContainer("postgres:18-alpine", driver=None).start()
    except docker.errors.DockerException as error:
        pytest.skip(f"Docker недоступний: {error}")
    yield container.get_connection_url()
    container.stop()


@pytest.fixture
def repository(database_url):
    with (
        psycopg.connect(database_url) as connection,
        connection.transaction(force_rollback=True),
    ):
        repository = StudentRepository(connection)
        repository.create_schema()
        yield repository


def test_saved_student_is_loaded_back(repository):
    student = Student(
        1,
        "Олена",
        "Коваль",
        [
            Grade("Python", 95, date(2026, 10, 1)),
            Grade("Бази даних", 88, date(2026, 10, 8)),
        ],
        "o.koval@example.edu",
        funding=Funding.CONTRACT,
        status=Status.ON_LEAVE,
    )

    repository.add(student)

    assert repository.get(1) == student


def test_unknown_student_is_not_found(repository):
    with pytest.raises(StudentNotFoundError):
        repository.get(42)


def test_grade_is_added_to_existing_student(repository):
    repository.add(Student(1, "Андрій", "Мельник"))

    repository.add_grade(1, Grade("Python", 72, date(2026, 10, 1)))

    assert repository.get(1).grades == [Grade("Python", 72, date(2026, 10, 1))]


def test_grade_for_unknown_student_is_rejected(repository):
    with pytest.raises(StudentNotFoundError):
        repository.add_grade(42, Grade("Python", 72))


def test_find_by_part_of_last_name(repository):
    repository.add(Student(1, "Олена", "Коваль"))
    repository.add(Student(2, "Андрій", "Мельник"))
    repository.add(Student(3, "Максим", "Бондар"))

    assert [s.last_name for s in repository.find("Кова")] == ["Коваль"]
    assert [s.last_name for s in repository.find("")] == ["Бондар", "Коваль", "Мельник"]
