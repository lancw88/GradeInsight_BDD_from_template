"""
數據模型定義 - 使用 SQLAlchemy ORM
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from typing import Optional, List
import json

db = SQLAlchemy()


class Student(db.Model):
    """學生模型"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    class_name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    
    # 關聯
    grades = db.relationship('Grade', backref='student', cascade='all, delete-orphan')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Student {self.student_id}: {self.name}>'
    
    active_scheme_id = db.Column(db.Integer, db.ForeignKey('scoring_schemes.id'))
    rule_adjustment = db.Column(db.Float, default=0.0)
    attendance_count = db.Column(db.Integer, default=0)

    active_scheme = db.relationship('ScoringScheme', foreign_keys=[active_scheme_id])
    view_logs = db.relationship('StudentViewLog', backref='student', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'name': self.name,
            'class_name': self.class_name,
            'email': self.email,
            'attendance_count': self.attendance_count,
            'rule_adjustment': self.rule_adjustment,
        }


class GradeComponent(db.Model):
    """成績組件定義（如：期中考試、期末考試、作業等）"""
    __tablename__ = 'grade_components'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # 例如："期中考"
    description = db.Column(db.Text)
    weight = db.Column(db.Float, default=1.0)  # 權重
    max_score = db.Column(db.Float, default=100.0)
    min_score = db.Column(db.Float, default=0.0)
    component_type = db.Column(db.String(50), default='exam')  # exam, assignment, participation, etc.
    
    # 關聯
    grades = db.relationship('Grade', backref='component', cascade='all, delete-orphan')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<GradeComponent {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'weight': self.weight,
            'max_score': self.max_score,
        }


class Grade(db.Model):
    """單個成績記錄"""
    __tablename__ = 'grades'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    component_id = db.Column(db.Integer, db.ForeignKey('grade_components.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    remarks = db.Column(db.Text)  # 備註
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('student_id', 'component_id', name='unique_student_component'),)
    
    def __repr__(self):
        return f'<Grade Student:{self.student_id} Component:{self.component_id} Score:{self.score}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'component': self.component.to_dict() if self.component else None,
            'score': float(self.score),
            'remarks': self.remarks,
        }


class ScoringScheme(db.Model):
    """評分方案"""
    __tablename__ = 'scoring_schemes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    # JSON 格式存儲規則: {"component_id": weight, ...}
    rules = db.Column(db.Text, nullable=False)
    
    # 計算方法: 'weighted_average', 'simple_average', 'highest', 'custom'
    calculation_method = db.Column(db.String(50), default='weighted_average')
    
    # 是否為預設方案
    is_default = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_rules(self) -> dict:
        try:
            return json.loads(self.rules)
        except:
            return {}
    
    def set_rules(self, rules: dict):
        self.rules = json.dumps(rules)
    
    def __repr__(self):
        return f'<ScoringScheme {self.name}>'


class AdjustmentRule(db.Model):
    """成績自動調整規則"""
    __tablename__ = 'adjustment_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # 例如："缺勤3次扣5分"
    description = db.Column(db.Text)
    
    # 規則條件: JSON 格式
    condition = db.Column(db.Text, nullable=False)  # 例如: {"absence_count": {"gte": 3}}
    
    # 規則類型: 'deduct', 'award', 'percentage_adjust'
    rule_type = db.Column(db.String(50), nullable=False)
    
    # 調整值: 如 -5 (扣分) 或 +3 (加分) 或 0.9 (90% - 百分比)
    adjustment_value = db.Column(db.Float, nullable=False)
    
    # 應用於哪個組件（可為 NULL 表示影響最終分數）
    component_id = db.Column(db.Integer, db.ForeignKey('grade_components.id'))
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_condition(self) -> dict:
        try:
            return json.loads(self.condition)
        except:
            return {}


class AuditLog(db.Model):
    """審計日誌 - 記錄所有成績修改"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 操作類型: 'import', 'edit', 'delete', 'rule_apply', 'scheme_apply'
    operation_type = db.Column(db.String(50), nullable=False, index=True)
    
    # 涉及的學生和組件
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
    component_id = db.Column(db.Integer, db.ForeignKey('grade_components.id'))
    
    # 修改信息
    old_value = db.Column(db.Float)
    new_value = db.Column(db.Float)
    reason = db.Column(db.Text)  # 修改原因
    
    # 操作人（在全功能應用中應該有用戶信息）
    operator = db.Column(db.String(100), default='system')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    student = db.relationship('Student', foreign_keys=[student_id], backref='audit_logs')
    component = db.relationship('GradeComponent', foreign_keys=[component_id])

    def __repr__(self):
        return f'<AuditLog {self.operation_type} at {self.created_at}>'


class ReportTemplate(db.Model):
    """報告範本"""
    __tablename__ = 'report_templates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    fields = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_fields(self):
        try:
            return json.loads(self.fields)
        except:
            return []

    def set_fields(self, fields):
        self.fields = json.dumps(fields)

    def __repr__(self):
        return f'<ReportTemplate {self.name}>'


class SchemeApplicationLog(db.Model):
    """評分方案套用紀錄"""
    __tablename__ = 'scheme_application_logs'

    id = db.Column(db.Integer, primary_key=True)
    scheme_id = db.Column(db.Integer, db.ForeignKey('scoring_schemes.id'), nullable=False)
    operator = db.Column(db.String(100), default='system')
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_reverted = db.Column(db.Boolean, default=False)
    reverted_at = db.Column(db.DateTime)
    previous_scheme_id = db.Column(db.Integer)
    description = db.Column(db.Text)

    def __repr__(self):
        return f'<SchemeApplicationLog {self.scheme_id} at {self.applied_at}>'


class RuleApplicationLog(db.Model):
    """調整規則套用紀錄"""
    __tablename__ = 'rule_application_logs'

    id = db.Column(db.Integer, primary_key=True)
    rule_id = db.Column(db.Integer, db.ForeignKey('adjustment_rules.id'), nullable=False)
    operator = db.Column(db.String(100), default='system')
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_reverted = db.Column(db.Boolean, default=False)
    reverted_at = db.Column(db.DateTime)
    summary = db.Column(db.Text)

    def __repr__(self):
        return f'<RuleApplicationLog {self.rule_id} at {self.applied_at}>'


class StudentViewLog(db.Model):
    """學生檢視日誌"""
    __tablename__ = 'student_view_logs'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    viewer = db.Column(db.String(100), default='system')
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<StudentViewLog student={self.student_id} at {self.viewed_at}>'


class BackupLog(db.Model):
    """備份日誌"""
    __tablename__ = 'backup_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    backup_file = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer)  # 字節
    
    # 備份狀態: 'success', 'failed', 'pending'
    status = db.Column(db.String(20), default='pending')
    
    # 失敗原因
    error_message = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    completed_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<BackupLog {self.status} - {self.created_at}>'


def migrate_schema():
    """
    遷移舊schema以添加缺失的欄位
    在db.create_all()之後調用
    """
    from sqlalchemy import inspect
    import sqlite3
    
    inspector = inspect(db.engine)
    existing_columns = {col['name'] for col in inspector.get_columns('students')}
    
    missing_columns = [
        ('active_scheme_id', 'INTEGER'),
        ('rule_adjustment', 'REAL'),
        ('attendance_count', 'INTEGER'),
    ]
    
    conn = sqlite3.connect(db.engine.url.database)
    cursor = conn.cursor()
    
    for col_name, col_type in missing_columns:
        if col_name not in existing_columns:
            default_val = "0.0" if col_type == 'REAL' else "0"
            cursor.execute(f"ALTER TABLE students ADD COLUMN {col_name} {col_type} DEFAULT {default_val}")
            print(f"✓ 已添加欄位: {col_name}")
    
    conn.commit()
    conn.close()
