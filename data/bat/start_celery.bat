@echo off
start cmd /k "celery -A app.extensions.celery worker --pool=solo --loglevel=info"
start cmd /k "celery -A app.extensions.celery beat --loglevel=info"