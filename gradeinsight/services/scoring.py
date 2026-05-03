"""
評分方案和規則管理服務 - 處理 US-004, US-008, US-009
"""

import json
from typing import Dict, List, Optional
from datetime import datetime
from gradeinsight.models import (
    db,
    Student,
    Grade,
    GradeComponent,
    ScoringScheme,
    AdjustmentRule,
    AuditLog,
    SchemeApplicationLog,
    RuleApplicationLog,
)


class ScoringSchemeService:
    """評分方案管理"""
    
    @staticmethod
    def create_scheme(name: str, description: str, calculation_method: str, rules: Dict) -> ScoringScheme:
        """
        創建評分方案
        
        Args:
            name: 方案名稱
            description: 描述
            calculation_method: 'weighted_average', 'simple_average', 'highest', 'custom'
            rules: {component_id: weight}
        """
        
        scheme = ScoringScheme(
            name=name,
            description=description,
            calculation_method=calculation_method,
        )
        scheme.set_rules(rules)
        db.session.add(scheme)
        db.session.commit()
        return scheme
    
    @staticmethod
    def get_scheme_details(scheme_id: int) -> Dict:
        scheme = ScoringScheme.query.get(scheme_id)
        if not scheme:
            raise ValueError(f"評分方案 ID {scheme_id} 不存在")
        return {
            'id': scheme.id,
            'name': scheme.name,
            'description': scheme.description,
            'calculation_method': scheme.calculation_method,
            'rules': scheme.get_rules(),
            'is_default': scheme.is_default,
        }

    @staticmethod
    def list_schemes() -> List[Dict]:
        """列出所有評分方案"""
        schemes = ScoringScheme.query.all()
        return [{
            'id': s.id,
            'name': s.name,
            'description': s.description,
            'calculation_method': s.calculation_method,
            'is_default': s.is_default,
        } for s in schemes]
    
    @staticmethod
    def preview_scheme_application(scheme_id: int) -> Dict:
        scheme = ScoringScheme.query.get(scheme_id)
        if not scheme:
            raise ValueError(f"評分方案 ID {scheme_id} 不存在")

        students = Student.query.all()
        preview = []
        for student in students:
            old_score = ScoringSchemeService._calculate_student_score(student.id)
            new_score = ScoringSchemeService._calculate_student_score(student.id, scheme=scheme)
            preview.append({
                'student_id': student.student_id,
                'name': student.name,
                'old_score': round(old_score, 2),
                'new_score': round(new_score, 2),
                'change': round(new_score - old_score, 2),
            })

        return {
            'scheme_id': scheme.id,
            'scheme_name': scheme.name,
            'preview': preview,
        }

    @staticmethod
    def apply_scheme(scheme_id: int, dry_run: bool = True, operator: str = 'system') -> Dict:
        scheme = ScoringScheme.query.get(scheme_id)
        if not scheme:
            raise ValueError(f"評分方案 ID {scheme_id} 不存在")

        preview_data = ScoringSchemeService.preview_scheme_application(scheme_id)['preview']
        affected_count = sum(1 for row in preview_data if abs(row['change']) > 0.01)

        if not dry_run:
            previous_scheme_id = None
            students = Student.query.all()
            if students:
                previous_scheme_id = students[0].active_scheme_id
            for student in students:
                student.active_scheme_id = scheme_id
            db.session.add(SchemeApplicationLog(
                scheme_id=scheme_id,
                operator=operator,
                previous_scheme_id=previous_scheme_id,
                description=f"應用評分方案 {scheme.name}",
            ))
            for row in preview_data:
                student = Student.query.filter_by(student_id=row['student_id']).first()
                if student:
                    audit_log = AuditLog(
                        operation_type='scheme_apply',
                        student_id=student.id,
                        old_value=row['old_score'],
                        new_value=row['new_score'],
                        reason=f"應用評分方案: {scheme.name}",
                        operator=operator,
                    )
                    db.session.add(audit_log)
            db.session.commit()

        return {
            'success': True,
            'affected_students': affected_count,
            'preview': preview_data if dry_run else None,
        }

    @staticmethod
    def undo_scheme_application(application_id: int, operator: str = 'system') -> bool:
        application = SchemeApplicationLog.query.get(application_id)
        if not application or application.is_reverted:
            return False

        previous_scheme_id = application.previous_scheme_id
        students = Student.query.all()
        for student in students:
            student.active_scheme_id = previous_scheme_id
        application.is_reverted = True
        application.reverted_at = datetime.utcnow()
        db.session.commit()
        return True

    @staticmethod
    def _calculate_student_score(student_id: int, scheme: Optional[ScoringScheme] = None) -> float:
        grades = db.session.query(
            Grade.score,
            GradeComponent.weight,
            Grade.component_id
        ).join(GradeComponent).filter(Grade.student_id == student_id).all()

        student = Student.query.get(student_id)
        if not grades:
            return (student.rule_adjustment or 0.0) if student else 0.0

        if scheme is None and student and student.active_scheme_id:
            scheme = ScoringScheme.query.get(student.active_scheme_id)

        total = 0
        total_weight = 0
        if scheme is not None:
            scheme_rules = scheme.get_rules()
            for score, _, component_id in grades:
                weight = scheme_rules.get(str(component_id), None)
                if weight is None:
                    weight = next((w for _, w, cid in grades if cid == component_id), 1.0)
                total += score * weight
                total_weight += weight
        else:
            for score, weight, _ in grades:
                total += score * weight
                total_weight += weight

        base_score = total / total_weight if total_weight > 0 else 0.0
        result = base_score
        if student:
            result += student.rule_adjustment or 0.0
        return result


class GradeEditService:
    """成績編輯服務 - US-008"""
    
    @staticmethod
    def edit_grade(grade_id: int, new_score: float, reason: str, operator: str = 'system') -> Grade:
        """
        編輯成績
        
        Args:
            grade_id: 成績 ID
            new_score: 新分數
            reason: 修改原因
            operator: 操作人
        """
        
        grade = Grade.query.get(grade_id)
        if not grade:
            raise ValueError(f"成績 ID {grade_id} 不存在")
        
        # 驗證分數範圍
        component = grade.component
        if not (component.min_score <= new_score <= component.max_score):
            raise ValueError(f"分數必須在 {component.min_score}-{component.max_score} 之間")
        
        old_score = grade.score
        
        # 記錄審計日誌
        audit_log = AuditLog(
            operation_type='edit',
            student_id=grade.student_id,
            component_id=grade.component_id,
            old_value=old_score,
            new_value=new_score,
            reason=reason,
            operator=operator
        )
        db.session.add(audit_log)
        
        # 更新成績
        grade.score = new_score
        grade.updated_at = datetime.utcnow()
        db.session.commit()
        
        return grade
    
    @staticmethod
    def get_audit_history(student_id: int = None, limit: int = 100) -> List[Dict]:
        """獲取審計日誌"""
        
        query = AuditLog.query
        if student_id:
            query = query.filter_by(student_id=student_id)
        
        logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
        
        return [{
            'id': log.id,
            'operation_type': log.operation_type,
            'student_name': log.student.name if log.student else 'N/A',
            'old_value': log.old_value,
            'new_value': log.new_value,
            'reason': log.reason,
            'operator': log.operator,
            'created_at': log.created_at.isoformat(),
        } for log in logs]

    @staticmethod
    def undo_last_edit(student_id: int) -> bool:
        last_log = AuditLog.query.filter_by(student_id=student_id, operation_type='edit').order_by(AuditLog.created_at.desc()).first()
        if not last_log:
            return False

        grade = Grade.query.filter_by(student_id=student_id, component_id=last_log.component_id).first()
        if not grade:
            return False

        grade.score = last_log.old_value
        audit_log = AuditLog(
            operation_type='edit',
            student_id=student_id,
            component_id=last_log.component_id,
            old_value=last_log.new_value,
            new_value=last_log.old_value,
            reason=f"撤銷編輯: {last_log.reason}",
            operator='system'
        )
        db.session.add(audit_log)
        db.session.commit()
        return True


class AdjustmentRuleService:
    """成績自動調整規則 - US-009"""
    
    @staticmethod
    def create_rule(name: str, rule_type: str, condition: Dict, adjustment_value: float, component_id: int = None) -> AdjustmentRule:
        rule = AdjustmentRule(
            name=name,
            rule_type=rule_type,
            adjustment_value=adjustment_value,
            component_id=component_id,
            is_active=True,
        )
        rule.condition = json.dumps(condition)
        db.session.add(rule)
        db.session.commit()
        return rule
    
    @staticmethod
    def preview_rule_application(rule_id: int) -> Dict:
        rule = AdjustmentRule.query.get(rule_id)
        if not rule:
            raise ValueError(f"規則 ID {rule_id} 不存在")
        
        condition = rule.get_condition()
        students = Student.query.all()
        affected_students = []
        total_adjustment = 0
        adjustments = []

        for student in students:
            adjustment = AdjustmentRuleService._evaluate_rule(rule, student)
            if adjustment != 0:
                current_score = ScoringSchemeService._calculate_student_score(student.id)
                new_score = current_score + adjustment
                affected_students.append({
                    'student_id': student.student_id,
                    'name': student.name,
                    'current_score': round(current_score, 2),
                    'adjustment': adjustment,
                    'new_score': round(new_score, 2),
                })
                total_adjustment += adjustment
                adjustments.append(adjustment)

        max_adj = max(adjustments) if adjustments else 0
        min_adj = min(adjustments) if adjustments else 0
        avg_adj = round(total_adjustment / len(adjustments), 2) if adjustments else 0

        return {
            'rule_id': rule_id,
            'rule_name': rule.name,
            'affected_count': len(affected_students),
            'preview': affected_students,
            'summary': {
                '受影響學生數': len(affected_students),
                '最大扣分': f"{min_adj}分" if min_adj < 0 else f"{max_adj}分",
                '最小扣分': f"{max_adj}分" if max_adj > 0 else f"{min_adj}分",
                '平均扣分': f"{avg_adj}分",
            }
        }
    
    @staticmethod
    def apply_rule(rule_id: int, operator: str = 'system') -> Dict:
        rule = AdjustmentRule.query.get(rule_id)
        if not rule:
            raise ValueError(f"規則 ID {rule_id} 不存在")
        if not rule.is_active:
            raise ValueError(f"規則 {rule.name} 已停用，不可重複套用")

        preview = AdjustmentRuleService.preview_rule_application(rule_id)
        affected = preview['preview']
        for row in affected:
            student = Student.query.filter_by(student_id=row['student_id']).first()
            if student:
                student.rule_adjustment += row['adjustment']
                audit_log = AuditLog(
                    operation_type='rule_apply',
                    student_id=student.id,
                    old_value=row['current_score'],
                    new_value=row['new_score'],
                    reason=f"套用規則: {rule.name}",
                    operator=operator,
                )
                db.session.add(audit_log)

        rule.is_active = False
        log_summary = {
            'affected_count': len(affected),
            'max_adjustment': preview['summary']['最大扣分'],
            'min_adjustment': preview['summary']['最小扣分'],
            'average_adjustment': preview['summary']['平均扣分'],
        }
        db.session.add(RuleApplicationLog(
            rule_id=rule.id,
            operator=operator,
            summary=json.dumps(log_summary),
        ))
        db.session.commit()

        return {
            'success': True,
            'rule_id': rule_id,
            'affected_students': len(affected),
            'summary': preview['summary'],
        }
    
    @staticmethod
    def undo_rule_application(rule_id: int) -> bool:
        rule = AdjustmentRule.query.get(rule_id)
        if not rule:
            return False
        if rule.is_active:
            return False
        applications = RuleApplicationLog.query.filter_by(rule_id=rule.id, is_reverted=False).order_by(RuleApplicationLog.applied_at.desc()).all()
        if not applications:
            return False
        application = applications[0]

        students = Student.query.all()
        for student in students:
            adjustment = AdjustmentRuleService._evaluate_rule(rule, student)
            if adjustment != 0:
                student.rule_adjustment -= adjustment
        application.is_reverted = True
        application.reverted_at = datetime.utcnow()
        rule.is_active = True
        db.session.commit()
        return True
    
    @staticmethod
    def list_rules() -> List[Dict]:
        rules = AdjustmentRule.query.all()
        return [{
            'id': r.id,
            'name': r.name,
            'rule_type': r.rule_type,
            'adjustment_value': r.adjustment_value,
            'is_active': r.is_active,
        } for r in rules]

    @staticmethod
    def _evaluate_rule(rule: AdjustmentRule, student: Student) -> float:
        condition = rule.get_condition()
        if 'absence_count' in condition:
            absence = student.attendance_count
            for entry in condition.get('absence_count', []):
                min_count = entry.get('min', 0)
                max_count = entry.get('max', None)
                if max_count is None and absence >= min_count:
                    return entry.get('adjustment', 0)
                if max_count is not None and min_count <= absence <= max_count:
                    return entry.get('adjustment', 0)
        return 0.0
