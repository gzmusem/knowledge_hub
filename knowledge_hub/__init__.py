# 确保Celery app在Django启动时创建
from .celery import app as celery_app

__all__ = ['celery_app']