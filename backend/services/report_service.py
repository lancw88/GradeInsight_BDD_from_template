import csv
import io
import zipfile
from datetime import datetime
from typing import Any

from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

from .analysis_service import AnalysisService
from .student_service import COMPONENT_LABELS, StudentService


class ReportService:
    def __init__(self, students: StudentService, analysis: AnalysisService) -> None:
        self.students = students
        self.analysis = analysis

    def export(
        self,
        format_name: str,
        privacy: str = "full",
        student_id: str | None = None,
        title: str = "班級成績報告",
        include_stats: bool = True,
        include_qr: bool = False,
    ) -> tuple[bytes, str, str]:
        rows = self.students.list_students()
        if student_id:
            rows = [row for row in rows if row["student_id"] == student_id]
            if not rows:
                raise KeyError("找不到指定學生")
        rows = [self._apply_privacy(row, privacy) for row in rows]
        stats = self.analysis.analyze() if include_stats and not student_id else None
        fields = ["student_id", "name", "class_name", "coursework", "midterm", "final", "final_score", "grade"]
        if format_name == "csv":
            return self._csv(rows, fields, stats, title), "text/csv; charset=utf-8", "成績報告.csv"
        if format_name == "xlsx":
            return self._xlsx(rows, fields, stats, title), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "成績報告.xlsx"
        if format_name == "pdf":
            return self._pdf(rows, fields, stats, title, include_qr), "application/pdf", "成績報告.pdf"
        raise ValueError("匯出格式需為 CSV、Excel 或 PDF")

    def export_batch(
        self, format_name: str, privacy: str = "full", title: str = "個人成績單", include_qr: bool = False
    ) -> tuple[bytes, str, str]:
        students = self.students.list_students()
        if not students:
            raise ValueError("目前沒有可匯出的學生資料")
        archive_buffer = io.BytesIO()
        with zipfile.ZipFile(archive_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
            extension = {"csv": "csv", "xlsx": "xlsx", "pdf": "pdf"}.get(format_name)
            if not extension:
                raise ValueError("匯出格式需為 CSV、Excel 或 PDF")
            for index, student in enumerate(students, start=1):
                content, _, _ = self.export(
                    format_name,
                    privacy,
                    student_id=student["student_id"],
                    title=title,
                    include_stats=False,
                    include_qr=include_qr,
                )
                archive.writestr(f"student_{index:03d}.{extension}", content)
        return archive_buffer.getvalue(), "application/zip", "個人成績單_批次.zip"

    @staticmethod
    def _apply_privacy(row: dict[str, Any], privacy: str) -> dict[str, Any]:
        if privacy not in {"full", "masked", "anonymous"}:
            raise ValueError("隱私級別需為 full、masked 或 anonymous")
        exported = {**row, "coursework": row["scores"]["coursework"], "midterm": row["scores"]["midterm"], "final": row["scores"]["final"]}
        if privacy == "masked":
            exported["student_id"] = "*" * max(0, len(row["student_id"]) - 2) + row["student_id"][-2:]
            exported["name"] = row["name"][:1] + "＊"
        elif privacy == "anonymous":
            exported["student_id"] = "匿名"
            exported["name"] = "匿名學生"
            exported["class_name"] = ""
        return exported

    @staticmethod
    def _csv(rows: list[dict[str, Any]], fields: list[str], stats: dict[str, Any] | None, title: str) -> bytes:
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow([title])
        if stats:
            writer.writerow(["平均分", stats["statistics"]["mean"], "及格率", stats["statistics"]["pass_rate"]])
        labels = {"student_id": "學號", "name": "姓名", "class_name": "班級", "coursework": "平時", "midterm": "期中", "final": "期末", "final_score": "總成績", "grade": "等級"}
        writer.writerow([labels[field] for field in fields])
        for row in rows:
            writer.writerow([row.get(field, "") for field in fields])
        return ("\ufeff" + output.getvalue()).encode("utf-8")

    @staticmethod
    def _xlsx(rows: list[dict[str, Any]], fields: list[str], stats: dict[str, Any] | None, title: str) -> bytes:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "成績報告"
        sheet.append([title])
        if stats:
            sheet.append(["平均分", stats["statistics"]["mean"], "及格率（%）", stats["statistics"]["pass_rate"]])
        labels = {"student_id": "學號", "name": "姓名", "class_name": "班級", "coursework": "平時", "midterm": "期中", "final": "期末", "final_score": "總成績", "grade": "等級"}
        sheet.append([labels[field] for field in fields])
        for row in rows:
            sheet.append([row.get(field, "") for field in fields])
        sheet.freeze_panes = "A4" if stats else "A3"
        output = io.BytesIO()
        workbook.save(output)
        return output.getvalue()

    @staticmethod
    def _pdf(rows: list[dict[str, Any]], fields: list[str], stats: dict[str, Any] | None, title: str, include_qr: bool) -> bytes:
        output = io.BytesIO()
        document = SimpleDocTemplate(output, pagesize=landscape(A4), title=title)
        styles = getSampleStyleSheet()
        content: list[Any] = [Paragraph(title, styles["Title"]), Spacer(1, 12)]
        if stats:
            values = stats["statistics"]
            content.append(Paragraph(f"平均分：{values['mean']}　及格率：{values['pass_rate']}%　優良率：{values['excellent_rate']}%", styles["Normal"]))
            content.append(Spacer(1, 10))
        labels = {"student_id": "學號", "name": "姓名", "class_name": "班級", "coursework": "平時", "midterm": "期中", "final": "期末", "final_score": "總成績", "grade": "等級"}
        table_data = [[labels[field] for field in fields]]
        table_data.extend([[str(row.get(field, "")) for field in fields] for row in rows])
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#244b45")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#b8c8c2")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eff4f1")]),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        content.append(table)
        if include_qr:
            code = QrCodeWidget(f"GradeInsight:{datetime.now().date().isoformat()}:{len(rows)}")
            bounds = code.getBounds()
            size = 70
            drawing = Drawing(size, size, transform=[size / (bounds[2] - bounds[0]), 0, 0, size / (bounds[3] - bounds[1]), 0, 0])
            drawing.add(code)
            content.extend([Spacer(1, 12), Paragraph("報告識別 QR Code", styles["Normal"]), drawing])
        document.build(content)
        return output.getvalue()