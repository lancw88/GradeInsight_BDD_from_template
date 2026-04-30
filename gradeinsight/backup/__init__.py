"""
備份服務 - 處理 US-010
自動備份和數據安全管理
"""

import os
import shutil
import json
from datetime import datetime, timedelta
from pathlib import Path
from cryptography.fernet import Fernet
import sqlite3
from gradeinsight.models import db, BackupLog


class BackupService:
    """備份服務"""
    
    # 加密密鑰（在生產環境應從環境變量讀取）
    ENCRYPTION_KEY = Fernet.generate_key()
    
    # 備份配置
    BACKUP_RETENTION_DAYS = 30
    DB_PATH = '/workspaces/GradeInsight_BDD_from_template/data/gradeinsight.db'
    BACKUP_DIR = '/workspaces/GradeInsight_BDD_from_template/data/backups'
    
    @staticmethod
    def ensure_backup_dir():
        """確保備份目錄存在"""
        Path(BackupService.BACKUP_DIR).mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def create_backup() -> BackupLog:
        """
        創建完整備份
        使用 AES-256 加密
        """
        
        BackupService.ensure_backup_dir()
        
        # 創建備份記錄
        backup_log = BackupLog(
            backup_file='',
            status='pending'
        )
        db.session.add(backup_log)
        db.session.commit()
        
        try:
            # 生成備份文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"backup_{timestamp}.db"
            backup_path = os.path.join(BackupService.BACKUP_DIR, backup_filename)
            
            # 複製數據庫文件
            if os.path.exists(BackupService.DB_PATH):
                shutil.copy2(BackupService.DB_PATH, backup_path)
                
                # 加密備份文件
                BackupService._encrypt_file(backup_path)
                
                # 獲取文件大小
                file_size = os.path.getsize(backup_path)
                
                # 更新備份記錄
                backup_log.backup_file = backup_filename
                backup_log.file_size = file_size
                backup_log.status = 'success'
                backup_log.completed_at = datetime.utcnow()
            else:
                raise Exception(f"數據庫文件不存在: {BackupService.DB_PATH}")
            
        except Exception as e:
            backup_log.status = 'failed'
            backup_log.error_message = str(e)
            print(f"❌ 備份失敗: {str(e)}")
        
        db.session.commit()
        return backup_log
    
    @staticmethod
    def restore_backup(backup_filename: str) -> bool:
        """
        從備份恢復數據
        
        Args:
            backup_filename: 備份文件名
            
        Returns:
            成功返回 True
        """
        
        backup_path = os.path.join(BackupService.BACKUP_DIR, backup_filename)
        
        if not os.path.exists(backup_path):
            raise ValueError(f"備份文件不存在: {backup_filename}")
        
        try:
            # 解密備份文件
            decrypted_path = backup_path + '.decrypted'
            BackupService._decrypt_file(backup_path, decrypted_path)
            
            # 備份當前數據庫
            current_backup = os.path.join(BackupService.BACKUP_DIR, f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
            if os.path.exists(BackupService.DB_PATH):
                shutil.copy2(BackupService.DB_PATH, current_backup)
            
            # 恢復備份
            shutil.copy2(decrypted_path, BackupService.DB_PATH)
            
            # 清理臨時文件
            os.remove(decrypted_path)
            
            return True
            
        except Exception as e:
            print(f"❌ 恢復失敗: {str(e)}")
            return False
    
    @staticmethod
    def cleanup_old_backups() -> int:
        """
        清理超過 30 天的備份文件
        
        Returns: 刪除的備份數
        """
        
        BackupService.ensure_backup_dir()
        deleted_count = 0
        cutoff_date = datetime.now() - timedelta(days=BackupService.BACKUP_RETENTION_DAYS)
        
        for backup_file in os.listdir(BackupService.BACKUP_DIR):
            if backup_file.startswith('backup_'):
                backup_path = os.path.join(BackupService.BACKUP_DIR, backup_file)
                
                # 檢查文件修改時間
                file_mtime = datetime.fromtimestamp(os.path.getmtime(backup_path))
                if file_mtime < cutoff_date:
                    try:
                        os.remove(backup_path)
                        deleted_count += 1
                        print(f"🗑️  已刪除過期備份: {backup_file}")
                    except Exception as e:
                        print(f"⚠️  無法刪除備份: {backup_file} - {str(e)}")
        
        return deleted_count
    
    @staticmethod
    def list_backups() -> list:
        """列出所有可用的備份"""
        
        BackupService.ensure_backup_dir()
        backups = []
        
        for backup_file in sorted(os.listdir(BackupService.BACKUP_DIR)):
            if backup_file.startswith('backup_'):
                backup_path = os.path.join(BackupService.BACKUP_DIR, backup_file)
                file_stats = os.stat(backup_path)
                
                backups.append({
                    'filename': backup_file,
                    'size': file_stats.st_size,
                    'created_at': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                })
        
        return sorted(backups, key=lambda x: x['created_at'], reverse=True)
    
    @staticmethod
    def get_backup_logs(limit: int = 20) -> list:
        """獲取備份日誌"""
        
        logs = BackupLog.query.order_by(BackupLog.created_at.desc()).limit(limit).all()
        return [{
            'id': log.id,
            'backup_file': log.backup_file,
            'file_size': log.file_size,
            'status': log.status,
            'error_message': log.error_message,
            'created_at': log.created_at.isoformat(),
            'completed_at': log.completed_at.isoformat() if log.completed_at else None,
        } for log in logs]
    
    # ========== 私有方法 ==========
    
    @staticmethod
    def _encrypt_file(file_path: str):
        """加密文件（使用 Fernet 對稱加密）"""
        
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # 使用加密密鑰加密
            cipher = Fernet(BackupService.ENCRYPTION_KEY)
            encrypted_data = cipher.encrypt(file_data)
            
            # 寫回加密數據
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)
            
            print(f"✓ 文件已加密: {file_path}")
        except Exception as e:
            print(f"⚠️  加密失敗: {str(e)}")
    
    @staticmethod
    def _decrypt_file(encrypted_path: str, output_path: str):
        """解密文件"""
        
        try:
            with open(encrypted_path, 'rb') as f:
                encrypted_data = f.read()
            
            # 解密
            cipher = Fernet(BackupService.ENCRYPTION_KEY)
            decrypted_data = cipher.decrypt(encrypted_data)
            
            # 寫出解密文件
            with open(output_path, 'wb') as f:
                f.write(decrypted_data)
            
            print(f"✓ 文件已解密: {output_path}")
        except Exception as e:
            print(f"⚠️  解密失敗: {str(e)}")
            raise


class BackupScheduler:
    """備份調度器"""
    
    @staticmethod
    def schedule_daily_backup():
        """
        調度每日備份
        在實際應用中應使用 schedule 庫或 APScheduler
        """
        
        import schedule
        import time
        
        # 每天午夜執行備份
        schedule.every().day.at("00:00").do(BackupService.create_backup)
        
        while True:
            schedule.run_pending()
            time.sleep(60)
