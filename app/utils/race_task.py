from celery.schedules import crontab
from ..extensions import celery
from ..services.race_service import update_race_status


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # 每分钟执行一次状态检查
    sender.add_periodic_task(
        crontab(minute='*'),
        check_race_status.s(),
        name='check race status every minute'
    )


@celery.task
def check_race_status():
    try:
        update_race_status()
        return {'success': True, 'message': 'Race status updated'}
    except Exception as e:
        return {'success': False, 'message': str(e)}
