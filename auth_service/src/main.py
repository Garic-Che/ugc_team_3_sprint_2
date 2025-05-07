import logging
from contextlib import asynccontextmanager
import uuid

from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse
from starlette.middleware.sessions import SessionMiddleware
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

from utils.initial_data import init_roles_and_privileges
from api.v1 import users, roles, provider_auth
from core import config
from core.config import settings
from db.redis import init_redis, init_limiter_redis
from db.postgres import get_session
from db.auth_engine import AuthEngine

def configure_tracing():
    # Создаем ресурс с именем сервиса
    resource = Resource(attributes={
        SERVICE_NAME: settings.auth_project_name
    })

    # Настраиваем провайдер трассировки
    trace.set_tracer_provider(TracerProvider(resource=resource))

    # Настраиваем экспортер Jaeger
    jaeger_exporter = JaegerExporter(
        agent_host_name=settings.jaeger_host,
        agent_port=settings.jaeger_port,
    )

    # Добавляем процессор для экспорта спанов
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(jaeger_exporter)
    )

def add_tracing_middleware(app: FastAPI):
    @app.middleware("http")
    async def tracing_middleware(request: Request, call_next):
        # Получаем или создаем request_id
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))

        # Получаем текущий span и добавляем request_id как атрибут
        span = trace.get_current_span()
        if span.is_recording():
            span.set_attribute("http.request_id", request_id)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute("http.method", request.method)

        # Продолжаем обработку запроса
        response = await call_next(request)

        # Добавляем request_id в заголовки ответа
        response.headers["X-Request-ID"] = request_id

        if span.is_recording():
            span.set_attribute("http.status_code", response.status_code)

        return response

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Инициализация трассировки
        if settings.enable_tracing:
            configure_tracing()
            logging.info("Tracing initialized")

        # Инициализация Redis
        redis = await init_redis()
        app.state.token_engine = redis
        logging.info("Redis initialized")

        # Инициализация ролей и привилегий
        session_gen = get_session()
        session = await anext(session_gen)
        try:
            auth_engine = AuthEngine(redis=redis, session=session)
            await init_roles_and_privileges(auth_engine)
            logging.info("Роли и привилегии успешно инициализированы.")
        finally:
            await session.close()
            await session_gen.aclose()
        
        limiter_redis = await init_limiter_redis()
        await FastAPILimiter.init(limiter_redis)

        yield
    except Exception as e:
        logging.error(f"Lifespan error: {e}", exc_info=True)
        raise
    finally:
        # Закрываем соединение с Redis
        if hasattr(app.state, "token_engine"):
            await app.state.token_engine.close()

app = FastAPI(
    title=config.settings.auth_project_name,
    description=config.settings.auth_project_description,
    version=config.settings.auth_project_version,
    docs_url="/api/v1/auth/openapi",
    openapi_url="/api/v1/auth/openapi.json",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

# Инструментируем FastAPI приложение для трассировки
if settings.enable_tracing:
    FastAPIInstrumentor.instrument_app(app)
    add_tracing_middleware(app)

# Добавляем middleware для сессий
app.add_middleware(SessionMiddleware, secret_key=settings.auth_secret_key)

# Подключаем роутеры
app.include_router(users.router, prefix="/api/v1/user", tags=["user"])
app.include_router(roles.router, prefix="/api/v1/role", tags=["role"])
app.include_router(provider_auth.router, prefix="/api/v1/user", tags=["provider auth"])
