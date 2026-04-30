"""
導出服務 - 處理 US-005
支持 PDF、Excel、CSV 格式導出
"""

import io
import csv
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from gradeinsight.models import Student, Grade, GradeComponent


class ExportService:
    """導出服務"""
    
    @staticmethod
    def export_class_report_excel(output_path: str) -> str:
        """
        導出班級成績表 - Excel 格式
        
        Returns: 文件路徑
        """
        
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = "班級成績表"
        
        # 設置標題
        title_cell = worksheet['A1']
        title_cell.value = "班級成績表"
        title_cell.font = Font(size=16, bold=True)
        worksheet.merge_cells('A1:G1')
        
        worksheet['A2'] = f"生成日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # 表頭
        headers = ['學號', '姓名', '班級']
        components = GradeComponent.query.all()
        for comp in components:
            headers.append(comp.name)
        headers.append('最終分數')
        
        worksheet.append(headers)
        
        # 設置表頭樣式
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)
        
        for cell in worksheet[4]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")
        
        # 數據行
        students = Student.query.all()
        for student in students:
            row = [student.student_id, student.name, student.class_name or '']
            
            total_weighted = 0
            total_weight = 0
            
            for component in components:
                grade = Grade.query.filter_by(
                    student_id=student.id,
                    component_id=component.id
                ).first()
                
                if grade:
                    row.append(grade.score)
                    total_weighted += grade.score * component.weight
                    total_weight += component.weight
                else:
                    row.append('-')
            
            final_score = total_weighted / total_weight if total_weight > 0 else 0
            row.append(round(final_score, 2))
            
            worksheet.append(row)
        
        # 調整列寬
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            worksheet.column_dimensions[column_letter].width = min(max_length + 2, 20)
        
        workbook.save(output_path)
        return output_path
    
    @staticmethod
    def export_individual_report_excel(student_id: int, output_path: str) -> str:
        """導出個人成績單 - Excel 格式"""
        
        student = Student.query.get(student_id)
        if not student:
            raise ValueError(f"學生 ID {student_id} 不存在")
        
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = "成績單"
        
        # 標題
        title = worksheet['A1']
        title.value = "個人成績單"
        title.font = Font(size=18, bold=True)
        worksheet.merge_cells('A1:C1')
        
        # 學生信息
        worksheet['A3'] = "學號:"
        worksheet['B3'] = student.student_id
        worksheet['A4'] = "姓名:"
        worksheet['B4'] = student.name
        worksheet['A5'] = "班級:"
        worksheet['B5'] = student.class_name or '-'
        worksheet['A6'] = "生成日期:"
        worksheet['B6'] = datetime.now().strftime('%Y-%m-%d')
        
        # 成績明細
        worksheet['A8'] = "成績明細"
        worksheet['A8'].font = Font(size=12, bold=True)
        
        headers = ['組件', '分數', '權重', '加權分']
        worksheet.append([])
        worksheet.append(headers)
        
        # 表頭樣式
        header_row = worksheet[10]
        for cell in header_row:
            cell.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
            cell.font = Font(bold=True)
        
        # 數據
        total_weighted = 0
        total_weight = 0
        row_num = 11
        
        components = GradeComponent.query.all()
        for component in components:
            grade = Grade.query.filter_by(
                student_id=student_id,
                component_id=component.id
            ).first()
            
            if grade:
                worksheet[f'A{row_num}'] = component.name
                worksheet[f'B{row_num}'] = grade.score
                worksheet[f'C{row_num}'] = component.weight
                worksheet[f'D{row_num}'] = round(grade.score * component.weight, 2)
                
                total_weighted += grade.score * component.weight
                total_weight += component.weight
                row_num += 1
        
        # 最終分數
        final_score = total_weighted / total_weight if total_weight > 0 else 0
        worksheet[f'A{row_num+1}'] = "最終分數:"
        worksheet[f'A{row_num+1}'].font = Font(bold=True)
        worksheet[f'B{row_num+1}'] = round(final_score, 2)
        worksheet[f'B{row_num+1}'].font = Font(bold=True)
        
        # 調整列寬
        worksheet.column_dimensions['A'].width = 15
        worksheet.column_dimensions['B'].width = 12
        worksheet.column_dimensions['C'].width = 12
        worksheet.column_dimensions['D'].width = 15
        
        workbook.save(output_path)
        return output_path
    
    @staticmethod
    def export_class_report_csv(output_path: str) -> str:
        """導出班級成績表 - CSV 格式"""
        
        with open(output_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            
            # 表頭
            headers = ['學號', '姓名', '班級']
            components = GradeComponent.query.all()
            for comp in components:
                headers.append(comp.name)
            headers.append('最終分數')
            
            writer.writerow(headers)
            
            # 數據
            students = Student.query.all()
            for student in students:
                row = [student.student_id, student.name, student.class_name or '']
                
                total_weighted = 0
                total_weight = 0
                
                for component in components:
                    grade = Grade.query.filter_by(
                        student_id=student.id,
                        component_id=component.id
                    ).first()
                    
                    if grade:
                        row.append(grade.score)
                        total_weighted += grade.score * component.weight
                        total_weight += component.weight
                    else:
                        row.append('-')
                
                final_score = total_weighted / total_weight if total_weight > 0 else 0
                row.append(round(final_score, 2))
                
                writer.writerow(row)
        
        return output_path
    
    @staticmethod
    def export_statistics_summary(output_path: str) -> str:
        """導出統計摘要 - Excel 格式"""
        
        from gradeinsight.services.analysis import GradeAnalysisService
        
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = "統計分析"
        
        # 標題
        title = worksheet['A1']
        title.value = "成績統計分析報告"
        title.font = Font(size=16, bold=True)
        worksheet.merge_cells('A1:C1')
        
        worksheet['A2'] = f"生成日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # 基本統計
        worksheet['A4'] = "基本統計指標"
        worksheet['A4'].font = Font(size=12, bold=True)
        
        summary = GradeAnalysisService.get_statistics_summary()
        
        row_num = 5
        metrics = [
            ('總學生數', summary['total_students']),
            ('平均分', summary['statistics'].get('mean', 0)),
            ('中位數', summary['statistics'].get('median', 0)),
            ('標準差', summary['statistics'].get('std_dev', 0)),
            ('最高分', summary['statistics'].get('max', 0)),
            ('最低分', summary['statistics'].get('min', 0)),
            ('及格率 (%)', summary['pass_rate']),
            ('優秀率 (%)', summary['excellent_rate']),
        ]
        
        for metric, value in metrics:
            worksheet[f'A{row_num}'] = metric
            worksheet[f'B{row_num}'] = value
            row_num += 1
        
        # 成績分級
        worksheet[f'A{row_num+1}'] = "成績分級分布"
        worksheet[f'A{row_num+1}'].font = Font(size=12, bold=True)
        
        row_num += 2
        worksheet[f'A{row_num}'] = "等級"
        worksheet[f'B{row_num}'] = "人數"
        row_num += 1
        
        for level, count in summary['grade_levels'].items():
            worksheet[f'A{row_num}'] = level
            worksheet[f'B{row_num}'] = count
            row_num += 1
        
        # 調整列寬
        worksheet.column_dimensions['A'].width = 20
        worksheet.column_dimensions['B'].width = 15
        
        workbook.save(output_path)
        return output_path
