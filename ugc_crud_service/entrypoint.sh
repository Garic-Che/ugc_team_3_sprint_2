#!/bin/sh

exec uvicorn main:app --host $UGC_CRUD_SERVICE_HOST --port $UGC_CRUD_SERVICE_PORT --reload