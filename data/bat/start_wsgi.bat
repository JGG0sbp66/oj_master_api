@echo off
start cmd /k "cd ..\.. && waitress-serve --host=0.0.0.0 --port=5000 --threads=16 wsgi:app"