import sqlite3
from pathlib import Path
from typing import List

# Anchor database to this file's folder so it doesn't wander across directories
DB_PATH = Path(__file__).parent / "todo.db"


def get_connection() -> sqlite3.Connection:
    """Creates a connection with Row factory enabled for dict-style column access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def setup_database() -> None:
    """Initializes the database schema and performs non-destructive column migrations."""
    with get_connection() as conn:
        cursor = conn.cursor()
        # Create base table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT NOT NULL,
                completed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Migration guard: If upgrading from the grade-8 table (which had no 'completed' column)
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [row["name"] for row in cursor.fetchall()]
        if "completed" not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN completed INTEGER DEFAULT 0")
        if "created_at" not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

        conn.commit()


def add_task(task_text: str) -> int:
    """Inserts a new task and returns its new ID."""
    clean_text = task_text.strip()
    if not clean_text:
        return -1

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tasks (task) VALUES (?)", (clean_text,))
        conn.commit()
        return cursor.lastrowid or -1


def get_tasks() -> List[sqlite3.Row]:
    """Retrieves all tasks sorted with incomplete tasks first, newest on top."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, task, completed FROM tasks ORDER BY completed ASC, id DESC")
        return cursor.fetchall()


def update_task_text(task_id: int, new_text: str) -> bool:
    """Updates the task description safely without deleting."""
    clean_text = new_text.strip()
    if not clean_text:
        return False

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET task = ? WHERE id = ?", (clean_text, task_id))
        conn.commit()
        return cursor.rowcount > 0


def toggle_task_completed(task_id: int) -> bool:
    """Flips completed state between 0 (pending) and 1 (done)."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET completed = 1 - completed WHERE id = ?", (task_id,))
        conn.commit()
        return cursor.rowcount > 0


def delete_task(task_id: int) -> bool:
    """Permanently deletes a task by ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        return cursor.rowcount > 0