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
            
            if risk_min <= final_score <= risk_max:
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
        
        try:
            mode = statistics.mode(grades)
        except Exception:
            mode = 0

        return {
            'total_students': len(grades),
            'statistics': {
                'mean': round(mean, 2),
                'median': round(statistics.median(grades), 2),
                'mode': round(mode, 2) if isinstance(mode, (int, float)) else mode,
                'std_dev': round(std_dev, 2),
                'min': min(grades),
                'max': max(grades),
            },
            'grade_levels': grade_levels,
            'pass_rate': round((len(grades) - grade_levels['F']) / len(grades) * 100, 2),
            'excellent_rate': round(grade_levels['A'] / len(grades) * 100, 2),
            'outliers': sorted(outliers),
        }

    @staticmethod
    def get_statistics_by_dimension(dimension: str) -> Dict:
        """按維度 (如 component type) 統計成績"""
        if dimension == '按考試類型':
            components = GradeComponent.query.all()
            results = []
            for comp in components:
                grades = Grade.query.filter_by(component_id=comp.id).all()
                scores = [g.score for g in grades if g.score is not None]
                if not scores:
                    continue
                pass_rate = round(sum(1 for s in scores if s >= 60) / len(scores) * 100, 2)
                results.append({
                    'exam_type': comp.name,
                    'average': round(sum(scores) / len(scores), 2),
                    'pass_rate': pass_rate,
                })
            return {'dimension': dimension, 'items': results}
        return {'dimension': dimension, 'items': []}

    @staticmethod
    def compare_class_with_other(class_name: str, other_class_name: str) -> Dict:
        """比較兩個班級的統計指標"""
        def metrics_for_class(name):
            students = Student.query.filter_by(class_name=name).all()
            if not students:
                return None
            scores = []
            for student in students:
                final = GradeAnalysisService._calculate_final_score_for_student(student.id)
                if final is not None:
                    scores.append(final)
            if not scores:
                return None
            return {
                'class_name': name,
                'average': round(statistics.mean(scores), 2),
                'median': round(statistics.median(scores), 2),
                'pass_rate': round(sum(1 for s in scores if s >= 60) / len(scores) * 100, 2),
            }

        return {
            'current': metrics_for_class(class_name),
            'other': metrics_for_class(other_class_name),
        }

    @staticmethod
    def identify_outliers() -> Dict:
        """識別異常成績"""
        summary = GradeAnalysisService.get_statistics_summary()
        return {
            'high_outliers': [s for s in summary['outliers'] if s > summary['statistics']['mean']] if summary['statistics']['mean'] is not None else [],
            'low_outliers': [s for s in summary['outliers'] if s < summary['statistics']['mean']] if summary['statistics']['mean'] is not None else [],
        }

    @staticmethod
    def generate_analysis_conclusions() -> Dict:
        """產生分析結論與建議"""
        summary = GradeAnalysisService.get_statistics_summary()
        conclusions = []
        if summary['total_students'] == 0:
            conclusions.append('無可用成績數據進行分析。')
        else:
            if summary['grade_levels']['F'] > 0:
                conclusions.append('班上仍有不及格學生，需加強補救教學。')
            if summary['grade_levels']['A'] >= summary['grade_levels']['B']:
                conclusions.append('優良成績比例較高，教學成果良好。')
            if summary['statistics']['std_dev'] > 15:
                conclusions.append('成績離散度較大，建議檢視教學與評量一致性。')
            conclusions.append('建議針對低分學生提供個別輔導方案。')
            conclusions.append('建議檢討課程設計以提升整體學習成效。')
            conclusions.append('建議評估教學策略以提高弱勢學生的表現。')

        return {
            'conclusions': conclusions,
            'summary': summary,
        }

    @staticmethod
    def _calculate_final_score_for_student(student_id: int) -> float:
        grades = db.session.query(Grade.score, GradeComponent.weight).join(GradeComponent).filter(Grade.student_id == student_id).all()
        student = Student.query.get(student_id)
        if not grades:
            return student.rule_adjustment if student else 0
        total_weighted = sum(g[0] * g[1] for g in grades)
        total_weight = sum(g[1] for g in grades)
        result = total_weighted / total_weight if total_weight > 0 else 0
        return result + (student.rule_adjustment or 0)

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
                final_score += student.rule_adjustment or 0
            else:
                final_score = student.rule_adjustment or 0
            
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
