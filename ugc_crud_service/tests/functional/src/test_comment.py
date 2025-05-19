import pytest
from http.client import OK


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "search_term, expected_status, expected_match_num",
    [
        ("words", 200, 2),
        ("proud", 200, 1),
        ("random", 200, 1),
        ("nonsense", 200, 0),
        ("put into sentence", 200, 1),
    ]
)
async def test_fulltext_search(search_term, expected_status, expected_match_num, fetch):
    # Act
    status, comments = await fetch(f"comments/search/{search_term}")
    
    # Assert
    assert status == expected_status
    if expected_status == OK:
        assert len(comments) == expected_match_num
