"""
Flask 應用程序工廠
"""

from flask import Flask
from gradeinsight.config import get_config
from gradeinsight.models import db
from pathlib import Path
import logging


def create_app(config=None):
    """
    應用程序工廠函數
    
    Args:
        config: 配置對象
        
    Returns:
        Flask 應用程序實例
    """
    
    app = Flask(__name__)
    
    # 載入配置
    if config is None:
        config = get_config()
    
    app.config.from_object(config)
    
    # 初始化數據庫
    db.init_app(app)
    
    # 創建必要的目錄
    for folder in [app.config['UPLOAD_FOLDER'], 
                   app.config['EXPORT_FOLDER'],
                   app.config['BACKUP_FOLDER']]:
        Path(folder).mkdir(parents=True, exist_ok=True)
    
    # 設置日誌
    _setup_logging(app)
    
    # 應用程序上下文
    with app.app_context():
        # 創建數據庫表
        db.create_all()
    
    return app


def _setup_logging(app):
    """設置應用程序日誌"""
    
    log_file = app.config.get('LOG_FILE')
    log_level = app.config.get('LOG_LEVEL', 'INFO')
    
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level))
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        app.logger.addHandler(file_handler)
    
    app.logger.setLevel(getattr(logging, log_level))
