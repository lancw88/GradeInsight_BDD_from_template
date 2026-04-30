#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GradeInsight CLI - 命令行界面
一個功能完整的教師成績管理系統
"""

import click
import os
import sys
from pathlib import Path
from tabulate import tabulate
from datetime import datetime

# 添加項目根目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from gradeinsight.app import create_app
from gradeinsight.models import db, Student, Grade, GradeComponent, ScoringScheme
from gradeinsight.services import GradeImportService
from gradeinsight.services.analysis import GradeAnalysisService
from gradeinsight.services.scoring import ScoringSchemeService, GradeEditService, AdjustmentRuleService
from gradeinsight.export import ExportService
from gradeinsight.backup import BackupService


# 創建應用上下文
app = create_app()


@click.group()
def cli():
    """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║              🎓 GradeInsight - 教師成績管理系統 🎓              ║
    ║                                                              ║
    ║  版本: 1.0.0  |  Python 應用程序                              ║
    ║  支持成績匯入、分析、導出、自動備份等完整功能                     ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    pass


# ==================== US-001: 匯入成績 ====================

@cli.group()
def import_grades():
    """匯入學生成績"""
    pass


@import_grades.command()
@click.argument('file_path')
def from_csv(file_path):
    """從 CSV 文件匯入成績"""
    
    with app.app_context():
        try:
            click.echo(f"📥 正在讀取文件: {file_path}")
            
            GradeImportService.validate_file(file_path)
            df = GradeImportService.read_file(file_path)
            
            click.echo(f"✓ 文件讀取成功，共 {len(df)} 行")
            click.echo("\n📋 數據預覽:")
            click.echo(GradeImportService.generate_preview(df))
            
            # 驗證數據
            click.echo("\n🔍 正在驗證數據...")
            is_valid, errors = GradeImportService.validate_data(df)
            
            if not is_valid:
                click.secho("❌ 數據驗證失敗:", fg='red')
                for error in errors[:10]:
                    click.echo(f"  - {error}")
                if len(errors) > 10:
                    click.echo(f"  ... 還有 {len(errors) - 10} 個錯誤")
                sys.exit(1)
            
            click.secho("✓ 數據驗證通過", fg='green')
            
            # 確認導入
            if click.confirm("\n確認要匯入這些數據嗎？", default=True):
                click.echo("\n⏳ 正在匯入數據...")
                result = GradeImportService.import_grades(df)
                
                if result['success']:
                    click.secho("✅ 匯入成功！", fg='green')
                    click.echo(f"\n📊 匯入摘要:")
                    click.echo(result['summary'])
                else:
                    click.secho("❌ 匯入失敗", fg='red')
                    for error in result['errors']:
                        click.echo(f"  - {error}")
            else:
                click.echo("⏭️  已取消匯入")
                
        except Exception as e:
            click.secho(f"❌ 错误: {str(e)}", fg='red')
            sys.exit(1)


@import_grades.command()
@click.argument('file_path')
def from_excel(file_path):
    """從 Excel 文件匯入成績"""
    
    with app.app_context():
        try:
            click.echo(f"📥 正在讀取文件: {file_path}")
            
            GradeImportService.validate_file(file_path)
            df = GradeImportService.read_file(file_path)
            
            click.echo(f"✓ 文件讀取成功，共 {len(df)} 行")
            
            # 驗證和導入（同上）
            is_valid, errors = GradeImportService.validate_data(df)
            
            if not is_valid:
                click.secho("❌ 數據驗證失敗", fg='red')
                sys.exit(1)
            
            if click.confirm("確認要匯入這些數據嗎？", default=True):
                result = GradeImportService.import_grades(df)
                if result['success']:
                    click.secho("✅ 匯入成功！", fg='green')
                    click.echo(result['summary'])
                    
        except Exception as e:
            click.secho(f"❌ 错误: {str(e)}", fg='red')


# ==================== US-002: 成績分布 ====================

@cli.group()
def analyze():
    """分析成績數據"""
    pass


@analyze.command()
@click.option('--width', default=10, help='成績段位寬度 (預設: 10)')
def distribution(width):
    """顯示成績分布"""
    
    with app.app_context():
        dist = GradeAnalysisService.get_grade_distribution(bin_width=width)
        
        click.echo("\n📊 成績分布直方圖:")
        click.echo("=" * 50)
        
        if dist['bins']:
            for bin_label, count in zip(dist['bins'], dist['counts']):
                bar = "█" * count
                click.echo(f"{bin_label:>5}: {bar} ({count})")
        else:
            click.echo("（暫無數據）")
        
        click.echo("\n📈 統計指標:")
        click.echo("=" * 50)
        stats = dist['statistics']
        stats_data = [
            ['平均分', f"{stats['mean']:.2f}"],
            ['中位數', f"{stats['median']:.2f}"],
            ['標準差', f"{stats['std_dev']:.2f}"],
            ['最高分', f"{stats['max']:.0f}"],
            ['最低分', f"{stats['min']:.0f}"],
            ['總人數', stats['total_count']],
        ]
        click.echo(tabulate(stats_data, headers=['指標', '數值']))


@analyze.command()
def summary():
    """顯示統計分析摘要"""
    
    with app.app_context():
        summary_data = GradeAnalysisService.get_statistics_summary()
        
        click.echo("\n📋 成績統計分析摘要")
        click.echo("=" * 60)
        
        basic_stats = [
            ['總學生數', summary_data['total_students']],
            ['平均分', f"{summary_data['statistics']['mean']:.2f}"],
            ['中位數', f"{summary_data['statistics']['median']:.2f}"],
            ['標準差', f"{summary_data['statistics']['std_dev']:.2f}"],
            ['最高分', f"{summary_data['statistics']['max']:.0f}"],
            ['最低分', f"{summary_data['statistics']['min']:.0f}"],
        ]
        click.echo(tabulate(basic_stats, headers=['指標', '數值']))
        
        click.echo("\n📊 成績分布 (A/B/C/D/F):")
        levels = summary_data['grade_levels']
        level_data = [
            ['A (90+)', levels['A']],
            ['B (80-89)', levels['B']],
            ['C (70-79)', levels['C']],
            ['D (60-69)', levels['D']],
            ['F (<60)', levels['F']],
        ]
        click.echo(tabulate(level_data, headers=['等級', '人數']))
        
        click.echo(f"\n及格率: {summary_data['pass_rate']:.2f}%")
        click.echo(f"優秀率: {summary_data['excellent_rate']:.2f}%")


# ==================== US-003: 識別風險學生 ====================

@cli.group()
def students():
    """學生管理命令"""
    pass


@students.command()
@click.option('--pass-line', default=60, help='及格線 (預設: 60)')
@click.option('--risk-range', default=10, help='風險範圍 (預設: ±10)')
def at_risk(pass_line, risk_range):
    """識別需要幫助的學生"""
    
    with app.app_context():
        at_risk_students = GradeAnalysisService.identify_at_risk_students(
            pass_line=pass_line,
            risk_range=risk_range
        )
        
        if at_risk_students:
            click.echo(f"\n⚠️  識別到 {len(at_risk_students)} 位需要幫助的學生")
            click.echo("=" * 70)
            
            table_data = []
            for student in at_risk_students:
                risk_emoji = "🔴" if student['risk_level'] == 'high' else "🟡"
                table_data.append([
                    student['student_id'],
                    student['name'],
                    f"{student['final_score']:.1f}",
                    f"{student['gap_to_pass']:.1f}",
                    risk_emoji
                ])
            
            click.echo(tabulate(
                table_data,
                headers=['學號', '姓名', '分數', '距及格', '風險'],
                tablefmt='grid'
            ))
        else:
            click.secho("✅ 沒有風險學生", fg='green')


@students.command()
@click.argument('student_id')
def details(student_id):
    """查看學生詳細信息"""
    
    with app.app_context():
        try:
            student = Student.query.filter_by(student_id=student_id).first()
            if not student:
                click.secho(f"❌ 學生不存在: {student_id}", fg='red')
                return
            
            details = GradeAnalysisService.get_student_details(student.id)
            
            click.echo(f"\n👤 {student.name} ({student.student_id})")
            click.echo("=" * 60)
            
            click.echo(f"班級: {student.class_name or '未設置'}")
            click.echo(f"郵箱: {student.email or '未設置'}")
            
            click.echo("\n📊 各科成績:")
            grade_data = [[
                g['component'],
                f"{g['score']:.1f}",
                f"{g['weight']}",
                f"{g['weighted_score']:.1f}"
            ] for g in details['grades_by_component']]
            click.echo(tabulate(
                grade_data,
                headers=['組件', '分數', '權重', '加權分'],
                tablefmt='grid'
            ))
            
            click.echo(f"\n📈 最終分數: {details['final_score']:.2f}")
            click.echo(f"班級排名: 第 {details['class_rank']} 名")
            click.echo(f"班級平均分: {details['comparison_to_average']['average_score']:.2f}")
            click.echo(f"與平均分差: {details['comparison_to_average']['difference']:+.2f}")
            
        except Exception as e:
            click.secho(f"❌ 错误: {str(e)}", fg='red')


# ==================== US-005: 導出報告 ====================

@cli.group()
def export():
    """導出成績報告"""
    pass


@export.command()
@click.option('--format', type=click.Choice(['xlsx', 'csv']), default='xlsx', help='導出格式')
def class_report(format):
    """導出班級成績表"""
    
    with app.app_context():
        try:
            export_dir = app.config['EXPORT_FOLDER']
            Path(export_dir).mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if format == 'xlsx':
                filename = f"class_report_{timestamp}.xlsx"
                filepath = os.path.join(export_dir, filename)
                ExportService.export_class_report_excel(filepath)
            else:
                filename = f"class_report_{timestamp}.csv"
                filepath = os.path.join(export_dir, filename)
                ExportService.export_class_report_csv(filepath)
            
            click.secho(f"✅ 導出成功: {filepath}", fg='green')
            
        except Exception as e:
            click.secho(f"❌ 导出失败: {str(e)}", fg='red')


@export.command()
@click.argument('student_id')
def individual(student_id):
    """導出個人成績單"""
    
    with app.app_context():
        try:
            student = Student.query.filter_by(student_id=student_id).first()
            if not student:
                click.secho(f"❌ 學生不存在: {student_id}", fg='red')
                return
            
            export_dir = app.config['EXPORT_FOLDER']
            Path(export_dir).mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{student_id}_report_{timestamp}.xlsx"
            filepath = os.path.join(export_dir, filename)
            
            ExportService.export_individual_report_excel(student.id, filepath)
            click.secho(f"✅ 導出成功: {filepath}", fg='green')
            
        except Exception as e:
            click.secho(f"❌ 导出失败: {str(e)}", fg='red')


@export.command()
def statistics():
    """導出統計分析報告"""
    
    with app.app_context():
        try:
            export_dir = app.config['EXPORT_FOLDER']
            Path(export_dir).mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"statistics_{timestamp}.xlsx"
            filepath = os.path.join(export_dir, filename)
            
            ExportService.export_statistics_summary(filepath)
            click.secho(f"✅ 導出成功: {filepath}", fg='green')
            
        except Exception as e:
            click.secho(f"❌ 导出失败: {str(e)}", fg='red')


# ==================== US-010: 備份管理 ====================

@cli.group()
def backup():
    """備份和恢復"""
    pass


@backup.command()
def create():
    """創建備份"""
    
    with app.app_context():
        click.echo("⏳ 正在創建備份...")
        try:
            backup_log = BackupService.create_backup()
            if backup_log.status == 'success':
                click.secho(f"✅ 備份成功!", fg='green')
                click.echo(f"文件: {backup_log.backup_file}")
                click.echo(f"大小: {backup_log.file_size / 1024:.2f} KB")
            else:
                click.secho(f"❌ 備份失敗: {backup_log.error_message}", fg='red')
        except Exception as e:
            click.secho(f"❌ 错误: {str(e)}", fg='red')


@backup.command()
def list():
    """列出所有備份"""
    
    with app.app_context():
        backups = BackupService.list_backups()
        
        if backups:
            click.echo("\n📦 可用的備份:")
            click.echo("=" * 70)
            
            table_data = []
            for i, backup in enumerate(backups, 1):
                table_data.append([
                    i,
                    backup['filename'],
                    f"{backup['size'] / 1024:.2f} KB",
                    backup['created_at']
                ])
            
            click.echo(tabulate(
                table_data,
                headers=['#', '文件名', '大小', '創建時間'],
                tablefmt='grid'
            ))
        else:
            click.echo("暫無備份")


@backup.command()
def cleanup():
    """清理過期備份 (>30天)"""
    
    with app.app_context():
        click.echo("⏳ 正在清理過期備份...")
        deleted = BackupService.cleanup_old_backups()
        click.secho(f"✅ 已刪除 {deleted} 個過期備份", fg='green')


# ==================== 數據庫管理 ====================

@cli.group()
def database():
    """數據庫管理"""
    pass


@database.command()
def init():
    """初始化數據庫"""
    
    with app.app_context():
        click.echo("⏳ 正在初始化數據庫...")
        try:
            db.create_all()
            click.secho("✅ 數據庫初始化成功", fg='green')
        except Exception as e:
            click.secho(f"❌ 错误: {str(e)}", fg='red')


@database.command()
def reset():
    """重置數據庫 (警告: 會刪除所有數據)"""
    
    if click.confirm("⚠️  確定要重置數據庫嗎? (將刪除所有數據)", default=False):
        with app.app_context():
            click.echo("⏳ 正在重置數據庫...")
            try:
                db.drop_all()
                db.create_all()
                click.secho("✅ 數據庫已重置", fg='green')
            except Exception as e:
                click.secho(f"❌ 错误: {str(e)}", fg='red')
    else:
        click.echo("⏭️  已取消重置")


@database.command()
def status():
    """查看數據庫狀態"""
    
    with app.app_context():
        try:
            student_count = Student.query.count()
            component_count = GradeComponent.query.count()
            grade_count = Grade.query.count()
            
            click.echo("\n📊 數據庫狀態:")
            click.echo("=" * 40)
            
            status_data = [
                ['學生數', student_count],
                ['成績組件數', component_count],
                ['成績記錄數', grade_count],
            ]
            click.echo(tabulate(status_data, headers=['項目', '數量']))
            
        except Exception as e:
            click.secho(f"❌ 错误: {str(e)}", fg='red')


# ==================== 主函數 ====================

if __name__ == '__main__':
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n⏸️  程序已中斷")
        sys.exit(0)
    except Exception as e:
        click.secho(f"\n❌ 發生錯誤: {str(e)}", fg='red')
        sys.exit(1)
