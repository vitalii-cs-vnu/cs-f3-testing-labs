"use strict";
// Вебінтерфейс системи управління студентами (вимоги Р-25, Р-27)

const ROLES = { admin: "Адміністратор", teacher: "Викладач" };
const $ = (id) => document.getElementById(id);
let students = [];
let order = null; // сортування за середнім балом: null, "desc", "asc"

function token() {
  return sessionStorage.getItem("token");
}

async function api(method, path, body) {
  const response = await fetch(path, {
    method,
    headers: {
      Authorization: `Bearer ${token()}`,
      ...(body ? { "Content-Type": "application/json" } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = response.status === 204 ? null : await response.json();
  return { status: response.status, data };
}

function say(text) {
  $("error").textContent = "";
  $("message").textContent = text;
}

function fail(text) {
  $("message").textContent = "";
  $("error").textContent = text;
}

function formatAverage(average) {
  return average === null
    ? "-"
    : average.toLocaleString("uk-UA", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
}

function show(view) {
  for (const id of ["login-view", "list-view", "card-view"]) {
    $(id).hidden = id !== view;
  }
}

function cell(text) {
  const td = document.createElement("td");
  td.textContent = text;
  return td;
}

// Студенти без оцінок - наприкінці за будь-якого напряму
function byAverage(direction) {
  return (a, b) => {
    if (a.average === null || b.average === null) {
      return (a.average === null) - (b.average === null);
    }
    return direction * (a.average - b.average);
  };
}

function renderStudents() {
  const query = $("search").value.trim();
  const shown = students.filter((s) => s.last_name.includes(query));
  if (order) {
    shown.sort(byAverage(order === "asc" ? 1 : -1));
  }
  const rows = shown.map((s) => {
    const tr = document.createElement("tr");
    const name = document.createElement("td");
    const link = document.createElement("a");
    link.href = `#student-${s.id}`;
    link.textContent = `${s.last_name} ${s.first_name}`;
    link.addEventListener("click", (event) => {
      event.preventDefault();
      openCard(s.id);
    });
    name.append(link);
    tr.append(name, cell(s.email), cell(s.average === null ? "-" : String(Math.round(s.average))));
    const actions = document.createElement("td");
    if (sessionStorage.getItem("role") === "admin") {
      const remove = document.createElement("button");
      remove.type = "button";
      remove.textContent = "Видалити";
      remove.addEventListener("click", () => removeStudent(s));
      actions.append(remove);
    }
    tr.append(actions);
    return tr;
  });
  $("students").replaceChildren(...rows);
  $("empty").hidden = shown.length > 0;
}

function updateTotal() {
  $("total").textContent = `Усього: ${students.length}`;
}

async function loadStudents() {
  const { status, data } = await api("GET", "/api/students");
  if (status !== 200) {
    fail("Помилка: не вдалося завантажити студентів");
    return;
  }
  students = data;
  renderStudents();
  updateTotal();
}

async function openList() {
  show("list-view");
  const role = sessionStorage.getItem("role");
  $("add-form").hidden = role !== "admin";
  $("import-form").hidden = role !== "admin";
  $("export").hidden = role !== "admin" && role !== "teacher";
  if (students.length === 0) {
    await loadStudents();
  } else {
    renderStudents();
  }
}

async function openCard(id) {
  const [student, grades] = await Promise.all([
    api("GET", `/api/students/${id}`),
    api("GET", `/api/students/${id}/grades`),
  ]);
  if (student.status !== 200 || grades.status !== 200) {
    fail("Помилка: не вдалося відкрити картку студента");
    return;
  }
  const s = student.data;
  $("card-name").textContent = `${s.last_name} ${s.first_name}`;
  $("card-average").textContent = formatAverage(s.average);
  $("grades").replaceChildren(
    ...grades.data.map((g) => {
      const tr = document.createElement("tr");
      tr.append(cell(g.course), cell(String(g.score)), cell(g.ects), cell(g.graded_on));
      return tr;
    }),
  );
  $("grade-form").hidden = sessionStorage.getItem("role") !== "teacher";
  $("grade-form").dataset.studentId = id;
  $("back").hidden = sessionStorage.getItem("role").startsWith("student");
  show("card-view");
}

async function removeStudent(s) {
  confirm(`Видалити студента ${s.last_name} ${s.first_name}?`);
  const { status } = await api("DELETE", `/api/students/${s.id}`);
  if (status !== 204) {
    fail("Помилка: не вдалося видалити студента");
    return;
  }
  students = students.filter((other) => other.id !== s.id);
  renderStudents();
  say("Студента видалено");
}

function toggleOrder() {
  order = order === "desc" ? "asc" : "desc";
  $("sort-average").dataset.order = order;
  renderStudents();
}

async function exportCsv() {
  const response = await fetch("/api/export/students.csv", {
    headers: { Authorization: `Bearer ${token()}` },
  });
  if (response.status !== 200) {
    fail("Помилка: не вдалося експортувати список");
    return;
  }
  const link = document.createElement("a");
  link.href = URL.createObjectURL(await response.blob());
  link.download = "students.csv";
  link.click();
  URL.revokeObjectURL(link.href);
}

async function importCsv(form) {
  const response = await fetch("/api/students/import", {
    method: "POST",
    headers: { Authorization: `Bearer ${token()}` },
    body: new FormData(form),
  });
  if (response.status === 201) {
    const { imported } = await response.json();
    form.reset();
    await loadStudents();
    say(`Імпортовано студентів: ${imported}`);
  } else if (response.status === 400) {
    const { detail } = await response.json();
    fail(`Помилка імпорту: ${detail}`);
  } else {
    fail("Помилка: не вдалося імпортувати файл");
  }
}

async function login(value) {
  sessionStorage.setItem("token", value);
  const { status, data } = await api("GET", "/api/me");
  if (status !== 200) {
    sessionStorage.clear();
    fail("Невідомий токен");
    return;
  }
  const role = data.role === "student" ? `student:${data.student_id}` : data.role;
  sessionStorage.setItem("role", role);
  startSession();
}

function startSession() {
  const role = sessionStorage.getItem("role");
  $("role").textContent = ROLES[role] ?? "Студент";
  $("who").hidden = false;
  say("");
  if (role.startsWith("student:")) {
    openCard(Number(role.split(":")[1]));
  } else {
    openList();
  }
}

document.addEventListener("DOMContentLoaded", () => {
  $("login-form").addEventListener("submit", (event) => {
    event.preventDefault();
    login(new FormData(event.target).get("token").trim());
  });

  $("logout").addEventListener("click", () => {
    sessionStorage.clear();
    students = [];
    $("who").hidden = true;
    $("login-form").reset();
    say("");
    show("login-view");
  });

  $("search").addEventListener("input", renderStudents);
  $("sort-average").addEventListener("click", toggleOrder);
  $("export").addEventListener("click", exportCsv);

  $("import-form").addEventListener("submit", (event) => {
    event.preventDefault();
    importCsv(event.target);
  });

  $("add-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.target;
    const body = Object.fromEntries(new FormData(form));
    const { status, data } = await api("POST", "/api/students", body);
    form.reset();
    if (status === 409) {
      fail("Помилка: email уже використовується");
    } else if (status !== 201) {
      fail("Помилка: перевірте поля форми");
    } else {
      students.push(data);
      renderStudents();
      updateTotal();
      say(`Студента додано: ${data.last_name} ${data.first_name}`);
    }
  });

  $("grade-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.target;
    const studentId = Number(form.dataset.studentId);
    const fields = new FormData(form);
    const { status } = await api("POST", "/api/grades", {
      student_id: studentId,
      course: fields.get("course"),
      score: Number(fields.get("score")),
    });
    if (status !== 201) {
      fail("Помилка: бали від 0 до 100");
      return;
    }
    form.reset();
    await openCard(studentId);
    say("Оцінку виставлено");
  });

  $("back").addEventListener("click", openList);

  if (token()) {
    startSession();
  } else {
    show("login-view");
  }
});
