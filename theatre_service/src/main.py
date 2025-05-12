import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
import sentry_sdk

from api.v1 import films, genres, persons
from core.config import settings
from db.redis import init_redis
from db import search_engine
from db.elasticsearch_engine import init_elastic

sentry_sdk.init(dsn=settings.sentry_dsn_theatre)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Код, выполняемый при запуске приложения
        app.state.cache_engine = await init_redis()
        search_engine.engine = await init_elastic()
        yield
    except Exception as e:
        logging.error(f"Lifespan error: {e}")
        raise
    finally:
        # Код, выполняемый при завершении работы приложения
        await app.state.cache_engine.close()
        await search_engine.engine.client.close()


app = FastAPI(
    title=settings.project_name,
    description=settings.project_description,
    version=settings.project_version,
    docs_url="/api/v1/theatre/openapi",
    openapi_url="/api/v1/theatre/openapi.json",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)


# Подключаем роутер к серверу, указав префикс
# Теги указываем для удобства навигации по документации
app.include_router(films.router, prefix="/api/v1/films", tags=["films"])
app.include_router(persons.router, prefix="/api/v1/persons", tags=["persons"])
app.include_router(genres.router, prefix="/api/v1/genres", tags=["genres"])
