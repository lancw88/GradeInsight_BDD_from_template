"""
應用程序配置模塊
"""

import os
from datetime import timedelta

class Config:
    """基礎配置"""
    
    # 數據庫配置
    SQLALCHEMY_DATABASE_URI = 'sqlite:////workspaces/GradeInsight_BDD_from_template/data/gradeinsight.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 應用配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    JSON_SORT_KEYS = False
    
    # 文件上傳配置
    UPLOAD_FOLDER = '/workspaces/GradeInsight_BDD_from_template/data/uploads'
    EXPORT_FOLDER = '/workspaces/GradeInsight_BDD_from_template/data/exports'
    BACKUP_FOLDER = '/workspaces/GradeInsight_BDD_from_template/data/backups'
    
    # 備份配置
    BACKUP_RETENTION_DAYS = 30
    BACKUP_SCHEDULE_HOUR = 0  # 午夜備份
    BACKUP_SCHEDULE_MINUTE = 0
    
    # 分頁配置
    ITEMS_PER_PAGE = 50
    
    # 日誌配置
    LOG_LEVEL = 'INFO'
    LOG_FILE = '/workspaces/GradeInsight_BDD_from_template/data/logs/gradeinsight.log'


class DevelopmentConfig(Config):
    """開發環境配置"""
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """測試環境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


class ProductionConfig(Config):
    """生產環境配置"""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///gradeinsight.db')


def get_config():
    """獲取配置對象"""
    env = os.getenv('FLASK_ENV', 'development')
    configs = {
        'development': DevelopmentConfig,
        'testing': TestingConfig,
        'production': ProductionConfig,
    }
    return configs.get(env, DevelopmentConfig)
