import pytest

@pytest.mark.asyncio
async def test_likes_by_user(ugc_db, fetch):
    url = "http://ugc_crud_service:8000/api/v1/likes/user/550e8400-e29b-41d4-a716-446655440000"
    json_data = await fetch(url)

    #assert ugc_db.likes.count_documents({}) == 4
    assert json_data == []

