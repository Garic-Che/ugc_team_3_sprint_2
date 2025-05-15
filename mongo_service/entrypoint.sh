#!/bin/sh

exec uvicorn main:app --host $MONGO_SERVICE_HOST --port $MONGO_SERVICE_PORT --reload