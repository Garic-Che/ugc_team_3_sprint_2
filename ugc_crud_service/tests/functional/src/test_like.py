import pytest
from http.client import OK


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user_id, expected_status, expected_like_num",
    [
        ("476bff82-92d5-4c21-99ef-67cbbdd5fd5e", 200, 3),
        ("550e8400-e29b-41d4-a716-446655440000", 200, 1),
        ("c9d4c530-7657-4ca3-bc8d-0b888e65000b", 200, 0),
        ("invalid uuid", 422, None),
    ]
)
async def test_user_search(user_id, expected_status, expected_like_num, fetch):
    # Act
    status, likes = await fetch(f"likes/user/{user_id}")
    
    # Assert
    assert status == expected_status
    if expected_status == OK:
        assert len(likes) == expected_like_num
        assert all([like["user_id"] == user_id for like in likes])


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "content_id, expected_status, expected_like_num",
    [
        ("a7f12e4b-5c8d-40e9-821e-9d2b3478f1a5", 200, 1),
        ("550e8400-e29b-41d4-a716-446655440000", 200, 0),
        ("invalid uuid", 422, None),
    ]
)
async def test_content_search(content_id, expected_status, expected_like_num, fetch):
    # Act
    status, likes = await fetch(f"likes/content/{content_id}")
    
    # Assert
    assert status == expected_status
    if expected_status == OK:
        assert len(likes) == expected_like_num
        assert all([like["content_id"] == content_id for like in likes])


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "content_id, expected_status, expected_avg_rate",
    [
        ("c9d4c530-7657-4ca3-bc8d-0b888e65000b", 200, 7.5),
        ("a7f12e4b-5c8d-40e9-821e-9d2b3478f1a5", 200, 10),
        ("a7f12e4b-5c8d-40e9-821e-9d2b3478f1a4", 404, None),
        ("invalid uuid", 422, None),
    ]
)
async def test_like_avg_rate(content_id, expected_status, expected_avg_rate, fetch):
    # Act
    status, avg_rate = await fetch(f"likes/avg_rate/{content_id}")
    
    # Assert
    assert status == expected_status
    if expected_status == OK:
        assert avg_rate == expected_avg_rate
