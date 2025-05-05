from flask_marshmallow import Marshmallow
from marshmallow import validate

ma = Marshmallow()


class EventSchema(ma.Schema):
    """
    Схема валидации событий
    """

    timestamp = ma.Integer(
        required=True,
        validate=validate.Range(min=0),
        error_messages={
            "required": "Timestamp is required",
            "invalid": "Timestamp must be UNIX timestamp (integer)",
        },
    )
    event = ma.String(
        required=True,
        error_messages={
            "required": "Event type is required",
            "invalid": "Event must be a string",
        },
    )
    user_id = ma.String(
        required=True,
        error_messages={
            "required": "User ID is required",
            "invalid": "User ID must be a string",
        },
    )

    class Meta:
        strict = True


event_schema = EventSchema()
