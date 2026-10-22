"""Учасники навчального процесу."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from statistics import fmean

from student_portal.grades import Grade


@dataclass
class Person(ABC):
    """Абстрактна особа: спільні дані студента і викладача."""

    id: int
    first_name: str
    last_name: str

    @property
    def full_name(self) -> str:
        return f"{self.last_name} {self.first_name}"

    @property
    @abstractmethod
    def role(self) -> str:
        """Назва ролі в системі."""

    def __str__(self) -> str:
        return f"{self.full_name} ({self.role})"


@dataclass
class Student(Person):
    """Студент і його оцінки."""

    grades: list[Grade] = field(default_factory=list)
    email: str | None = None

    @property
    def role(self) -> str:
        return "студент"

    def add_grade(self, grade: Grade) -> None:
        self.grades.append(grade)

    def grades_for(self, course: str) -> list[Grade]:
        return [grade for grade in self.grades if grade.course == course]

    def average(self) -> float | None:
        if not self.grades:
            return None
        return fmean(grade.score for grade in self.grades)


@dataclass
class Teacher(Person):
    """Викладач і дисципліни, які він веде."""

    courses: list[str] = field(default_factory=list)

    @property
    def role(self) -> str:
        return "викладач"
