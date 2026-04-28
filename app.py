from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "tasks.db"

app = Flask(__name__)


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'todo',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


@app.get("/")
def index() -> str:
    return render_template("index.html")


@app.get("/api/tasks")
def list_tasks() -> Any:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, title, description, status, created_at FROM tasks ORDER BY id DESC"
        ).fetchall()
    return jsonify([dict(row) for row in rows])


@app.post("/api/tasks")
def create_task() -> Any:
    payload = request.get_json(silent=True) or {}
    title = str(payload.get("title", "")).strip()
    description = str(payload.get("description", "")).strip()

    if not title:
        return jsonify({"error": "Le titre est obligatoire."}), 400

    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO tasks (title, description) VALUES (?, ?)", (title, description)
        )
        task_id = cur.lastrowid

    return jsonify({"id": task_id, "title": title, "description": description, "status": "todo"}), 201


@app.patch("/api/tasks/<int:task_id>")
def update_task(task_id: int) -> Any:
    payload = request.get_json(silent=True) or {}
    status = payload.get("status")
    if status not in {"todo", "done"}:
        return jsonify({"error": "Statut invalide."}), 400

    with get_db() as conn:
        conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))

    return jsonify({"ok": True})


@app.delete("/api/tasks/<int:task_id>")
def delete_task(task_id: int) -> Any:
    with get_db() as conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    return jsonify({"ok": True})


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
