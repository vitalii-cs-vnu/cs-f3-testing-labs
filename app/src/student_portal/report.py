"""Відомість успішності групи з дисципліни (вимога Р-11)."""

import csv
import logging
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from student_portal.group import Group

log = logging.getLogger(__name__)

REPORTS_DIR = Path("reports")


@dataclass
class ReportRow:
    student_id: int
    full_name: str
    email: str | None
    score: int | None
    ects: str
    passed: bool


def course_report(
    group: Group, course: str, exclude: list[int] = []
) -> list[ReportRow]:
    rows = []
    for student in group:
        if student.id in exclude:
            continue
        grades = student.grades_for(course)
        score = grades[0].score if grades else None
        if score == None:
            ects = "—"
        else:
            ects = grades[0].ects
        rows.append(
            ReportRow(
                student.id,
                student.full_name,
                student.email,
                score,
                ects,
                ects not in ("Fx", "—"),
            )
        )
    log.info("Відомість з дисципліни %s: %s", course, rows)
    return rows


def pass_rate(rows: list[ReportRow]) -> float:
    graded = [r for r in rows if r.score is not None]
    return sum(r.passed for r in graded) / len(graded) * 100


def export_csv(rows: list[ReportRow], name: str) -> Path:
    REPORTS_DIR.mkdir(exist_ok=True)
    path = REPORTS_DIR / f"{name}.csv"
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "ПІБ", "Email", "Бали", "ECTS", "Зараховано"])
        for r in rows:
            writer.writerow(
                [r.student_id, r.full_name, r.email, r.score, r.ects, r.passed]
            )
    return path


def export_pdf(path: Path) -> None:
    try:
        subprocess.run(
            f"soffice --headless --convert-to pdf --outdir {REPORTS_DIR} {path}",
            shell=True,
            check=True,
        )
    except Exception:
        pass
