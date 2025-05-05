# Используем официальный образ Python
FROM python:3.11

# Устанавливаем рабочую директорию
WORKDIR /app/src

# Копируем зависимости
COPY requirements.txt /app

# Устанавливаем зависимости
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

# Копируем исходный код приложения
COPY . /app

# Копируем статику Flasgger в отдельную директорию
RUN mkdir -p /app/flasgger_static && \
    cp -r /usr/local/lib/python3.11/site-packages/flasgger/ui3/static/* /app/flasgger_static/

RUN chmod +x /app/entrypoint.sh

# Команда для запуска приложения
ENTRYPOINT ["/app/entrypoint.sh"]