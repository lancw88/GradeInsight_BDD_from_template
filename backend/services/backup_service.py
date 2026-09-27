import logging
import json
import os
import secrets
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .storage import GradeStore

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc).astimezone()


class BackupService:
    def __init__(self, store: GradeStore, backup_dir: Path | None = None) -> None:
        self.store = store
        self.backup_dir = backup_dir or (store.database_path.parent / "backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.key = self._load_key()

    def _load_key(self) -> bytes:
        configured = os.getenv("GRADEINSIGHT_BACKUP_KEY")
        if configured:
            try:
                key = bytes.fromhex(configured)
            except ValueError as error:
                raise ValueError("GRADEINSIGHT_BACKUP_KEY 必須是 64 個十六進位字元") from error
            if len(key) != 32:
                raise ValueError("GRADEINSIGHT_BACKUP_KEY 必須代表 32 位元組 AES-256 金鑰")
            return key
        key_path = self.backup_dir / ".local-backup.key"
        if not key_path.exists():
            descriptor = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "wb") as key_file:
                key_file.write(secrets.token_bytes(32))
        return key_path.read_bytes()

    def create_backup(self) -> dict[str, Any]:
        timestamp = _now()
        filename = f"gradeinsight_{timestamp.strftime('%Y%m%d_%H%M%S')}.aes"
        target = self.backup_dir / filename
        try:
            with tempfile.TemporaryDirectory() as temporary_dir:
                snapshot_path = Path(temporary_dir) / "snapshot.sqlite3"
                with sqlite3.connect(self.store.database_path) as source, sqlite3.connect(snapshot_path) as snapshot:
                    source.backup(snapshot)
                nonce = secrets.token_bytes(12)
                encrypted = b"GI1" + nonce + AESGCM(self.key).encrypt(nonce, snapshot_path.read_bytes(), b"GradeInsight backup v1")
            target.write_bytes(encrypted)
            os.chmod(target, 0o600)
            self._prune(timestamp)
            result = {"filename": filename, "size_bytes": target.stat().st_size, "status": "success", "message": "備份已使用 AES-256-GCM 加密"}
            self.store.save_backup(filename, result["size_bytes"], result["status"], result["message"], timestamp.isoformat(timespec="seconds"))
            return result
        except Exception as error:
            logger.exception("GradeInsight backup failed")
            message = "備份失敗，系統管理員需檢查服務紀錄"
            self.store.save_backup(filename, 0, "failed", f"{message}：{error}", timestamp.isoformat(timespec="seconds"))
            self._notify_admin(f"{message}：{error}")
            raise RuntimeError(message) from error

    @staticmethod
    def _notify_admin(message: str) -> None:
        webhook_url = os.getenv("GRADEINSIGHT_ADMIN_WEBHOOK")
        if not webhook_url:
            logger.error("備份失敗通知：%s", message)
            return
        request = Request(
            webhook_url,
            data=json.dumps({"text": message}, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=5):
                logger.info("已傳送備份失敗通知至管理員 Webhook")
        except Exception:
            logger.exception("無法傳送備份失敗管理員通知")

    def _prune(self, now: datetime) -> None:
        files = sorted(self.backup_dir.glob("gradeinsight_*.aes"), key=lambda path: path.stat().st_mtime, reverse=True)
        cutoff = now - timedelta(days=30)
        for index, path in enumerate(files):
            modified = datetime.fromtimestamp(path.stat().st_mtime, tz=now.tzinfo)
            if index >= 30 or modified < cutoff:
                path.unlink(missing_ok=True)

    def history(self) -> list[dict[str, Any]]:
        return self.store.backup_history()