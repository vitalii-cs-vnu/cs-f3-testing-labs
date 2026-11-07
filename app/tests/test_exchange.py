"""Обмін даними з деканатом (вимога Р-27): рейтинг, експорт і імпорт CSV."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from student_portal.api import create_app
from student_portal.grades import Grade
from student_portal.group import Group
from student_portal.people import Student

DATA = Path(__file__).parent.parent / "data"


@pytest.fixture
def client():
    group = Group("КН-11")
    group.add(Student(1, "Олена", "Коваль", [Grade("Python", 95)], email="o@ex.edu"))
    group.add(Student(2, "Андрій", "Мельник", [Grade("Python", 72)], email="a@ex.edu"))
    group.add(Student(3, "Софія", "Ткачук", email="s@ex.edu"))
    return TestClient(create_app(group))


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_list_contains_rank(client):
    response = client.get("/api/students", headers=auth("teacher-token"))

    assert [s["rank"] for s in response.json()] == [1, 2, None]


def test_export_is_csv_in_ranking_order(client):
    response = client.get("/api/export/students.csv", headers=auth("teacher-token"))

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    lines = response.content.decode("utf-8-sig").splitlines()
    assert lines == [
        "id;last_name;first_name;email;average;rank",
        "1;Коваль;Олена;o@ex.edu;95,0;1",
        "2;Мельник;Андрій;a@ex.edu;72,0;2",
        "3;Ткачук;Софія;s@ex.edu;;",
    ]


def test_admin_imports_students(client):
    with (DATA / "students-import.csv").open("rb") as file:
        response = client.post(
            "/api/students/import",
            files={"file": ("students.csv", file, "text/csv")},
            headers=auth("admin-token"),
        )

    assert response.status_code == 201
    assert response.json() == {"imported": 3}
    students = client.get("/api/students", headers=auth("admin-token")).json()
    assert students[-1]["last_name"] == "Лисенко"


def test_teacher_cannot_import(client):
    response = client.post(
        "/api/students/import",
        files={"file": ("students.csv", b"", "text/csv")},
        headers=auth("teacher-token"),
    )

    assert response.status_code == 403
