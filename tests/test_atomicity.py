import pytest
from unittest.mock import MagicMock, patch
from OsmoCaseStudy.app import FragranceServer
from OsmoCaseStudy.queue import FormulaCreatedQueue
from OsmoCaseStudy.database import FragranceDatabase

###########################################
# Testing `publish_with_retry` from app.py
###########################################
@patch("time.sleep", return_value=None) # patch time.sleep to save time while running test suite
def test_publish_success_first_try_size(summer_breeze, winter_breeze, another_summer_breeze):
    server = FragranceServer()
    db = FragranceDatabase()
    q = FormulaCreatedQueue()
    formulas = [summer_breeze, winter_breeze, another_summer_breeze]

    server.publish_with_retry(formulas, db, q)

    assert db.size() == 3
    assert q.size() == 3

@patch("time.sleep", return_value=None)
def test_publish_success_first_try_calls(summer_breeze, winter_breeze, another_summer_breeze):
    server = FragranceServer()
    db = MagicMock()
    q = MagicMock()
    formulas = [summer_breeze, winter_breeze, another_summer_breeze]

    server.publish_with_retry(formulas, db, q)

    db.add_formulas.assert_called_once_with(formulas)
    q.publish.assert_called_once_with(formulas)

    db.remove_formulas.assert_not_called()
    q.remove.assert_not_called()

@patch("time.sleep", return_value=None)
def test_publish_success_first_try(summer_breeze, winter_breeze, another_summer_breeze):
    server = FragranceServer()
    db = MagicMock()
    q = FormulaCreatedQueue()
    formulas = [summer_breeze, winter_breeze, another_summer_breeze]

    db.add_formulas.side_effect = [Exception("db fail"), None]

    server.publish_with_retry(formulas, db, q)
    assert q.size() == 3

@patch("time.sleep", return_value=None)
def test_publish_fails_once_then_succeeds(mock_sleep, summer_breeze, winter_breeze, another_summer_breeze):
    server = FragranceServer()
    db = MagicMock()
    q = MagicMock()
    formulas = [summer_breeze, winter_breeze, another_summer_breeze]

    # First call fails, second call succeeds
    db.add_formulas.side_effect = [Exception("db fail"), None]

    server.publish_with_retry(formulas, db, q)

    # First attempt
    assert db.add_formulas.call_count == 2  # failed once, then succeeded
    db.remove_formulas.assert_called_once_with(formulas)

    # sleep called once (between attempts)
    mock_sleep.assert_called_once_with(1.0)  # base_delay == 1

    # then queue.publish should only be called on second attempt
    q.publish.assert_called_once_with(formulas)

@patch("time.sleep", return_value=None)
def test_publish_all_retries_fail(mock_sleep, summer_breeze, winter_breeze, another_summer_breeze):
    server = FragranceServer()
    db = MagicMock()
    q = MagicMock()
    formulas = [summer_breeze, winter_breeze, another_summer_breeze]

    db.add_formulas.side_effect = Exception("db fail")

    with pytest.raises(Exception):
        server.publish_with_retry(formulas, db, q) #default is 3 attempts

    # 3 attempts ==> 3 add_formulas calls
    assert db.add_formulas.call_count == 3
    assert q.publish.call_count == 0 # we never make it here bc error in db
    # Rollback happens 3 times 
    assert db.remove_formulas.call_count == 3
    assert q.remove.call_count == 3
    # sleep called twice 
    assert mock_sleep.call_count == 2
    mock_sleep.assert_any_call(1.0)
    mock_sleep.assert_any_call(2.0)

    assert q.is_empty()
    assert db.is_empty()