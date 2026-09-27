import csv
import hmac
import io
import json
import logging
import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime
from urllib.parse import quote

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import RequestValidationError

from backend.models.schemas import (
    AdjustmentRuleCreate,
    ApplyRuleRequest,
    EditScoreRequest,
    ImportCommitRequest,
    NotificationRequest,
    SchemeCreate,
)
from backend.services.analysis_service import AnalysisService
from backend.services.backup_service import BackupService
from backend.services.import_service import ImportService
from backend.services.report_service import ReportService
from backend.services.scoring_service import ScoringService
from backend.services.storage import GradeStore
from backend.services.student_service import StudentService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

store = GradeStore()
students = StudentService(store)
analysis = AnalysisService(students)
scoring = ScoringService(store, students)
imports = ImportService(store)
reports = ReportService(students, analysis)
backups = BackupService(store)


@asynccontextmanager
async def lifespan(_: FastAPI):
    store.initialize()
    students.ensure_default_scheme()
    if store.count_students() == 0:
        students.generate_demo_students(30)
    scheduler = BackgroundScheduler(timezone="Asia/Taipei")
    scheduler.add_job(
        backups.create_backup,
        CronTrigger(hour=0, minute=0, timezone="Asia/Taipei"),
        id="daily-grade-backup",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("GradeInsight API 已啟動；每日備份排程已啟用")
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)


app = FastAPI(
    title="GradeInsight 成績管理 API",
    description="成績匯入、分析、評分、報表與加密備份服務。",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["*"],
)


@app.middleware("http")
async def require_api_token(request, call_next):
    expected_token = os.getenv("GRADEINSIGHT_API_TOKEN", "")
    if expected_token and request.url.path.startswith("/api/") and request.url.path != "/api/health":
        supplied_token = request.headers.get("X-API-Key", "")
        if not hmac.compare_digest(supplied_token, expected_token):
            return JSONResponse(status_code=401, content={"detail": "未授權，請設定有效的 API Token。"})
    return await call_next(request)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_, error: RequestValidationError):
    errors = [
        {"field": ".".join(str(part) for part in item["loc"]), "message": item["msg"]}
        for item in error.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={"detail": "輸入資料格式有誤，請檢查必填欄位與數值範圍。", "errors": errors},
    )


@app.exception_handler(ValueError)
async def value_error_handler(_, error: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(error)})


@app.exception_handler(KeyError)
async def not_found_error_handler(_, error: KeyError):
    return JSONResponse(status_code=404, content={"detail": str(error).strip("'") or "找不到指定資料"})


@app.exception_handler(Exception)
async def unexpected_error_handler(_, error: Exception):
    logger.exception("未預期的 API 錯誤", exc_info=error)
    return JSONResponse(status_code=500, content={"detail": "系統暫時無法處理此請求，請稍後再試或聯絡管理員。"})


def _component(value: str) -> str:
    if value not in {"overall", "coursework", "midterm", "final"}:
        raise HTTPException(status_code=400, detail="成績項目需為總成績、平時、期中或期末")
    return value


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "message": "服務正常"}


@app.get("/api/students")
def list_students(class_name: str | None = None) -> list[dict]:
    return students.list_students(class_name)


@app.get("/api/students/{student_id}")
def student_details(student_id: str) -> dict:
    record = students.student_details(student_id)
    if not record:
        raise HTTPException(status_code=404, detail="找不到這位學生")
    return record


@app.put("/api/students/{student_id}/scores")
def edit_student_score(student_id: str, request: EditScoreRequest) -> dict:
    if not store.get_student(student_id):
        raise HTTPException(status_code=404, detail="找不到這位學生")
    result = students.edit_score(student_id, request.component, request.score, request.reason, request.modified_by)
    return {"message": "成績已更新，修改紀錄已保存", "student": result}


@app.post("/api/students/{student_id}/undo")
def undo_student_edit(student_id: str) -> dict:
    if not store.get_student(student_id):
        raise HTTPException(status_code=404, detail="找不到這位學生")
    result = students.undo_edit(student_id)
    if not result:
        raise HTTPException(status_code=409, detail="此學生沒有可撤銷的成績修改")
    return {"message": "已還原最近一次成績修改", "student": result}


@app.get("/api/audit")
def audit_history(student_id: str | None = None) -> list[dict]:
    return store.audit_history(student_id)


@app.get("/api/analysis")
def analyze_grades(
    component: str = "overall",
    pass_mark: float = Query(default=60, ge=0, le=100),
    bin_width: int = Query(default=10, ge=1, le=50),
    class_name: str | None = None,
) -> dict:
    return analysis.analyze(_component(component), pass_mark, bin_width, class_name)


@app.get("/api/analysis/compare")
def compare_analysis(
    baseline_mean: float = Query(ge=0, le=100),
    baseline_label: str = Query(default="比較班級", max_length=100),
    component: str = "overall",
) -> dict:
    current = analysis.analyze(_component(component))["statistics"]
    if not current:
        raise HTTPException(status_code=404, detail="目前沒有足夠的成績資料可比較")
    delta = round(current["mean"] - baseline_mean, 2)
    return {
        "current_mean": current["mean"],
        "baseline_mean": baseline_mean,
        "baseline_label": baseline_label,
        "difference": delta,
        "summary": "高於" if delta > 0 else "低於" if delta < 0 else "持平",
    }


@app.get("/api/at-risk")
def at_risk_students(
    pass_mark: float = Query(default=60, ge=0, le=100),
    risk_range: float = Query(default=10, ge=0, le=100),
    sort_by: str = "score",
    class_name: str | None = None,
) -> list[dict]:
    if sort_by not in {"score", "risk"}:
        raise HTTPException(status_code=400, detail="排序方式需為 score 或 risk")
    return analysis.at_risk(pass_mark, risk_range, sort_by, class_name)


@app.get("/api/at-risk/export")
def export_at_risk(
    pass_mark: float = Query(default=60, ge=0, le=100),
    risk_range: float = Query(default=10, ge=0, le=100),
) -> Response:
    records = analysis.at_risk(pass_mark, risk_range)
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["學號", "姓名", "班級", "總成績", "與及格線差距", "風險級別"])
    for row in records:
        writer.writerow([row["student_id"], row["name"], row["class_name"], row["final_score"], row["gap_to_pass"], row["risk_level"]])
    return Response("\ufeff" + output.getvalue(), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": "attachment; filename=at-risk.csv"})


@app.post("/api/notifications/batch")
def send_batch_notifications(request: NotificationRequest) -> dict:
    available = store.student_ids()
    missing = sorted(set(request.student_ids) - available)
    if missing:
        raise HTTPException(status_code=404, detail=f"找不到學號：{', '.join(missing[:10])}")
    for student_id in set(request.student_ids):
        store.save_notification(student_id, request.message, datetime.now().astimezone().isoformat(timespec="seconds"))
    return {"queued": len(set(request.student_ids)), "delivery_mode": "simulated", "message": "提醒已記錄於系統；尚未設定外部郵件或簡訊服務，因此不會實際寄送。"}


@app.post("/api/import/preview")
async def preview_import(file: UploadFile = File(...)) -> dict:
    content = await file.read(5 * 1024 * 1024 + 1)
    return imports.preview(file.filename or "upload", content)


@app.post("/api/import/commit")
def commit_import(request: ImportCommitRequest) -> dict:
    return imports.commit([record.model_dump() for record in request.records])


@app.get("/api/import/template")
def download_import_template() -> Response:
    content = "學號,姓名,班級,平時,期中,期末,出席率,缺席次數\nS001,王小明,示範班,85,78,90,95,1\n"
    return Response("\ufeff" + content, media_type="text/csv; charset=utf-8", headers={"Content-Disposition": "attachment; filename=grade-template.csv"})


@app.post("/api/demo/generate")
def generate_demo(count: int = Query(default=30, ge=1, le=500), replace: bool = False) -> dict:
    return students.generate_demo_students(count, replace)


@app.get("/api/schemes")
def list_schemes() -> dict:
    return {"active_scheme": store.active_scheme_name(), "schemes": store.list_schemes()}


@app.post("/api/schemes")
def create_scheme(request: SchemeCreate) -> dict:
    return scoring.create_scheme(request.name, request.method, request.weights)


@app.post("/api/schemes/{name}/preview")
def preview_scheme(name: str) -> dict:
    return scoring.preview_scheme(name)


@app.post("/api/schemes/{name}/apply")
def apply_scheme(name: str) -> dict:
    return scoring.apply_scheme(name)


@app.post("/api/schemes/undo")
def undo_scheme() -> dict:
    return scoring.undo_scheme()


@app.get("/api/rules")
def list_rules() -> list[dict]:
    return store.list_rules()


@app.post("/api/rules")
def create_rule(request: AdjustmentRuleCreate) -> dict:
    try:
        return scoring.create_rule(request.model_dump())
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=409, detail="此規則名稱已存在") from error


@app.post("/api/rules/{rule_id}/preview")
def preview_rule(rule_id: int) -> dict:
    return scoring.preview_rule(rule_id)


@app.post("/api/rules/apply")
def apply_rule(request: ApplyRuleRequest) -> dict:
    return scoring.apply_rule(request.rule_id)


@app.post("/api/rules/{rule_id}/undo")
def undo_rule(rule_id: int) -> dict:
    return scoring.undo_rule(rule_id)


@app.get("/api/reports/export")
def export_report(
    format: str = "csv",
    privacy: str = "full",
    student_id: str | None = None,
    title: str = Query(default="班級成績報告", max_length=100),
    include_stats: bool = True,
    include_qr: bool = False,
) -> Response:
    content, media_type, filename = reports.export(format, privacy, student_id, title, include_stats, include_qr)
    encoded_filename = quote(filename)
    return Response(content, media_type=media_type, headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"})


@app.get("/api/reports/batch")
def export_batch_reports(
    format: str = "pdf",
    privacy: str = "full",
    title: str = Query(default="個人成績單", max_length=100),
    include_qr: bool = False,
) -> Response:
    content, media_type, filename = reports.export_batch(format, privacy, title, include_qr)
    encoded_filename = quote(filename)
    return Response(content, media_type=media_type, headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"})


@app.post("/api/backups")
def create_backup() -> dict:
    return backups.create_backup()


@app.get("/api/backups")
def backup_history() -> list[dict]:
    return backups.history()