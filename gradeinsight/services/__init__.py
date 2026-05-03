"""
成績匯入服務 - 處理 US-001
"""

import os
import pandas as pd
import io
from datetime import datetime
from typing import Tuple, List, Dict
from gradeinsight.models import db, Student, Grade, GradeComponent, AuditLog


class ImportError(Exception):
    """匯入錯誤"""
    pass


class GradeImportService:
    """成績匯入服務"""
    
    # 支持的文件格式
    SUPPORTED_FORMATS = ['.csv', '.xlsx', '.xls']
    
    # 必需的列名
    REQUIRED_COLUMNS = ['student_id', 'name']
    
    @staticmethod
    def validate_file(filename: str) -> bool:
        """驗證文件格式"""
        if not any(filename.lower().endswith(fmt) for fmt in GradeImportService.SUPPORTED_FORMATS):
            raise ImportError(f"不支持的文件格式: {filename}。支持的格式: {', '.join(GradeImportService.SUPPORTED_FORMATS)}")
        return True

    @staticmethod
    def validate_file_size(file_path: str, max_size_mb: int = 500) -> Tuple[bool, str]:
        """驗證檔案大小"""
        if not os.path.exists(file_path):
            return False, '檔案不存在'
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if size_mb > max_size_mb:
            return False, f'檔案過大，最大限制為 {max_size_mb} MB'
        return True, ''

    @staticmethod
    def read_file(file_path: str) -> pd.DataFrame:
        """讀取文件"""
        try:
            if file_path.lower().endswith('.csv'):
                return pd.read_csv(file_path, dtype={'student_id': str})
            elif file_path.lower().endswith('.xlsx'):
                return pd.read_excel(file_path, dtype={'student_id': str})
            elif file_path.lower().endswith('.xls'):
                return pd.read_excel(file_path, dtype={'student_id': str})
        except Exception as e:
            raise ImportError(f"讀取文件失敗: {str(e)}")
    
    @staticmethod
    def validate_data(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """驗證數據"""
        errors = []
        
        # 檢查必需列
        for col in GradeImportService.REQUIRED_COLUMNS:
            if col not in df.columns:
                errors.append(f"缺少必需列: {col}")
        
        # 檢查行數
        if len(df) > 500:
            errors.append(f"數據行數超過限制 (最多500名學生)，當前: {len(df)}")
        
        # 數據驗證
        for idx, row in df.iterrows():
            row_errors = []
            
            # 驗證學號不為空
            if pd.isna(row.get('student_id')) or str(row.get('student_id')).strip() == '':
                row_errors.append("學號不能為空")
            
            # 驗證姓名不為空
            if pd.isna(row.get('name')) or str(row.get('name')).strip() == '':
                row_errors.append("姓名不能為空")
            
            # 驗證成績列（除了 student_id 和 name）
            for col in df.columns:
                if col not in ['student_id', 'name', 'class_name', 'email']:
                    try:
                        value = row.get(col)
                        if pd.notna(value) and str(value).strip() != '':
                            score = float(value)
                            if not (0 <= score <= 100):
                                row_errors.append(f"列 '{col}' 的成績必須在 0-100 之間")
                    except ValueError:
                        row_errors.append(f"列 '{col}' 的成績格式無效: {value}")
            
            if row_errors:
                errors.append(f"第 {idx + 2} 行: {'; '.join(row_errors)}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def generate_preview(df: pd.DataFrame, max_rows: int = 5) -> str:
        """生成預覽"""
        preview = df.head(max_rows).to_string()
        summary = f"\n\n匯入摘要:\n- 總行數: {len(df)}\n- 列數: {len(df.columns)}"
        return preview + summary
    
    @staticmethod
    def import_grades(df: pd.DataFrame, operator: str = 'system') -> Dict:
        """
        匯入成績數據
        
        Args:
            df: 包含成績的 DataFrame
            operator: 操作人
            
        Returns:
            {
                'success': bool,
                'imported_count': int,
                'skipped_count': int,
                'errors': List[str],
                'summary': str
            }
        """
        
        results = {
            'success': True,
            'imported_count': 0,
            'skipped_count': 0,
            'errors': [],
            'summary': ''
        }
        
        try:
            # 確保所有成績組件已創建
            grade_components = {}
            for col in df.columns:
                if col not in ['student_id', 'name', 'class_name', 'email']:
                    component = GradeComponent.query.filter_by(name=col).first()
                    if not component:
                        component = GradeComponent(
                            name=col,
                            description=f"自動導入的組件: {col}",
                            component_type='exam'
                        )
                        db.session.add(component)
                    grade_components[col] = component
            
            db.session.commit()
            
            # 匯入學生和成績
            duplicate_students = set()
            imported_coordinates = set()  # 用於檢測重複成績
            
            for idx, row in df.iterrows():
                student_id = str(row.get('student_id', '')).strip()
                name = str(row.get('name', '')).strip()
                
                # 跳過無效行
                if not student_id or not name:
                    results['skipped_count'] += 1
                    continue
                
                # 檢查重複
                existing_student = Student.query.filter_by(student_id=student_id).first()
                if existing_student:
                    duplicate_students.add(student_id)
                    # 繼續匯入該學生的新成績
                    student = existing_student
                else:
                    student = Student(
                        student_id=student_id,
                        name=name,
                        class_name=row.get('class_name', ''),
                        email=row.get('email', ''),
                    )
                    db.session.add(student)
                    db.session.flush()  # 獲取自動分配的 ID
                
                # 匯入成績
                grades_imported = False
                for col, component in grade_components.items():
                    value = row.get(col)
                    if pd.notna(value) and str(value).strip() != '':
                        try:
                            score = float(value)
                            
                            # 檢查是否已存在此成績記錄
                            coordinate = (student.id if hasattr(student, 'id') else None, component.id)
                            if coordinate in imported_coordinates:
                                results['skipped_count'] += 1
                                continue
                            
                            # 查找現有記錄
                            grade = Grade.query.filter_by(
                                student_id=student.id if hasattr(student, 'id') else None,
                                component_id=component.id
                            ).first()
                            
                            if grade:
                                grade.score = score
                                grade.updated_at = datetime.utcnow()
                            else:
                                grade = Grade(
                                    student_id=student.id if hasattr(student, 'id') else None,
                                    component_id=component.id,
                                    score=score
                                )
                                db.session.add(grade)
                            
                            # 記錄審計日誌
                            audit_log = AuditLog(
                                operation_type='import',
                                student_id=student.id,
                                component_id=component.id,
                                new_value=score,
                                reason='自動匯入',
                                operator=operator
                            )
                            db.session.add(audit_log)
                            
                            imported_coordinates.add(coordinate)
                            grades_imported = True
                        except ValueError:
                            pass
                
                if grades_imported:
                    results['imported_count'] += 1
            
            db.session.commit()
            
            # 生成摘要
            summary_lines = [
                f"成功匯入: {results['imported_count']} 條記錄",
                f"跳過: {results['skipped_count']} 條記錄",
            ]
            
            if duplicate_students:
                summary_lines.append(f"更新了現有學生: {len(duplicate_students)} 名")
            
            results['summary'] = '\n'.join(summary_lines)
            
            return results
            
        except Exception as e:
            db.session.rollback()
            results['success'] = False
            results['errors'].append(str(e))
            return results
