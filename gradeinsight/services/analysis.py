"""
成績分析和統計服務 - 處理 US-002, US-003, US-006, US-007
"""

import statistics
from typing import Dict, List, Tuple
from sqlalchemy import func
from gradeinsight.models import db, Student, Grade, GradeComponent, AuditLog


class GradeAnalysisService:
    """成績分析服務"""
    
    @staticmethod
    def get_grade_distribution(component_id: int = None, bin_width: int = 10) -> Dict:
        """
        獲取成績分布
        
        Args:
            component_id: 特定組件，若為 None 則計算最終成績
            bin_width: 分數段寬度
            
        Returns:
            {
                'bins': [成績段位],
                'counts': [各段人數],
                'statistics': {平均分、中位數、標準差等}
            }
        """
        
        # 獲取所有相關成績
        if component_id:
            grades = db.session.query(Grade.score).filter_by(component_id=component_id).all()
        else:
            # 計算最終成績（加權平均）
            grades = GradeAnalysisService._calculate_final_grades()
        
        scores = [g[0] if isinstance(g, tuple) else g for g in grades if g and g[0] is not None]
        
        if not scores:
            return {
                'bins': [],
                'counts': [],
                'statistics': {
                    'mean': 0,
                    'median': 0,
                    'mode': 0,
                    'std_dev': 0,
                    'variance': 0,
                    'min': 0,
                    'max': 0,
                    'total_count': 0,
                }
            }
        
        # 生成分布
        min_score = min(scores)
        max_score = max(scores)
        bins = []
        counts = []
        
        current = int(min_score // bin_width) * bin_width
        while current <= max_score:
            bin_label = f"{current}-{current + bin_width - 1}"
            count = sum(1 for s in scores if current <= s < current + bin_width)
            bins.append(bin_label)
            counts.append(count)
            current += bin_width
        
        # 計算統計信息
        try:
            mode = statistics.mode(scores)
        except:
            mode = 0
        
        statistics_dict = {
            'mean': round(statistics.mean(scores), 2),
            'median': round(statistics.median(scores), 2),
            'mode': mode,
            'std_dev': round(statistics.stdev(scores), 2) if len(scores) > 1 else 0,
            'variance': round(statistics.variance(scores), 2) if len(scores) > 1 else 0,
            'min': min(scores),
            'max': max(scores),
            'total_count': len(scores),
        }
        
        return {
            'bins': bins,
            'counts': counts,
            'statistics': statistics_dict,
        }
    
    @staticmethod
    def get_grade_by_level() -> Dict:
        """按等級統計成績分布 (A, B, C, D, F)"""
        
        final_grades = GradeAnalysisService._calculate_final_grades()
        grades = [g[0] if isinstance(g, tuple) else g for g in final_grades if g and g[0] is not None]
        
        def get_level(score):
            if score >= 90:
                return 'A'
            elif score >= 80:
                return 'B'
            elif score >= 70:
                return 'C'
            elif score >= 60:
                return 'D'
            else:
                return 'F'
        
        level_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
        for score in grades:
            level = get_level(score)
            level_counts[level] += 1
        
        total = len(grades)
        return {
            'distribution': level_counts,
            'percentages': {k: round(v / total * 100, 2) if total > 0 else 0 for k, v in level_counts.items()},
            'pass_rate': round((total - level_counts['F']) / total * 100, 2) if total > 0 else 0,
            'excellent_rate': round(level_counts['A'] / total * 100, 2) if total > 0 else 0,
        }
    
    @staticmethod
    def identify_at_risk_students(pass_line: float = 60.0, risk_range: float = 10.0) -> List[Dict]:
        """
        識別風險學生
        
        Args:
            pass_line: 及格線
            risk_range: 風險範圍（±%)
            
        Returns:
            風險學生列表
        """
        
        final_grades = GradeAnalysisService._calculate_final_grades()
        
        at_risk = []
        for student_data in final_grades:
            if isinstance(student_data, tuple):
                student_id, final_score = student_data
            else:
                continue
            
            if final_score is None:
                continue
            
            risk_min = pass_line - risk_range
            risk_max = pass_line + risk_range
            
            if risk_min <= final_score <= pass_line:
                student = Student.query.get(student_id)
                if student:
                    at_risk.append({
                        'student_id': student.student_id,
                        'name': student.name,
                        'final_score': round(final_score, 2),
                        'gap_to_pass': round(pass_line - final_score, 2),
                        'risk_level': 'high' if final_score < pass_line else 'warning',
                    })
        
        return sorted(at_risk, key=lambda x: x['final_score'])
    
    @staticmethod
    def get_student_details(student_id: int) -> Dict:
        """
        獲取學生詳細信息
        
        Returns:
            {
                'student': {...},
                'grades_by_component': [...],
                'final_score': float,
                'class_rank': int,
                'comparison_to_average': {...}
            }
        """
        
        student = Student.query.get(student_id)
        if not student:
            raise ValueError(f"學生 ID {student_id} 不存在")
        
        # 獲取各組件成績
        grades_by_component = []
        total_weighted_score = 0
        total_weight = 0
        
        components = GradeComponent.query.all()
        for component in components:
            grade = Grade.query.filter_by(student_id=student_id, component_id=component.id).first()
            if grade:
                grades_by_component.append({
                    'component': component.name,
                    'score': grade.score,
                    'weight': component.weight,
                    'weighted_score': grade.score * component.weight,
                })
                total_weighted_score += grade.score * component.weight
                total_weight += component.weight
        
        final_score = total_weighted_score / total_weight if total_weight > 0 else 0
        
        # 計算班級排名
        class_rank = GradeAnalysisService._calculate_class_rank(student_id, final_score)
        
        # 計算與班級平均分的對比
        avg_score = GradeAnalysisService._get_class_average()
        
        return {
            'student': student.to_dict(),
            'grades_by_component': grades_by_component,
            'final_score': round(final_score, 2),
            'class_rank': class_rank,
            'comparison_to_average': {
                'average_score': round(avg_score, 2),
                'difference': round(final_score - avg_score, 2),
            }
        }
    
    @staticmethod
    def get_statistics_summary() -> Dict:
        """生成統計分析摘要"""
        
        final_grades = GradeAnalysisService._calculate_final_grades()
        grades = [g[0] if isinstance(g, tuple) else g for g in final_grades if g and g[0] is not None]
        
        if not grades:
            return {
                'total_students': 0,
                'statistics': {
                    'mean': 0,
                    'median': 0,
                    'std_dev': 0,
                },
                'grade_levels': {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0},
                'pass_rate': 0,
                'outliers': []
            }
        
        # 計算異常值（超過 2 個標準差）
        mean = statistics.mean(grades)
        std_dev = statistics.stdev(grades) if len(grades) > 1 else 0
        outliers = [g for g in grades if abs(g - mean) > 2 * std_dev]
        
        # 按等級分類
        grade_levels = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
        for score in grades:
            if score >= 90:
                grade_levels['A'] += 1
            elif score >= 80:
                grade_levels['B'] += 1
            elif score >= 70:
                grade_levels['C'] += 1
            elif score >= 60:
                grade_levels['D'] += 1
            else:
                grade_levels['F'] += 1
        
        return {
            'total_students': len(grades),
            'statistics': {
                'mean': round(mean, 2),
                'median': round(statistics.median(grades), 2),
                'std_dev': round(std_dev, 2),
                'min': min(grades),
                'max': max(grades),
            },
            'grade_levels': grade_levels,
            'pass_rate': round((len(grades) - grade_levels['F']) / len(grades) * 100, 2),
            'excellent_rate': round(grade_levels['A'] / len(grades) * 100, 2),
            'outliers': sorted(outliers),
        }
    
    # ========== 私有幫助方法 ==========
    
    @staticmethod
    def _calculate_final_grades() -> List[Tuple]:
        """計算所有學生的最終成績（加權平均）"""
        
        students = Student.query.all()
        results = []
        
        for student in students:
            grades = db.session.query(
                Grade.score,
                GradeComponent.weight
            ).join(GradeComponent).filter(Grade.student_id == student.id).all()
            
            if grades:
                total_weighted = sum(g[0] * g[1] for g in grades)
                total_weight = sum(g[1] for g in grades)
                final_score = total_weighted / total_weight if total_weight > 0 else 0
            else:
                final_score = None
            
            results.append((student.id, final_score))
        
        return results
    
    @staticmethod
    def _calculate_class_rank(student_id: int, student_score: float) -> int:
        """計算學生在班級中的排名"""
        
        all_scores = GradeAnalysisService._calculate_final_grades()
        scores = sorted(
            [s[1] for s in all_scores if s[1] is not None],
            reverse=True
        )
        
        if student_score in scores:
            return scores.index(student_score) + 1
        return len(scores)
    
    @staticmethod
    def _get_class_average() -> float:
        """獲取班級平均分"""
        
        all_scores = GradeAnalysisService._calculate_final_grades()
        scores = [s[1] for s in all_scores if s[1] is not None]
        
        return statistics.mean(scores) if scores else 0
