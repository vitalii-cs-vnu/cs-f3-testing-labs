"""Зберігання студентів у PostgreSQL (вимога Р-22)."""

import psycopg

from student_portal.exceptions import StudentNotFoundError
from student_portal.grades import Grade
from student_portal.people import Funding, Student
from student_portal.status import Status

SCHEMA = """
CREATE TABLE IF NOT EXISTS student (
    id         INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name  TEXT NOT NULL,
    email      TEXT,
    funding    TEXT NOT NULL,
    status     TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS grade (
    id         INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES student (id),
    course     TEXT NOT NULL,
    score      INTEGER NOT NULL CHECK (score BETWEEN 0 AND 100),
    graded_on  DATE NOT NULL
);
"""


class StudentRepository:
    """Студенти та їхні оцінки в базі даних.

    Репозиторій не фіксує транзакцій: commit і rollback виконує код,
    який відкрив з'єднання.
    """

    def __init__(self, connection: psycopg.Connection) -> None:
        self.connection = connection

    def create_schema(self) -> None:
        self.connection.execute(SCHEMA)

    def add(self, student: Student) -> None:
        self.connection.execute(
            "INSERT INTO student (id, first_name, last_name, email, funding, status)"
            " VALUES (%s, %s, %s, %s, %s, %s)",
            (
                student.id,
                student.first_name,
                student.last_name,
                student.email,
                student.funding.value,
                student.status.value,
            ),
        )
        for grade in student.grades:
            self._insert_grade(student.id, grade)

    def add_grade(self, student_id: int, grade: Grade) -> None:
        try:
            with self.connection.transaction():
                self._insert_grade(student_id, grade)
        except psycopg.errors.ForeignKeyViolation as error:
            raise StudentNotFoundError(f"студента з id={student_id} немає") from error

    def get(self, student_id: int) -> Student:
        row = self.connection.execute(
            "SELECT first_name, last_name, email, funding, status"
            " FROM student WHERE id = %s",
            (student_id,),
        ).fetchone()
        if row is None:
            raise StudentNotFoundError(f"студента з id={student_id} немає")
        first_name, last_name, email, funding, status = row
        grades = [
            Grade(course, score, graded_on)
            for course, score, graded_on in self.connection.execute(
                "SELECT course, score, graded_on FROM grade"
                " WHERE student_id = %s ORDER BY graded_on, id",
                (student_id,),
            )
        ]
        return Student(
            student_id,
            first_name,
            last_name,
            grades,
            email,
            funding=Funding(funding),
            status=Status(status),
        )

    def find(self, query: str) -> list[Student]:
        rows = self.connection.execute(
            "SELECT id FROM student WHERE last_name LIKE %s"
            " ORDER BY last_name, first_name",
            (f"%{query.strip()}%",),
        )
        return [self.get(student_id) for (student_id,) in rows.fetchall()]

    def _insert_grade(self, student_id: int, grade: Grade) -> None:
        self.connection.execute(
            "INSERT INTO grade (student_id, course, score, graded_on)"
            " VALUES (%s, %s, %s, %s)",
            (student_id, grade.course, grade.score, grade.graded_on),
        )
