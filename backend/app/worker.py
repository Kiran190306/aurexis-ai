"""
Celery Worker Configuration
Celery application factory and task definitions for background processing
"""
from celery import Celery
from celery.schedules import crontab
from loguru import logger
import os

from app.core.config import settings


def create_celery_app() -> Celery:
    """
    Create and configure Celery application
    
    Returns:
        Celery application instance
    """
    # Create Celery app
    celery_app = Celery(
        'aurexis_worker',
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
        include=[
            'app.tasks.document_tasks',
            'app.tasks.knowledge_tasks',
            'app.tasks.agent_tasks',
            'app.tasks.computer_tasks',
        ]
    )
    
    # Configure Celery
    celery_app.conf.update(
        # Task settings
        task_track_started=True,
        task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
        task_soft_time_limit=settings.CELERY_TASK_TIME_LIMIT - 60,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        task_default_queue='default',
        task_queues={
            'default': {
                'exchange': 'default',
                'routing_key': 'default',
            },
            'documents': {
                'exchange': 'documents',
                'routing_key': 'documents',
            },
            'knowledge': {
                'exchange': 'knowledge',
                'routing_key': 'knowledge',
            },
            'agents': {
                'exchange': 'agents',
                'routing_key': 'agents',
            },
            'computer': {
                'exchange': 'computer',
                'routing_key': 'computer',
            },
        },
        task_default_exchange='default',
        task_default_routing_key='default',
        
        # Result backend settings
        result_expires=3600,  # 1 hour
        result_extended=True,
        
        # Serialization
        task_serializer='json',
        result_serializer='json',
        accept_content=['json'],
        
        # Timezone
        timezone='UTC',
        enable_utc=True,
        
        # Worker settings
        worker_prefetch_multiplier=4,
        worker_max_tasks_per_child=1000,
        
        # Retry settings
        task_autoretry_for=(Exception,),
        task_retry_delay=60,
        task_retry_max=3,
        task_retry_backoff=True,
        task_retry_backoff_max=600,
        task_retry_jitter=True,
        
        # Beat scheduler settings
        beat_schedule={
            'cleanup-old-documents': {
                'task': 'app.tasks.document_tasks.cleanup_old_documents',
                'schedule': crontab(hour=2, minute=0),  # 2 AM daily
            },
            'cleanup-old-executions': {
                'task': 'app.tasks.agent_tasks.cleanup_old_executions',
                'schedule': crontab(hour=3, minute=0),  # 3 AM daily
            },
        },
    )
    
    return celery_app


# Lazy-loaded Celery app instance
_celery_app = None


def get_celery_app():
    global _celery_app
    if _celery_app is None:
        _celery_app = create_celery_app()
        # Import tasks to register them
        try:
            from app.tasks import document_tasks, knowledge_tasks, agent_tasks, computer_tasks
            logger.info("Celery tasks imported successfully")
        except ImportError as e:
            logger.warning(f"Could not import Celery tasks: {e}")
    return _celery_app


# For task decorators that need the actual app at module import time
# This is used by task modules
_celery_app_for_tasks = None


def _get_celery_app_for_tasks():
    global _celery_app_for_tasks
    if _celery_app_for_tasks is None:
        _celery_app_for_tasks = create_celery_app()
    return _celery_app_for_tasks


# Create a module-level variable that task modules can import
# This is initialized lazily on first access
class _CeleryAppProxy:
    def __getattr__(self, name):
        app = _get_celery_app_for_tasks()
        return getattr(app, name)


celery_app = _CeleryAppProxy()


if __name__ == '__main__':
    celery_app.start()
