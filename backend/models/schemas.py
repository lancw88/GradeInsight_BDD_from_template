from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StudentCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    student_id: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=100)
    class_name: str = Field(default="未分類", max_length=100)
    scores: dict[str, float]
    attendance_rate: float = Field(default=100, ge=0, le=100)
    absences: int = Field(default=0, ge=0)

    @field_validator("scores")
    @classmethod
    def validate_scores(cls, scores: dict[str, float]) -> dict[str, float]:
        required = {"coursework", "midterm", "final"}
        if not required.issubset(scores):
            raise ValueError("成績必須包含 coursework、midterm、final 三個項目")
        if any(not 0 <= score <= 100 for score in scores.values()):
            raise ValueError("所有成績必須介於 0 到 100 分")
        return scores


class ImportCommitRequest(BaseModel):
    records: list[StudentCreate] = Field(min_length=1, max_length=500)


class EditScoreRequest(BaseModel):
    component: str = Field(min_length=1, max_length=60)
    score: float = Field(ge=0, le=100)
    reason: str = Field(min_length=3, max_length=500)
    modified_by: str = Field(default="教師", min_length=1, max_length=100)


class SchemeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    method: Literal["weighted", "average", "highest"] = "weighted"
    weights: dict[str, float] = Field(
        default_factory=lambda: {"coursework": 0.2, "midterm": 0.3, "final": 0.5}
    )


class AdjustmentRuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    field: Literal["overall", "attendance_rate", "absences"]
    operator: Literal["<", "<=", ">", ">="]
    threshold: float
    adjustment_type: Literal["deduct", "bonus", "percentage"]
    amount: float = Field(gt=0, le=100)


class ApplyRuleRequest(BaseModel):
    rule_id: int = Field(gt=0)


class NotificationRequest(BaseModel):
    student_ids: list[str] = Field(min_length=1, max_length=500)
    message: str = Field(min_length=1, max_length=1000)