FROM python:3.12.1

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh

WORKDIR /app/src

ENTRYPOINT ["/app/entrypoint.sh"]