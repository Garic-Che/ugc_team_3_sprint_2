import pytest
from http.client import OK


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "start_date, end_date, expected_status, expected_bookmark_num",
    [
        ("2021-01-01T10:00:00", "2021-01-02T13:00:00", 200, 3),
        ("2021-01-01T10:00:00", "2021-01-02T12:00:00", 200, 2),
        ("2021-01-02T00:00:00", "2021-01-02T23:59:59", 200, 1),
        ("2021-01-03T00:00:00", "2021-01-03T23:59:59", 200, 0),
        ("2021-01-04T00:00:00", "2021-01-03T23:59:59", 200, 0),
        ("non-date param", "2021-01-03T23:59:59", 422, None),
        ("2021-01-04T00:00:00", "non-date param", 422, None),
    ]
)
async def test_timerange_search(start_date, end_date, expected_status, expected_bookmark_num, fetch):
    # Act
    status, bookmarks = await fetch(f"bookmarks/timerange/{start_date}/{end_date}")
    
    # Assert
    assert status == expected_status
    if expected_status == OK:
        assert len(bookmarks) == expected_bookmark_num
        assert all([(start_date <= bookmark["created_at"] < end_date) for bookmark in bookmarks])