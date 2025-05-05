#!/bin/sh
gunicorn --bind $UGC_SERVICE_HOST:$UGC_SERVICE_PORT --workers 4 --worker-class gevent wsgi_app:app

exec "$@"