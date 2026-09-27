import statistics
from collections import Counter
from typing import Any

from .student_service import StudentService


def _letter_grade(score: float) -> str:
    return "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 70 else "D" if score >= 60 else "F"


class AnalysisService:
    def __init__(self, students: StudentService) -> None:
        self.students = students

    def analyze(
        self, component: str = "overall", pass_mark: float = 60, bin_width: int = 10, class_name: str | None = None
    ) -> dict[str, Any]:
        if not 1 <= bin_width <= 50:
            raise ValueError("分數區間寬度需介於 1 到 50")
        rows = self.students.list_students(class_name)
        values = [row["final_score"] if component == "overall" else row["scores"].get(component) for row in rows]
        values = [float(value) for value in values if value is not None]
        if not values:
            return {"count": 0, "statistics": {}, "grade_counts": {}, "histogram": [], "outliers": [], "conclusions": ["目前沒有可分析的成績資料。"]}
        mean = statistics.mean(values)
        modes = statistics.multimode(values)
        grade_counts = Counter(_letter_grade(value) for value in values)
        bins = []
        for start in range(0, 100, bin_width):
            end = min(100, start + bin_width)
            count = sum(start <= value < end or (end == 100 and value == 100) for value in values)
            bins.append({"label": f"{start}-{end}", "start": start, "end": end, "count": count})
        sorted_values = sorted(values)
        lower = statistics.median(sorted_values[: len(sorted_values) // 2]) if len(values) > 1 else values[0]
        upper = statistics.median(sorted_values[(len(sorted_values) + 1) // 2 :]) if len(values) > 1 else values[0]
        iqr = upper - lower
        outlier_ids = []
        for row in rows:
            value = row["final_score"] if component == "overall" else row["scores"].get(component)
            if value is not None and (value < lower - 1.5 * iqr or value > upper + 1.5 * iqr):
                outlier_ids.append({"student_id": row["student_id"], "name": row["name"], "score": value})
        pass_count = sum(value >= pass_mark for value in values)
        excellent_count = sum(value >= 85 for value in values)
        statistics_result = {
            "mean": round(mean, 2),
            "median": round(statistics.median(values), 2),
            "mode": modes,
            "standard_deviation": round(statistics.stdev(values), 2) if len(values) > 1 else 0,
            "variance": round(statistics.variance(values), 2) if len(values) > 1 else 0,
            "maximum": max(values),
            "minimum": min(values),
            "pass_rate": round(pass_count * 100 / len(values), 2),
            "excellent_rate": round(excellent_count * 100 / len(values), 2),
            "pass_mark": pass_mark,
        }
        conclusions = []
        if statistics_result["pass_rate"] < 70:
            conclusions.append("班級及格率偏低，建議安排補救教學並檢視高錯誤率單元。")
        else:
            conclusions.append("整體及格率達到七成，建議持續追蹤低分與近期退步學生。")
        if statistics_result["standard_deviation"] >= 15:
            conclusions.append("成績差異較大，可依程度分組提供不同練習與輔導。")
        if outlier_ids:
            conclusions.append(f"偵測到 {len(outlier_ids)} 筆統計離群成績，建議核對原始評量紀錄。")
        return {
            "count": len(values),
            "statistics": statistics_result,
            "grade_counts": {
                grade: {"count": grade_counts.get(grade, 0), "percentage": round(grade_counts.get(grade, 0) * 100 / len(values), 2)}
                for grade in ("A", "B", "C", "D", "F")
            },
            "histogram": bins,
            "outliers": outlier_ids,
            "conclusions": conclusions,
        }

    def at_risk(
        self, pass_mark: float = 60, risk_range: float = 10, sort_by: str = "score", class_name: str | None = None
    ) -> list[dict[str, Any]]:
        if not 0 <= pass_mark <= 100 or not 0 <= risk_range <= 100:
            raise ValueError("及格線和風險範圍需介於 0 到 100")
        result = []
        for student in self.students.list_students(class_name):
            score = student["final_score"]
            if score < pass_mark:
                level = "不及格"
            elif score <= pass_mark + risk_range:
                level = "接近及格線"
            else:
                continue
            result.append(
                {
                    "student_id": student["student_id"],
                    "name": student["name"],
                    "class_name": student["class_name"],
                    "final_score": score,
                    "gap_to_pass": round(score - pass_mark, 2),
                    "risk_level": level,
                }
            )
        if sort_by == "risk":
            result.sort(key=lambda row: (row["risk_level"] != "不及格", row["final_score"]))
        else:
            result.sort(key=lambda row: row["final_score"])
        return result