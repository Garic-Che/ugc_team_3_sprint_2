#!/bin/sh

uvicorn main:app --host $THEATRE_SERVICE_HOST --port $THEATRE_SERVICE_PORT --reload

exec "$@"