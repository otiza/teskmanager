from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "tasks.db"

app = Flask(__name__)


VALID_STATUSES = {"todo", "done"}


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_column(conn: sqlite3.Connection, column_name: str, definition: str) -> None:
    columns = conn.execute("PRAGMA table_info(tasks)").fetchall()
    existing_columns = {row[1] for row in columns}
    if column_name not in existing_columns:
        conn.execute(f"ALTER TABLE tasks ADD COLUMN {column_name} {definition}")


def init_db() -> None:
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                assigned_to TEXT DEFAULT '',
                deadline TEXT DEFAULT NULL,
                status TEXT NOT NULL DEFAULT 'todo',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        ensure_column(conn, "assigned_to", "TEXT DEFAULT ''")
        ensure_column(conn, "deadline", "TEXT DEFAULT NULL")


def parse_deadline(raw_deadline: str) -> str | None:
    raw_deadline = raw_deadline.strip()
    if not raw_deadline:
        return None
    try:
        datetime.strptime(raw_deadline, "%Y-%m-%d")
    except ValueError:
        raise ValueError("La date limite doit être au format AAAA-MM-JJ.") from None
    return raw_deadline


@app.get("/")
def index() -> str:
    return render_template("index.html")


@app.get("/api/tasks")
def list_tasks() -> Any:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT id, title, description, assigned_to, deadline, status, created_at
            FROM tasks
            ORDER BY
              CASE WHEN status = 'todo' THEN 0 ELSE 1 END,
              CASE WHEN deadline IS NULL OR deadline = '' THEN 1 ELSE 0 END,
              deadline ASC,
              id DESC
            """
        ).fetchall()
    return jsonify([dict(row) for row in rows])


@app.post("/api/tasks")
def create_task() -> Any:
    payload = request.get_json(silent=True) or {}
    title = str(payload.get("title", "")).strip()
    description = str(payload.get("description", "")).strip()
    assigned_to = str(payload.get("assigned_to", "")).strip()

    try:
        deadline = parse_deadline(str(payload.get("deadline", "")))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    if not title:
        return jsonify({"error": "Le titre est obligatoire."}), 400

    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO tasks (title, description, assigned_to, deadline)
            VALUES (?, ?, ?, ?)
            """,
            (title, description, assigned_to, deadline),
        )
        task_id = cur.lastrowid

    return (
        jsonify(
            {
                "id": task_id,
                "title": title,
                "description": description,
                "assigned_to": assigned_to,
                "deadline": deadline,
                "status": "todo",
            }
        ),
        201,
    )


@app.patch("/api/tasks/<int:task_id>")
def update_task(task_id: int) -> Any:
    payload = request.get_json(silent=True) or {}

    with get_db() as conn:
        existing = conn.execute("SELECT id FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not existing:
            return jsonify({"error": "Tâche introuvable."}), 404

        updates = []
        values: list[Any] = []

        if "status" in payload:
            status = payload.get("status")
            if status not in VALID_STATUSES:
                return jsonify({"error": "Statut invalide."}), 400
            updates.append("status = ?")
            values.append(status)

        if "assigned_to" in payload:
            updates.append("assigned_to = ?")
            values.append(str(payload.get("assigned_to", "")).strip())

        if "deadline" in payload:
            try:
                parsed_deadline = parse_deadline(str(payload.get("deadline", "")))
            except ValueError as exc:
                return jsonify({"error": str(exc)}), 400
            updates.append("deadline = ?")
            values.append(parsed_deadline)

        if not updates:
            return jsonify({"error": "Aucune mise à jour fournie."}), 400

        values.append(task_id)
        conn.execute(f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?", values)

    return jsonify({"ok": True})


@app.delete("/api/tasks/<int:task_id>")
def delete_task(task_id: int) -> Any:
    with get_db() as conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    return jsonify({"ok": True})


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
