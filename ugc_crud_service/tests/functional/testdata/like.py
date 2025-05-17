from uuid import uuid4
from bson import Binary

likes = [
    {
        "_id": Binary.from_uuid(uuid4()),
        "user_id": Binary.from_uuid(uuid4()),
        "content_id": "2a7d84a6-befe-437d-8813-e6d5bb06a34f",
        "created_at": "2025-05-09 10:00:00.123456",
    },
]