import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transaction_service.settings')

app = Celery('transaction_service')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.broker_url = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/1')
app.conf.result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/1')
app.autodiscover_tasks(['tasks'])

app.conf.beat_schedule = {
    'soft-delete-old-transactions-daily': {
        'task': 'tasks.celery_tasks.soft_delete_old_transactions',
        'schedule': 60 * 60 * 24,
    },
    'send-due-date-reminders-daily': {
        'task': 'tasks.celery_tasks.send_due_date_reminders',
        'schedule': 60 * 60 * 24,
    },
}
