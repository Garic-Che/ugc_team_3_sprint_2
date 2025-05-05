# Используем официальный образ Python
FROM python:3.10-slim

# Устанавливаем системные зависимости для ClickHouse-Driver
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir -r requirements.txt && \
    apt-get remove -y gcc python3-dev && \
    apt-get autoremove -y

# Копируем исходный код
COPY . .

ENV PYTHONUNBUFFERED=1

# Команда запуска
CMD ["python", "main.py"]