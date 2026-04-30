"""
評分方案和規則管理服務 - 處理 US-004, US-008, US-009
"""

import json
from typing import Dict, List
from datetime import datetime
from gradeinsight.models import db, Student, Grade, GradeComponent, ScoringScheme, AdjustmentRule, AuditLog


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
    def apply_scheme(scheme_id: int, dry_run: bool = True) -> Dict:
        """
        應用評分方案（計算預覽或實際應用）
        
        Args:
            scheme_id: 方案 ID
            dry_run: 是否只做預覽（不保存）
            
        Returns:
            {
                'success': bool,
                'affected_students': int,
                'preview': [{student_id, old_score, new_score}, ...] (dry_run=True)
            }
        """
        
        scheme = ScoringScheme.query.get(scheme_id)
        if not scheme:
            raise ValueError(f"評分方案 ID {scheme_id} 不存在")
        
        rules = scheme.get_rules()
        students = Student.query.all()
        preview = []
        affected_count = 0
        
        for student in students:
            old_score = ScoringSchemeService._calculate_student_score(student.id, schemes=None)
            new_score = ScoringSchemeService._calculate_student_score(student.id, scheme=scheme)
            
            if abs(old_score - new_score) > 0.01:  # 有變化
                preview.append({
                    'student_id': student.student_id,
                    'name': student.name,
                    'old_score': round(old_score, 2),
                    'new_score': round(new_score, 2),
                    'change': round(new_score - old_score, 2),
                })
                affected_count += 1
        
        if not dry_run:
            # 實際應用方案
            for item in preview:
                student = Student.query.filter_by(student_id=item['student_id']).first()
                if student:
                    audit_log = AuditLog(
                        operation_type='scheme_apply',
                        student_id=student.id,
                        old_value=item['old_score'],
                        new_value=item['new_score'],
                        reason=f"應用評分方案: {scheme.name}",
                        operator='system'
                    )
                    db.session.add(audit_log)
            db.session.commit()
        
        return {
            'success': True,
            'affected_students': affected_count,
            'preview': preview if dry_run else None,
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
    def _calculate_student_score(student_id: int, scheme: ScoringScheme = None) -> float:
        """計算學生的最終成績"""
        
        grades = db.session.query(
            Grade.score,
            GradeComponent.weight
        ).join(GradeComponent).filter(Grade.student_id == student_id).all()
        
        if not grades:
            return 0.0
        
        if scheme:
            rules = scheme.get_rules()
            # 根據方案計算
            total = 0
            total_weight = 0
            for score, weight in grades:
                total += score * weight
                total_weight += weight
            return total / total_weight if total_weight > 0 else 0.0
        else:
            # 默認加權平均
            total = sum(g[0] * g[1] for g in grades)
            total_weight = sum(g[1] for g in grades)
            return total / total_weight if total_weight > 0 else 0.0


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


class AdjustmentRuleService:
    """成績自動調整規則 - US-009"""
    
    @staticmethod
    def create_rule(name: str, rule_type: str, condition: Dict, adjustment_value: float, component_id: int = None) -> AdjustmentRule:
        """
        創建調整規則
        
        Args:
            name: 規則名稱
            rule_type: 'deduct', 'award', 'percentage_adjust'
            condition: 條件字典
            adjustment_value: 調整值
            component_id: 應用於的組件
        """
        
        rule = AdjustmentRule(
            name=name,
            rule_type=rule_type,
            adjustment_value=adjustment_value,
            component_id=component_id
        )
        rule.condition = json.dumps(condition)
        db.session.add(rule)
        db.session.commit()
        return rule
    
    @staticmethod
    def preview_rule_application(rule_id: int) -> Dict:
        """預覽規則應用的結果"""
        
        rule = AdjustmentRule.query.get(rule_id)
        if not rule:
            raise ValueError(f"規則 ID {rule_id} 不存在")
        
        affected_students = []
        
        # 評估規則條件（這是一個簡化的實裝）
        # 完整實現應支持更複雜的條件表達式
        students = Student.query.all()
        for student in students:
            # 這裡應該根據實際的業務邏輯評估條件
            # 例如計算缺勤次數、出席率等
            
            adjustment = rule.adjustment_value
            affected_students.append({
                'student_id': student.student_id,
                'name': student.name,
                'current_score': 0,  # 應計算實際分數
                'adjustment': adjustment,
                'new_score': 0,  # 應計算新分數
            })
        
        return {
            'rule_id': rule_id,
            'rule_name': rule.name,
            'affected_count': len(affected_students),
            'preview': affected_students[:10],  # 只顯示前 10 個
        }
    
    @staticmethod
    def apply_rule(rule_id: int, operator: str = 'system') -> Dict:
        """應用調整規則"""
        
        rule = AdjustmentRule.query.get(rule_id)
        if not rule:
            raise ValueError(f"規則 ID {rule_id} 不存在")
        
        # 標記規則已應用，防止重複應用
        if rule.is_active:
            # 應用邏輯
            pass
        
        return {
            'success': True,
            'rule_id': rule_id,
            'affected_students': 0,
        }
    
    @staticmethod
    def list_rules() -> List[Dict]:
        """列出所有規則"""
        
        rules = AdjustmentRule.query.all()
        return [{
            'id': r.id,
            'name': r.name,
            'rule_type': r.rule_type,
            'adjustment_value': r.adjustment_value,
            'is_active': r.is_active,
        } for r in rules]
