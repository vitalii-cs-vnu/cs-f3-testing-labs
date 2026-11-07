"""REST API системи управління студентами (вимоги Р-23, Р-27)."""

import asyncio
import csv
import io
import os
import random
import tempfile
from contextlib import suppress
from datetime import date
from pathlib import Path
from typing import Annotated

from fastapi import (
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field

from student_portal.exceptions import PortalError, StudentNotFoundError
from student_portal.grades import Grade
from student_portal.group import Group
from student_portal.importer import import_students
from student_portal.people import Student
from student_portal.storage import load_group

WEB = Path(__file__).parent / "web"

TOKENS = {
    "admin-token": "admin",
    "teacher-token": "teacher",
    "student-1-token": "student:1",
    "student-2-token": "student:2",
}

ERRORS = {
    401: {"description": "Немає токена або токен невідомий"},
    403: {"description": "Ролі бракує прав"},
}
NOT_FOUND = {404: {"description": "Студента не знайдено"}}
BAD_FILE = {400: {"description": "Файл не відповідає формату Р-19"}}
CONFLICT = {409: {"description": "Конфлікт з наявними даними"}}


class StudentIn(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    email: EmailStr


class StudentOut(StudentIn):
    id: int
    group: str
    average: float | None
    rank: int | None


class ImportResult(BaseModel):
    imported: int


class GradeIn(BaseModel):
    student_id: int
    course: str = Field(min_length=1, max_length=100)
    score: int = Field(ge=1, le=100)


class GradeOut(BaseModel):
    course: str
    score: int
    ects: str
    graded_on: date


class Me(BaseModel):
    role: str
    student_id: int | None


def create_app(group: Group) -> FastAPI:
    app = FastAPI(
        title="Система управління студентами",
        version="0.11.0",
        debug=os.environ.get("PORTAL_DEBUG", "1") == "1",
    )
    app.mount("/static", StaticFiles(directory=WEB), name="static")

    @app.middleware("http")
    async def slow_network(request: Request, call_next):
        """Випадкова затримка відповідей API до PORTAL_MAX_DELAY секунд."""
        delay = float(os.environ.get("PORTAL_MAX_DELAY", "0"))
        if delay and request.url.path.startswith("/api/"):
            await asyncio.sleep(random.uniform(0, delay))
        return await call_next(request)

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(WEB / "index.html")

    def role(authorization: Annotated[str | None, Header()] = None) -> str:
        token = (authorization or "").removeprefix("Bearer ")
        if token not in TOKENS:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "потрібна автентифікація")
        return TOKENS[token]

    def require(*allowed: str):
        def check(current: Annotated[str, Depends(role)]) -> str:
            if current not in allowed:
                raise HTTPException(status.HTTP_403_FORBIDDEN, "недостатньо прав")
            return current

        return check

    def find(student_id: int) -> Student:
        try:
            return group.get(student_id)
        except StudentNotFoundError:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "студента не знайдено"
            ) from None

    def ensure_unique(email: str) -> None:
        if any(s.email and s.email.casefold() == email.casefold() for s in group):
            raise HTTPException(status.HTTP_409_CONFLICT, "email уже використовується")

    def rank(s: Student) -> int | None:
        average = s.average()
        if average is None:
            return None
        return 1 + sum(1 for other in group if (other.average() or 0) > average)

    def out(s: Student) -> StudentOut:
        return StudentOut(
            id=s.id,
            first_name=s.first_name,
            last_name=s.last_name,
            email=s.email or "",
            group=group.name,
            average=s.average(),
            rank=rank(s),
        )

    def grade_out(g: Grade) -> GradeOut:
        return GradeOut(
            course=g.course, score=g.score, ects=g.ects, graded_on=g.graded_on
        )

    @app.get("/api/me", responses=ERRORS)
    def me(current: Annotated[str, Depends(role)]) -> Me:
        name, _, student_id = current.partition(":")
        return Me(role=name, student_id=int(student_id) if student_id else None)

    @app.get("/api/students", responses=ERRORS)
    def list_students(
        _: Annotated[str, Depends(require("admin", "teacher"))],
        group_name: Annotated[str | None, Query(alias="group")] = None,
    ) -> list[StudentOut]:
        if group_name is not None and group_name != group.name:
            return []
        return [out(s) for s in group]

    @app.post("/api/students", status_code=201, responses=ERRORS | CONFLICT)
    def create_student(
        data: StudentIn,
        response: Response,
        _: Annotated[str, Depends(require("admin"))],
    ) -> StudentOut:
        ensure_unique(data.email)
        student = Student(
            group.next_id(), data.first_name, data.last_name, email=data.email
        )
        group.add(student)
        response.headers["Location"] = f"/api/students/{student.id}"
        return out(student)

    @app.post("/api/students/import", status_code=201, responses=ERRORS | BAD_FILE)
    def import_csv(
        file: UploadFile, _: Annotated[str, Depends(require("admin"))]
    ) -> ImportResult:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "import.csv"
            path.write_bytes(file.file.read())
            try:
                count = import_students(group, path)
            except PortalError as error:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from None
        return ImportResult(imported=count)

    @app.get(
        "/api/export/students.csv",
        response_class=Response,
        responses=ERRORS | {200: {"content": {"text/csv": {}}}},
    )
    def export_csv(
        _: Annotated[str, Depends(require("admin", "teacher"))],
    ) -> Response:
        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
        writer.writerow(["id", "last_name", "first_name", "email", "average", "rank"])
        for s in group.ranking():
            row = out(s)
            average = "" if row.average is None else f"{row.average:.1f}"
            writer.writerow(
                [
                    row.id,
                    row.last_name,
                    row.first_name,
                    row.email,
                    average.replace(".", ","),
                    row.rank or "",
                ]
            )
        return Response(
            "\ufeff" + buffer.getvalue(),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="students.csv"'},
        )

    @app.get("/api/students/{student_id}", responses=ERRORS | NOT_FOUND)
    def get_student(
        student_id: int, current: Annotated[str, Depends(role)]
    ) -> StudentOut:
        if current not in ("admin", "teacher", f"student:{student_id}"):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "недостатньо прав")
        return out(find(student_id))

    @app.put("/api/students/{student_id}", responses=ERRORS | NOT_FOUND | CONFLICT)
    def update_student(
        student_id: int,
        data: StudentIn,
        _: Annotated[str, Depends(require("admin", "teacher"))],
    ) -> StudentOut:
        student = find(student_id)
        student.first_name = data.first_name
        student.last_name = data.last_name
        student.email = data.email
        return out(student)

    @app.delete(
        "/api/students/{student_id}", status_code=204, responses=ERRORS | NOT_FOUND
    )
    def delete_student(
        student_id: int, _: Annotated[str, Depends(require("admin"))]
    ) -> None:
        with suppress(StudentNotFoundError):
            group.remove(student_id)

    @app.post("/api/grades", status_code=201, responses=ERRORS | NOT_FOUND | CONFLICT)
    def add_grade(
        data: GradeIn, _: Annotated[str, Depends(require("teacher"))]
    ) -> GradeOut:
        student = find(data.student_id)
        try:
            grade = Grade(data.course, data.score)
            student.add_grade(grade)
        except PortalError as error:
            raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from None
        return grade_out(grade)

    @app.get("/api/students/{student_id}/grades", responses=ERRORS | NOT_FOUND)
    def list_grades(
        student_id: int, current: Annotated[str, Depends(role)]
    ) -> list[GradeOut]:
        if current not in ("admin", "teacher") and not current.startswith("student:"):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "недостатньо прав")
        grades = sorted(find(student_id).grades, key=lambda g: g.graded_on)
        return [grade_out(g) for g in grades]

    return app


def demo_app() -> FastAPI:
    """Застосунок з даними з файлу PORTAL_DATA (за замовчуванням data/group.json)."""
    return create_app(
        load_group(Path(os.environ.get("PORTAL_DATA", "data/group.json")))
    )


def main() -> None:
    import uvicorn

    uvicorn.run(
        "student_portal.api:demo_app",
        factory=True,
        host="127.0.0.1",
        port=int(os.environ.get("PORTAL_PORT", "8000")),
    )
