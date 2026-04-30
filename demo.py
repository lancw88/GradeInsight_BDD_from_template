#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GradeInsight 快速演示腳本
展示系統的主要功能
"""

import sys
from pathlib import Path

# 添加項目根目錄
sys.path.insert(0, str(Path(__file__).parent))

from gradeinsight.app import create_app
from gradeinsight.models import db, Student, GradeComponent, Grade
from gradeinsight.services.analysis import GradeAnalysisService


def print_header(title):
    """打印標題"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def demo():
    """運行演示"""
    
    app = create_app()
    
    with app.app_context():
        print("\n")
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║                                                              ║")
        print("║              🎓 GradeInsight 系統演示 🎓                    ║")
        print("║                                                              ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        
        # 1. 查看數據庫狀態
        print_header("1️⃣ 數據庫狀態")
        
        student_count = Student.query.count()
        component_count = GradeComponent.query.count()
        grade_count = Grade.query.count()
        
        print(f"  👥 學生數量: {student_count}")
        print(f"  📚 成績組件: {component_count}")
        print(f"  📊 成績記錄: {grade_count}")
        
        if student_count == 0:
            print("\n  ⚠️  數據庫為空。請先運行:")
            print("     python gradeinsight/cli.py import-grades from-csv data/sample_grades.csv")
            return
        
        # 2. 顯示所有學生
        print_header("2️⃣ 所有學生列表")
        
        students = Student.query.all()
        print(f"  {'學號':<8} {'姓名':<12} {'班級':<15} {'郵箱':<25}")
        print("  " + "-" * 65)
        
        for student in students[:5]:
            email = student.email or "未設置"
            print(f"  {student.student_id:<8} {student.name:<12} {student.class_name or '未設置':<15} {email:<25}")
        
        if len(students) > 5:
            print(f"  ... 還有 {len(students) - 5} 名學生")
        
        # 3. 顯示成績組件
        print_header("3️⃣ 成績組件配置")
        
        components = GradeComponent.query.all()
        print(f"  {'組件名稱':<15} {'權重':<8} {'最高分':<10} {'類型':<15}")
        print("  " + "-" * 50)
        
        for component in components:
            print(f"  {component.name:<15} {component.weight:<8} {component.max_score:<10} {component.component_type:<15}")
        
        # 4. 顯示一個學生的詳細信息
        if students:
            print_header("4️⃣ 學生詳細信息示例")
            
            student = students[0]
            print(f"  學號: {student.student_id}")
            print(f"  姓名: {student.name}")
            print(f"  班級: {student.class_name or '未設置'}")
            print(f"\n  各科成績:")
            print(f"    {'組件':<15} {'分數':<8} {'權重':<8} {'加權分':<10}")
            print("    " + "-" * 45)
            
            total_weighted = 0
            total_weight = 0
            
            grades = Grade.query.filter_by(student_id=student.id).all()
            for grade in grades:
                component = grade.component
                weighted = grade.score * component.weight
                print(f"    {component.name:<15} {grade.score:<8.1f} {component.weight:<8} {weighted:<10.1f}")
                total_weighted += weighted
                total_weight += component.weight
            
            if total_weight > 0:
                final_score = total_weighted / total_weight
                print(f"\n  最終分數 (加權平均): {final_score:.2f}")
        
        # 5. 統計分析
        print_header("5️⃣ 統計分析")
        
        summary = GradeAnalysisService.get_statistics_summary()
        
        print(f"  總學生數: {summary['total_students']}")
        print(f"  平均分: {summary['statistics']['mean']:.2f}")
        print(f"  中位數: {summary['statistics']['median']:.2f}")
        print(f"  標準差: {summary['statistics']['std_dev']:.2f}")
        print(f"  最高分: {summary['statistics']['max']:.0f}")
        print(f"  最低分: {summary['statistics']['min']:.0f}")
        print(f"  及格率: {summary['pass_rate']:.2f}%")
        print(f"  優秀率: {summary['excellent_rate']:.2f}%")
        
        # 6. 使用提示
        print_header("🚀 接下來的操作")
        
        print("  可以使用以下命令進行更多操作:\n")
        
        commands = [
            ("查看成績分布", "python gradeinsight/cli.py analyze distribution"),
            ("識別風險學生", "python gradeinsight/cli.py students at-risk"),
            ("查看學生詳情", "python gradeinsight/cli.py students details S001"),
            ("導出班級報告", "python gradeinsight/cli.py export class-report --format xlsx"),
            ("導出個人成績單", "python gradeinsight/cli.py export individual S001"),
            ("創建備份", "python gradeinsight/cli.py backup create"),
            ("列出所有備份", "python gradeinsight/cli.py backup list"),
            ("查看幫助信息", "python gradeinsight/cli.py --help"),
        ]
        
        for idx, (desc, cmd) in enumerate(commands, 1):
            print(f"  {idx}. {desc}")
            print(f"     $ {cmd}\n")
        
        print("\n" + "=" * 70)
        print("  ✅ 演示完成！祝您使用愉快 🎉")
        print("=" * 70 + "\n")


if __name__ == '__main__':
    try:
        demo()
    except KeyboardInterrupt:
        print("\n⏸️  程序已中斷")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
