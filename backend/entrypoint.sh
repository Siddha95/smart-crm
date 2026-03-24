#!/bin/sh
set -e

python manage.py collectstatic --noinput
python manage.py migrate --noinput

exec uvicorn config.asgi:application \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1
