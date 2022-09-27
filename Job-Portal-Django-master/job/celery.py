from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab
# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "job.settings")

app = Celery("job")
app.conf.enable_utc = False
app.conf.update(timezone='Africa/Accra')
app.conf.beat_schedule = {
    "update_job_csv_at_every_10_minutes":{
        "task": "dashboard.tasks.update_job_data",
        "schedule": crontab(minute="*", day_of_week="mon,tue,wed,thu,fri,sat")
    },
    "get_resume_datasets_every_week":{
        "task": "dashboard.tasks.get_resume_data",
        "schedule": crontab(hour="18", minute="45", day_of_week="mon,tue,wed,thu,fri,sat")
    },
    "extract_newsapi_data":{
        "task": "dashboard.tasks.extract_news_data",
        "schedule": crontab(hour="18", minute="30", day_of_week="mon,tue,wed,thu,fri,sat,sun")
    },
    "clean_job_dataset":{
        "task" : "dashboard.tasks.clean_job_data",
        "schedule" : crontab(minute="*", day_of_week="mon,tue")
    }
}

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f"Request {self.request!r}")
