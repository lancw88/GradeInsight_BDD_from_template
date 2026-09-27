import csv
import io
import tempfile
import unittest
import zipfile
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from backend.services.analysis_service import AnalysisService
from backend.services.backup_service import BackupService
from backend.services.import_service import ImportService
from backend.services.report_service import ReportService
from backend.services.scoring_service import ScoringService
from backend.services.storage import GradeStore
from backend.services.student_service import StudentService


class GradeServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.store = GradeStore(self.root / "grades.sqlite3")
        self.store.initialize()
        self.students = StudentService(self.store)
        self.students.ensure_default_scheme()
        self.students.generate_demo_students(30)
        self.analysis = AnalysisService(self.students)
        self.scoring = ScoringService(self.store, self.students)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_demo_data_and_statistics(self) -> None:
        rows = self.students.list_students()
        result = self.analysis.analyze(bin_width=5)
        self.assertEqual(len(rows), 30)
        self.assertEqual(result["count"], 30)
        self.assertAlmostEqual(sum(item["count"] for item in result["grade_counts"].values()), 30)
        self.assertEqual(len(result["histogram"]), 20)

    def test_import_preview_skips_duplicates_and_invalid_rows(self) -> None:
        content = (
            "student_id,name,class_name,coursework,midterm,final\n"
            "T001,王小明,二年甲班,80,75,90\n"
            "T001,重複學生,二年甲班,70,70,70\n"
            "T002,錯誤學生,二年甲班,101,60,60\n"
        ).encode("utf-8")
        preview = ImportService(self.store).preview("grades.csv", content)
        self.assertEqual(preview["valid_count"], 1)
        self.assertEqual(preview["duplicate_count"], 1)
        self.assertEqual(preview["invalid_count"], 1)
        outcome = ImportService(self.store).commit(preview["records"])
        self.assertEqual(outcome["imported"], 1)

    def test_score_edit_is_audited_and_reversible(self) -> None:
        student = self.store.get_student("S001")
        original_score = student["scores"]["final"]
        self.students.edit_score("S001", "final", 99, "複核修正計分", "教師甲")
        self.assertEqual(self.store.audit_history("S001")[0]["reason"], "複核修正計分")
        self.assertEqual(self.students.undo_edit("S001")["scores"]["final"], original_score)
        self.assertIsNone(self.students.undo_edit("S001"))

    def test_rules_can_be_previewed_applied_undone_and_reapplied(self) -> None:
        first = self.scoring.create_rule({
            "name": "出席獎勵甲", "field": "attendance_rate", "operator": ">=", "threshold": 0,
            "adjustment_type": "bonus", "amount": 1,
        })
        second = self.scoring.create_rule({
            "name": "出席獎勵乙", "field": "attendance_rate", "operator": ">=", "threshold": 0,
            "adjustment_type": "bonus", "amount": 2,
        })
        self.assertEqual(self.scoring.preview_rule(first["id"])["affected_count"], 30)
        self.assertEqual(self.scoring.apply_rule(first["id"])["applied_count"], 30)
        self.assertEqual(self.scoring.apply_rule(first["id"])["applied_count"], 0)
        self.scoring.apply_rule(second["id"])
        self.scoring.undo_rule(first["id"])
        self.assertAlmostEqual(self.store.get_student("S001")["adjustments"], 2)
        self.assertEqual(self.scoring.apply_rule(first["id"])["applied_count"], 30)
        self.assertAlmostEqual(self.store.get_student("S001")["adjustments"], 3)

    def test_exports_produce_csv_xlsx_and_pdf(self) -> None:
        service = ReportService(self.students, self.analysis)
        csv_bytes, _, _ = service.export("csv")
        csv_rows = list(csv.reader(io.StringIO(csv_bytes.decode("utf-8-sig"))))
        self.assertIn("學號", csv_rows[2])
        xlsx_bytes, _, _ = service.export("xlsx", privacy="anonymous")
        self.assertTrue(xlsx_bytes.startswith(b"PK"))
        pdf_bytes, _, _ = service.export("pdf", include_qr=True)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        batch_bytes, _, _ = service.export_batch("csv", privacy="anonymous")
        with zipfile.ZipFile(io.BytesIO(batch_bytes)) as archive:
            self.assertEqual(len(archive.namelist()), 30)

    def test_backup_is_encrypted_and_logged(self) -> None:
        service = BackupService(self.store, self.root / "backups")
        backup = service.create_backup()
        encrypted = (self.root / "backups" / backup["filename"]).read_bytes()
        self.assertEqual(encrypted[:3], b"GI1")
        snapshot = AESGCM(service.key).decrypt(encrypted[3:15], encrypted[15:], b"GradeInsight backup v1")
        self.assertIn(b"students", snapshot)
        self.assertEqual(service.history()[0]["status"], "success")


if __name__ == "__main__":
    unittest.main()