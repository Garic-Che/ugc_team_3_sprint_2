#!/bin/sh
#alembic revision --autogenerate -m "initial"
alembic upgrade head
uvicorn main:app --host $AUTH_SERVICE_HOST --port $AUTH_SERVICE_PORT --reload

exec "$@"