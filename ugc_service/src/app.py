import logging
from http import HTTPStatus

from flask import Flask, request, jsonify
from flasgger import Swagger
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

from core.config import settings
from db.kafka import send_to_broker
from schemas.entity import EventSchema, ma
from utils.auth_middleware import internal_auth_required

sentry_sdk.init(
    dsn=settings.sentry_dsn,
    integrations=[FlaskIntegration()],
)

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "UGC-API",
        "description": "Документация к API",
        "version": "1.0",
    },
    "securityDefinitions": {
        "InternalAuth": {
            "type": "apiKey",
            "name": "X-Internal-Auth",
            "in": "header",
        }
    },
    "security": [{"InternalAuth": []}],
    "components": {
        "schemas": {
            "EventInput": {
                "type": "object",
                "required": ["timestamp", "event", "user_id"],
                "properties": {
                    "timestamp": {"type": "integer", "example": 1672531200},
                    "event": {"type": "string", "example": "page_view"},
                    "user_id": {
                        "type": "string",
                        "example": "4e7e4fb5-7dac-4816-95f8-715cf4c220ab",
                    },
                },
            },
            "SuccessResponse": {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "message": {"type": "string"},
                    "event": {"type": "object"},
                },
            },
            "ErrorResponse": {
                "type": "object",
                "properties": {"message": {"type": "string"}},
            },
        },
    },
}

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "openapi",
            "route": "/api/v1/ugc/openapi.json",
            "static_url_path": "/flasgger_static",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api/v1/ugc/openapi",
}

app = Flask(__name__)
ma.init_app(app)
swagger = Swagger(app, config=swagger_config, template=swagger_template)

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    storage_uri=settings.ugc_limiter_redis_url,
)

event_schema = EventSchema()


@app.route("/api/v1/event", methods=["POST"])
@internal_auth_required
@limiter.limit("10 per second")
def handle_event():
    """
    Обработчик событий
    ---
    tags: [Events]
    consumes: [application/json]
    produces: [application/json]
    parameters:
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/components/schemas/EventInput'
    responses:
      200:
        description: Событие успешно отправлено
        schema:
          $ref: '#/components/schemas/SuccessResponse'
      400:
        description: Неверный запрос
        schema:
          $ref: '#/components/schemas/ErrorResponse'
      401:
        description: Требуется аутентификация
        schema:
          $ref: '#/components/schemas/ErrorResponse'
      403:
        description: Неверная аутентификация
        schema:
          $ref: '#/components/schemas/ErrorResponse'
      422:
        description: Ошибка валидации
        schema:
          $ref: '#/components/schemas/ErrorResponse'
      429:
        description: Превышен лимит запросов
        schema:
          $ref: '#/components/schemas/ErrorResponse'
      500:
        description: Внутренняя ошибка сервера
        schema:
          $ref: '#/components/schemas/ErrorResponse'
    """
    try:
        raw_data = request.get_json()

        if not raw_data:
            logging.error("No data provided")
            return jsonify(
                {"message": "No data provided"}
            ), HTTPStatus.BAD_REQUEST

        errors = event_schema.validate(raw_data)
        if errors:
            logging.error(f"Validation errors: {errors}")
            return jsonify(
                {"message": "Validation failed"}
            ), HTTPStatus.UNPROCESSABLE_ENTITY

        event_data = event_schema.load(raw_data)
        logging.info(f"Received valid event: {event_data}")

        send_to_broker(
            topic=settings.kafka_topic_name,
            value=event_data,
        )

        return jsonify(
            {"message": "Event sent to broker", "event": event_data}
        ), HTTPStatus.OK

    except Exception as e:
        logging.error(f"Error processing event: {str(e)}")
        return jsonify(
            {"message": "Internal server error"}
        ), HTTPStatus.INTERNAL_SERVER_ERROR


if __name__ == "__main__":
    app.run(debug=True)
