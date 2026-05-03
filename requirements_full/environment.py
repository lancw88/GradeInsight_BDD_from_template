import os
import shutil
import tempfile
from pathlib import Path
from gradeinsight.app import create_app
from gradeinsight.config import TestingConfig
from gradeinsight.models import db


def before_scenario(context, scenario):
    context.app = create_app(TestingConfig)
    context.app_context = context.app.app_context()
    context.app_context.push()
    db.create_all()

    context.temp_dir = Path(tempfile.mkdtemp(prefix='gradeinsight_'))
    context.state = {}
    context.notifications = []
    context.backup_notifications_enabled = False


def after_scenario(context, scenario):
    db.session.remove()
    db.drop_all()
    context.app_context.pop()
    if hasattr(context, 'temp_dir') and context.temp_dir.exists():
        shutil.rmtree(str(context.temp_dir), ignore_errors=True)
