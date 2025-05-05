#!/bin/sh

echo "Waiting for postgres..."
while ! nc -z $SQL_HOST $SQL_PORT; do
  sleep 0.1
done
echo "PostgreSQL started"

python manage.py migrate --fake --fake movies 0001
python manage.py migrate --no-input
python manage.py createsuperuser --login admin --noinput || true

gunicorn config.wsgi:application --bind $DJANGO_ADMIN_HOST:$DJANGO_ADMIN_PORT --reload

exec "$@"