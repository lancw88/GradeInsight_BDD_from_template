"""
測試套件
"""

import unittest
import sys
from pathlib import Path

# 添加項目根目錄
sys.path.insert(0, str(Path(__file__).parent.parent))

from gradeinsight.app import create_app
from gradeinsight.config import TestingConfig
from gradeinsight.models import db, Student, GradeComponent, Grade


class GradeInsightTestCase(unittest.TestCase):
    """基礎測試用例"""
    
    def setUp(self):
        """設置測試環境"""
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
    
    def tearDown(self):
        """清理測試環境"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_student_creation(self):
        """測試學生創建"""
        with self.app.app_context():
            student = Student(
                student_id='S001',
                name='張三',
                class_name='一年級'
            )
            db.session.add(student)
            db.session.commit()
            
            fetched = Student.query.filter_by(student_id='S001').first()
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.name, '張三')
    
    def test_grade_component_creation(self):
        """測試成績組件創建"""
        with self.app.app_context():
            component = GradeComponent(
                name='期中考',
                weight=0.3,
                max_score=100
            )
            db.session.add(component)
            db.session.commit()
            
            fetched = GradeComponent.query.filter_by(name='期中考').first()
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.weight, 0.3)
    
    def test_grade_creation(self):
        """測試成績記錄創建"""
        with self.app.app_context():
            # 創建學生
            student = Student(student_id='S002', name='李四')
            db.session.add(student)
            db.session.flush()
            
            # 創建組件
            component = GradeComponent(name='期末考', weight=0.5)
            db.session.add(component)
            db.session.flush()
            
            # 創建成績
            grade = Grade(
                student_id=student.id,
                component_id=component.id,
                score=85.5
            )
            db.session.add(grade)
            db.session.commit()
            
            fetched = Grade.query.filter_by(student_id=student.id).first()
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.score, 85.5)


if __name__ == '__main__':
    unittest.main()
