# Проектная работа 9 спринта

[Описание сервиса theatre_service](./theatre_service/README.md)

[Описание сервиса auth_service](./auth_service/README.md)

[Описание сервиса ugc_service](./ugc_service/README.md)

[Cистемные требования](./SYS-REQUIREMENTS.md)

[Исследование по выбору хранилища (clickhouse | vertica)](./storage_test/readme.md)

## Схема взаимодействия сервисов

![image](./docs/to_be/to_be.png)

## Запуск сервиса

- Переменные среды для всех сервисов положить в файл *.env* по примеру файла *.env.sample*
- запустить `docker compose up -d`

## Схема UGC таблиц:

```
shard.clicks:
    id UUID,
    event_time DateTime64(3, 'UTC'),
    user_id UUID,
    page_url String,
    content_type Enum16
```

```
shard.visits:
    id UUID,
    user_id UUID,
    page_url String,
    page_type Enum16('film', 'account', 'settings', 'finance'),
    started_at DateTime64(3, 'UTC'),
    finished_at DateTime64(3, 'UTC'),
```

```
shard.resolution_changes:
    id UUID,
    event_time DateTime64(3, 'UTC'),
    user_id UUID,
    video_id UInt32,
    target_resolution Enum8('480', '720', '1080', '1440', '4K', '8K'),
    origin_resolution Enum8('480', '720', '1080', '1440', '4K', '8K')
```

```
shard.completed_viewings:
    id UUID,
    event_time DateTime64(3, 'UTC'),
    user_id UUID,
    video_id UInt32
```

```
shard.filter_applications:
    id UUID,
    event_time DateTime64(3, 'UTC'),
    user_id UUID,
    filter_type Enum8('genre', 'rate', 'actors'),
    filter_value String
```
