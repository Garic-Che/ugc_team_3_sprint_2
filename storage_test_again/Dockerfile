FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

COPY . /app

RUN apt-get update && apt-get install -y && libpq5

CMD ["python", "-u", "/app/storage_test.py"]