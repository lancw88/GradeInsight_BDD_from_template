"""
GradeInsight - 教師成績管理系統
一個功能完整的 Python 應用程序，支持成績匯入、分析、導出和自動化管理
"""

__version__ = "1.0.0"
__author__ = "Grade Insight Team"

from .app import create_app
from .models import db

__all__ = ['create_app', 'db']
