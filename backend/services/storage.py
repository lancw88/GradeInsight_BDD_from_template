import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


def _default_database_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "gradeinsight.sqlite3"


class GradeStore:
    def __init__(self, database_path: str | Path | None = None) -> None:
        configured_path = database_path or os.getenv("GRADEINSIGHT_DB")
        self.database_path = Path(configured_path) if configured_path else _default_database_path()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path, timeout=15)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS students (
                    student_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    class_name TEXT NOT NULL DEFAULT '未分類',
                    scores TEXT NOT NULL,
                    attendance_rate REAL NOT NULL DEFAULT 100,
                    absences INTEGER NOT NULL DEFAULT 0,
                    adjustments REAL NOT NULL DEFAULT 0,
                    notes TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    component TEXT NOT NULL,
                    old_score REAL NOT NULL,
                    new_score REAL NOT NULL,
                    reason TEXT NOT NULL,
                    modified_by TEXT NOT NULL,
                    changed_at TEXT NOT NULL,
                    reverted INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS schemes (
                    name TEXT PRIMARY KEY,
                    definition TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS app_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS scheme_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    previous_name TEXT,
                    applied_name TEXT NOT NULL,
                    changed_at TEXT NOT NULL,
                    reverted INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS adjustment_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    definition TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS applied_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_id INTEGER NOT NULL,
                    student_id TEXT NOT NULL,
                    delta REAL NOT NULL,
                    previous_adjustment REAL NOT NULL,
                    applied_at TEXT NOT NULL,
                    reverted INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    delivery_status TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS backup_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_audit_student ON audit_log(student_id, id);
                CREATE INDEX IF NOT EXISTS idx_applied_rules_rule ON applied_rules(rule_id, reverted);
                CREATE UNIQUE INDEX IF NOT EXISTS idx_active_rule_application
                    ON applied_rules(rule_id, student_id) WHERE reverted = 0;
                """
            )

    def count_students(self) -> int:
        with self.connection() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM students").fetchone()[0])

    def student_ids(self) -> set[str]:
        with self.connection() as connection:
            return {row[0] for row in connection.execute("SELECT student_id FROM students")}

    def list_students(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute("SELECT * FROM students ORDER BY student_id").fetchall()
        return [self._student_dict(row) for row in rows]

    def get_student(self, student_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM students WHERE student_id = ?", (student_id,)
            ).fetchone()
        return self._student_dict(row) if row else None

    def insert_student(self, student: dict[str, Any]) -> bool:
        with self.connection() as connection:
            cursor = connection.execute(
                """INSERT OR IGNORE INTO students
                (student_id, name, class_name, scores, attendance_rate, absences,
                 adjustments, notes, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)""",
                (
                    student["student_id"],
                    student["name"],
                    student.get("class_name", "未分類"),
                    json.dumps(student["scores"], ensure_ascii=False),
                    student.get("attendance_rate", 100),
                    student.get("absences", 0),
                    student.get("notes", ""),
                    student["updated_at"],
                ),
            )
            return cursor.rowcount == 1

    def update_score(
        self,
        student_id: str,
        component: str,
        score: float,
        reason: str,
        modified_by: str,
        changed_at: str,
    ) -> tuple[float, dict[str, Any]] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM students WHERE student_id = ?", (student_id,)
            ).fetchone()
            if not row:
                return None
            scores = json.loads(row["scores"])
            old_score = scores.get(component)
            if old_score is None:
                raise ValueError(f"找不到成績項目：{component}")
            scores[component] = score
            connection.execute(
                "UPDATE students SET scores = ?, updated_at = ? WHERE student_id = ?",
                (json.dumps(scores, ensure_ascii=False), changed_at, student_id),
            )
            connection.execute(
                """INSERT INTO audit_log
                (student_id, component, old_score, new_score, reason, modified_by, changed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (student_id, component, old_score, score, reason, modified_by, changed_at),
            )
            updated_row = connection.execute(
                "SELECT * FROM students WHERE student_id = ?", (student_id,)
            ).fetchone()
            return float(old_score), self._student_dict(updated_row)

    def audit_history(self, student_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM audit_log"
        parameters: tuple[Any, ...] = ()
        if student_id:
            query += " WHERE student_id = ?"
            parameters = (student_id,)
        query += " ORDER BY id DESC LIMIT 500"
        with self.connection() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [dict(row) for row in rows]

    def undo_latest_edit(self, student_id: str, changed_at: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            audit = connection.execute(
                """SELECT * FROM audit_log WHERE student_id = ? AND reverted = 0
                ORDER BY id DESC LIMIT 1""",
                (student_id,),
            ).fetchone()
            if not audit:
                return None
            student = connection.execute(
                "SELECT scores FROM students WHERE student_id = ?", (student_id,)
            ).fetchone()
            if not student:
                return None
            scores = json.loads(student["scores"])
            scores[audit["component"]] = audit["old_score"]
            connection.execute(
                "UPDATE students SET scores = ?, updated_at = ? WHERE student_id = ?",
                (json.dumps(scores, ensure_ascii=False), changed_at, student_id),
            )
            connection.execute("UPDATE audit_log SET reverted = 1 WHERE id = ?", (audit["id"],))
            return dict(audit)

    def save_scheme(self, name: str, definition: dict[str, Any], created_at: str) -> None:
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO schemes(name, definition, created_at) VALUES (?, ?, ?) "
                "ON CONFLICT(name) DO UPDATE SET definition = excluded.definition",
                (name, json.dumps(definition, ensure_ascii=False), created_at),
            )

    def list_schemes(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute("SELECT * FROM schemes ORDER BY name").fetchall()
        return [
            {"name": row["name"], **json.loads(row["definition"]), "created_at": row["created_at"]}
            for row in rows
        ]

    def get_scheme(self, name: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM schemes WHERE name = ?", (name,)).fetchone()
        return {"name": row["name"], **json.loads(row["definition"])} if row else None

    def active_scheme_name(self) -> str | None:
        with self.connection() as connection:
            row = connection.execute("SELECT value FROM app_state WHERE key = 'active_scheme'").fetchone()
        return row[0] if row else None

    def apply_scheme(self, name: str, changed_at: str) -> None:
        with self.connection() as connection:
            previous = connection.execute(
                "SELECT value FROM app_state WHERE key = 'active_scheme'"
            ).fetchone()
            connection.execute(
                "INSERT INTO scheme_history(previous_name, applied_name, changed_at) VALUES (?, ?, ?)",
                (previous[0] if previous else None, name, changed_at),
            )
            connection.execute(
                "INSERT INTO app_state(key, value) VALUES ('active_scheme', ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (name,),
            )

    def undo_scheme(self) -> str | None:
        with self.connection() as connection:
            history = connection.execute(
                "SELECT * FROM scheme_history WHERE reverted = 0 ORDER BY id DESC LIMIT 1"
            ).fetchone()
            if not history:
                return None
            previous = history["previous_name"]
            if previous is None:
                connection.execute("DELETE FROM app_state WHERE key = 'active_scheme'")
            else:
                connection.execute(
                    "UPDATE app_state SET value = ? WHERE key = 'active_scheme'", (previous,)
                )
            connection.execute("UPDATE scheme_history SET reverted = 1 WHERE id = ?", (history["id"],))
            return previous

    def save_rule(self, name: str, definition: dict[str, Any], created_at: str) -> int:
        with self.connection() as connection:
            cursor = connection.execute(
                "INSERT INTO adjustment_rules(name, definition, created_at) VALUES (?, ?, ?)",
                (name, json.dumps(definition, ensure_ascii=False), created_at),
            )
            return int(cursor.lastrowid)

    def list_rules(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute("SELECT * FROM adjustment_rules ORDER BY id DESC").fetchall()
        return [
            {"id": row["id"], **json.loads(row["definition"]), "created_at": row["created_at"]}
            for row in rows
        ]

    def get_rule(self, rule_id: int) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM adjustment_rules WHERE id = ?", (rule_id,)
            ).fetchone()
        return {"id": row["id"], **json.loads(row["definition"])} if row else None

    def applied_student_ids(self, rule_id: int) -> set[str]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT student_id FROM applied_rules WHERE rule_id = ? AND reverted = 0",
                (rule_id,),
            ).fetchall()
        return {row[0] for row in rows}

    def record_rule_application(
        self, rule_id: int, student_id: str, delta: float, previous_adjustment: float, applied_at: str
    ) -> bool:
        with self.connection() as connection:
            cursor = connection.execute(
                """INSERT OR IGNORE INTO applied_rules
                (rule_id, student_id, delta, previous_adjustment, applied_at)
                VALUES (?, ?, ?, ?, ?)""",
                (rule_id, student_id, delta, previous_adjustment, applied_at),
            )
            if cursor.rowcount:
                connection.execute(
                    "UPDATE students SET adjustments = ?, updated_at = ? WHERE student_id = ?",
                    (previous_adjustment + delta, applied_at, student_id),
                )
            return cursor.rowcount == 1

    def revert_rule(self, rule_id: int, reverted_at: str) -> int:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM applied_rules WHERE rule_id = ? AND reverted = 0", (rule_id,)
            ).fetchall()
            for row in rows:
                connection.execute(
                    "UPDATE students SET adjustments = adjustments - ?, updated_at = ? WHERE student_id = ?",
                    (row["delta"], reverted_at, row["student_id"]),
                )
                connection.execute(
                    "UPDATE applied_rules SET reverted = 1 WHERE id = ?", (row["id"],)
                )
            return len(rows)

    def save_notification(self, student_id: str, message: str, created_at: str) -> None:
        with self.connection() as connection:
            connection.execute(
                """INSERT INTO notifications(student_id, message, created_at, delivery_status)
                VALUES (?, ?, ?, 'simulated')""",
                (student_id, message, created_at),
            )

    def save_backup(
        self, filename: str, size_bytes: int, status: str, message: str, created_at: str
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """INSERT INTO backup_history(filename, size_bytes, status, message, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (filename, size_bytes, status, message, created_at),
            )

    def backup_history(self, limit: int = 100) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM backup_history ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def _student_dict(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "student_id": row["student_id"],
            "name": row["name"],
            "class_name": row["class_name"],
            "scores": json.loads(row["scores"]),
            "attendance_rate": row["attendance_rate"],
            "absences": row["absences"],
            "adjustments": row["adjustments"],
            "notes": row["notes"],
            "updated_at": row["updated_at"],
        }