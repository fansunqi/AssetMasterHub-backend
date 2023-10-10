#!/bin/sh
python3 manage.py migrate

# TODO Start: [Student] Run with uWSGI instead
# python3 manage.py runserver 80
uwsgi --module=CS_Company_backend.wsgi:application \
    --env DJANGO_SETTINGS_MODULE=CS_Company_backend.settings \
    --master \
    --http=0.0.0.0:80 \
    --processes=5 \
    --harakiri=20 \
    --max-requests=5000 \
    --vacuum
# TODO End: [Student] Run with uWSGI instead