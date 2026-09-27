from datetime import datetime, timezone
from typing import Any

from .student_service import StudentService, now_iso
from .storage import GradeStore


class ScoringService:
    def __init__(self, store: GradeStore, students: StudentService) -> None:
        self.store = store
        self.students = students

    def create_scheme(self, name: str, method: str, weights: dict[str, float]) -> dict[str, Any]:
        if method == "weighted":
            if set(weights) != {"coursework", "midterm", "final"}:
                raise ValueError("加權方案需為平時、期中、期末各設定權重")
            if any(weight < 0 or weight > 1 for weight in weights.values()):
                raise ValueError("權重需介於 0 到 1")
            if abs(sum(weights.values()) - 1) > 0.001:
                raise ValueError("權重總和必須等於 100%")
        definition = {"method": method, "weights": weights}
        self.store.save_scheme(name, definition, now_iso())
        return {"name": name, **definition}

    def preview_scheme(self, name: str) -> dict[str, Any]:
        scheme = self.store.get_scheme(name)
        if not scheme:
            raise KeyError("找不到評分方案")
        before = self.students.list_students()
        records = []
        for student in before:
            scores = student["scores"]
            if scheme["method"] == "average":
                new_score = sum(scores[key] for key in ("coursework", "midterm", "final")) / 3
            elif scheme["method"] == "highest":
                new_score = max(scores[key] for key in ("coursework", "midterm", "final"))
            else:
                new_score = sum(scores[key] * weight for key, weight in scheme["weights"].items())
            new_score = round(min(100, max(0, new_score + student["adjustments"])), 2)
            records.append(
                {"student_id": student["student_id"], "name": student["name"], "before": student["final_score"], "after": new_score, "change": round(new_score - student["final_score"], 2)}
            )
        return {"scheme": scheme, "active_scheme": self.store.active_scheme_name(), "affected_count": len(records), "records": records}

    def apply_scheme(self, name: str) -> dict[str, Any]:
        if not self.store.get_scheme(name):
            raise KeyError("找不到評分方案")
        previous = self.store.active_scheme_name()
        self.store.apply_scheme(name, now_iso())
        return {"active_scheme": name, "previous_scheme": previous, "students_affected": self.store.count_students()}

    def undo_scheme(self) -> dict[str, Any]:
        previous = self.store.undo_scheme()
        return {"active_scheme": self.store.active_scheme_name(), "restored_scheme": previous}

    @staticmethod
    def _matches(value: float, operator: str, threshold: float) -> bool:
        return {"<": value < threshold, "<=": value <= threshold, ">": value > threshold, ">=": value >= threshold}[operator]

    def create_rule(self, definition: dict[str, Any]) -> dict[str, Any]:
        rule_id = self.store.save_rule(definition["name"], definition, now_iso())
        return {"id": rule_id, **definition}

    def preview_rule(self, rule_id: int) -> dict[str, Any]:
        rule = self.store.get_rule(rule_id)
        if not rule:
            raise KeyError("找不到調整規則")
        applied = self.store.applied_student_ids(rule_id)
        affected = []
        skipped = 0
        for student in self.students.list_students():
            if student["student_id"] in applied:
                skipped += 1
                continue
            target = student["final_score"] if rule["field"] == "overall" else student[rule["field"]]
            if not self._matches(float(target), rule["operator"], float(rule["threshold"])):
                continue
            if rule["adjustment_type"] == "deduct":
                delta = -float(rule["amount"])
            elif rule["adjustment_type"] == "bonus":
                delta = float(rule["amount"])
            else:
                delta = student["final_score"] * float(rule["amount"]) / 100
            affected.append({"student_id": student["student_id"], "name": student["name"], "current_score": student["final_score"], "adjustment": round(delta, 2), "projected_score": round(min(100, max(0, student["final_score"] + delta)), 2)})
        return {"rule": rule, "affected_count": len(affected), "already_applied_count": skipped, "records": affected}

    def apply_rule(self, rule_id: int) -> dict[str, Any]:
        preview = self.preview_rule(rule_id)
        timestamp = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
        applied = 0
        for target in preview["records"]:
            student = self.store.get_student(target["student_id"])
            if student and self.store.record_rule_application(rule_id, student["student_id"], target["adjustment"], student["adjustments"], timestamp):
                applied += 1
        return {"rule_id": rule_id, "applied_count": applied, "already_applied_count": preview["already_applied_count"]}

    def undo_rule(self, rule_id: int) -> dict[str, Any]:
        if not self.store.get_rule(rule_id):
            raise KeyError("找不到調整規則")
        return {"rule_id": rule_id, "reverted_count": self.store.revert_rule(rule_id, now_iso())}