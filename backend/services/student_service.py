import random
import uuid
from datetime import datetime, timezone
from typing import Any

from .storage import GradeStore

COMPONENTS = ("coursework", "midterm", "final")
COMPONENT_LABELS = {"coursework": "平時", "midterm": "期中", "final": "期末"}


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


class StudentService:
    def __init__(self, store: GradeStore) -> None:
        self.store = store

    def ensure_default_scheme(self) -> None:
        if not self.store.get_scheme("預設加權"):
            self.store.save_scheme(
                "預設加權",
                {"method": "weighted", "weights": {"coursework": 0.2, "midterm": 0.3, "final": 0.5}},
                now_iso(),
            )
        if not self.store.active_scheme_name():
            self.store.apply_scheme("預設加權", now_iso())

    def generate_demo_students(self, count: int = 30, replace: bool = False) -> dict[str, int]:
        if count < 1 or count > 500:
            raise ValueError("模擬資料筆數必須介於 1 到 500")
        if replace:
            with self.store.connection() as connection:
                connection.execute("DELETE FROM students")
                connection.execute("DELETE FROM audit_log")
                connection.execute("DELETE FROM applied_rules")
        use_sequential_ids = replace or self.store.count_students() == 0
        rng = random.Random()
        inserted = 0
        for index in range(1, count + 1):
            student_id = f"S{index:03d}" if use_sequential_ids else f"SIM-{uuid.uuid4().hex[:10].upper()}"
            student = {
                "student_id": student_id,
                "name": f"模擬學生{index:02d}",
                "class_name": "示範班",
                "scores": {
                    "coursework": round(rng.uniform(45, 100), 1),
                    "midterm": round(rng.uniform(35, 100), 1),
                    "final": round(rng.uniform(30, 100), 1),
                },
                "attendance_rate": round(rng.uniform(65, 100), 1),
                "absences": rng.randint(0, 8),
                "notes": "示範資料",
                "updated_at": now_iso(),
            }
            inserted += int(self.store.insert_student(student))
        return {"requested": count, "inserted": inserted, "total": self.store.count_students()}

    def overall_score(self, student: dict[str, Any]) -> float:
        active_name = self.store.active_scheme_name() or "預設加權"
        scheme = self.store.get_scheme(active_name) or {
            "method": "weighted",
            "weights": {"coursework": 0.2, "midterm": 0.3, "final": 0.5},
        }
        scores = student["scores"]
        method = scheme["method"]
        if method == "average":
            base = sum(scores[component] for component in COMPONENTS) / len(COMPONENTS)
        elif method == "highest":
            base = max(scores[component] for component in COMPONENTS)
        else:
            base = sum(scores[key] * weight for key, weight in scheme["weights"].items())
        return round(min(100, max(0, base + student.get("adjustments", 0))), 2)

    def serialize_student(self, student: dict[str, Any]) -> dict[str, Any]:
        score = self.overall_score(student)
        return {
            **student,
            "final_score": score,
            "grade": "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 70 else "D" if score >= 60 else "F",
        }

    def list_students(self, class_name: str | None = None) -> list[dict[str, Any]]:
        students = self.store.list_students()
        if class_name:
            students = [student for student in students if student["class_name"] == class_name]
        return [self.serialize_student(student) for student in students]

    def student_details(self, student_id: str) -> dict[str, Any] | None:
        student = self.store.get_student(student_id)
        if not student:
            return None
        roster = sorted(self.list_students(class_name=student["class_name"]), key=lambda row: row["final_score"], reverse=True)
        student_row = next(row for row in roster if row["student_id"] == student_id)
        class_average = sum(row["final_score"] for row in roster) / max(1, len(roster))
        return {
            **student_row,
            "rank": next(index for index, row in enumerate(roster, start=1) if row["student_id"] == student_id),
            "class_size": len(roster),
            "class_average": round(class_average, 2),
            "trend": [
                {"component": component, "label": COMPONENT_LABELS[component], "score": student["scores"][component]}
                for component in COMPONENTS
            ],
            "audit_history": self.store.audit_history(student_id),
        }

    def edit_score(
        self, student_id: str, component: str, score: float, reason: str, modified_by: str
    ) -> dict[str, Any] | None:
        if component not in COMPONENTS:
            raise ValueError("成績項目需為平時、期中或期末")
        result = self.store.update_score(student_id, component, score, reason, modified_by, now_iso())
        return self.serialize_student(result[1]) if result else None

    def undo_edit(self, student_id: str) -> dict[str, Any] | None:
        if not self.store.undo_latest_edit(student_id, now_iso()):
            return None
        student = self.store.get_student(student_id)
        return self.serialize_student(student) if student else None