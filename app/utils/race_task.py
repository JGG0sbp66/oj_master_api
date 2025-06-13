from celery.schedules import crontab
from app.extensions import celery
from .. import create_app
from ..services.race_service import update_race_status, race_reminder


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # 每分钟执行一次状态检查
    sender.add_periodic_task(
        crontab(minute='*'),
        check_race_status.s(),
        name='每分钟检测比赛状态'
    )

    sender.add_periodic_task(
        crontab(minute='*'),
        race_reminder_task.s(),
        name='定期发送比赛提醒'
    )


@celery.task
def check_race_status():
    try:
        update_race_status()
        return {'success': True, 'message': '比赛状态已更新'}
    except Exception as e:
        return {'success': False, 'message': str(e)}


@celery.task
def race_reminder_task():
    app = create_app()
    with app.app_context():
        try:
            res = race_reminder()
            if res['success']:
                return {"success": True, "message": "所有提醒邮件发送成功"}
            else:
                return {"success": False, "message": res['message']}
        except Exception as e:
            return {'success': False, 'message': str(e)}
