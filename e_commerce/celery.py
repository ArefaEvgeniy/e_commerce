import os

from celery import Celery
from celery.schedules import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_commerce.settings')

app = Celery('e_commerce')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.timezone = 'UTC'
app.conf.beat_schedule = {
    'low-stock-check': {
        'task': 'shop.tasks.notify_low_stock_products',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
        # 'schedule': crontab(hour=9, minute=0),  # Every day at 9:00 AM
    },
}

# import os
#
# from celery import Celery
# from django.conf import settings
#
#
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_commerce.settings')
#
# app = Celery('e_commerce')
# app.config_from_object('django.conf:settings', namespace='CELERY')
# app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
