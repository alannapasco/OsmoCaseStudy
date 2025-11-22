import pytest
from OsmoCaseStudy.queue import FormulaCreatedQueue

from OsmoCaseStudy.queue import FormulaCreatedEvent
from OsmoCaseStudy.queue import InProcessEvent
from werkzeug.exceptions import InternalServerError

def test_publish_success(summer_breeze):
    q = FormulaCreatedQueue()
    assert q.is_empty() == True
    assert q.size() == 0
    assert len(q._in_process) == 0
    assert len(q._published_hashes) == 0
    q.publish(summer_breeze)
    assert q.is_empty() == False
    assert q.size() == 1
    assert len(q._in_process) == 0 # make sure the item is not in the processing dict
    assert len(q._published_hashes) == 1

def test_publish_idempotent(summer_breeze):
    q = FormulaCreatedQueue()
    q.publish(summer_breeze)
    with pytest.raises(InternalServerError) as e_info:
        q.publish(summer_breeze)

def test_get_next_item_success(summer_breeze, winter_breeze, another_summer_breeze):
    q = FormulaCreatedQueue()
    q.publish(summer_breeze)
    q.publish(another_summer_breeze)
    q.publish(winter_breeze)
    summer_breeze = q.get_next_item()
    assert summer_breeze.name == "Summer Breeze"

def test_get_next_item_expired_item(summer_breeze, winter_breeze):
    q = FormulaCreatedQueue()
    q.publish(winter_breeze) #priority 1
    q.publish(summer_breeze) #priority 2
    
    # modify the event such that more than 30 seconds have passed for priority 2
    in_process_event_mock = InProcessEvent(
        event=FormulaCreatedEvent(summer_breeze.name, hash(summer_breeze)),
        ack_deadline=35
    )
    q._in_process[hash(summer_breeze)] = in_process_event_mock

    next_item = q.get_next_item()

    # assert that priority 2 became priority 1
    assert next_item.name == "Summer Breeze"

def test_ack_success(summer_breeze):
    q = FormulaCreatedQueue()
    assert q.is_empty() == True
    assert len(q._in_process) == 0
    assert len(q._published_hashes) == 0

    q.publish(summer_breeze)
    assert q.is_empty() == False
    assert len(q._in_process) == 0
    assert len(q._published_hashes) == 1

    sb = q.get_next_item()
    assert q.is_empty() == True
    assert len(q._in_process) == 1
    assert len(q._published_hashes) == 1

    q.ack(sb.id)
    assert q.is_empty() == True
    assert len(q._in_process) == 0 
    assert len(q._published_hashes) == 1

def test_already_processed(summer_breeze):
    q = FormulaCreatedQueue()
    q.publish(summer_breeze)
    sb = q.get_next_item()
    q.ack(sb.id)
    assert q.already_processed(summer_breeze)

def test_remove_success(summer_breeze):
    q = FormulaCreatedQueue()
    q.publish(summer_breeze)
    assert q.is_empty() == False
    assert len(q._in_process) == 0
    assert len(q._published_hashes) == 1

    q.get_next_item()
    q.remove(summer_breeze)
    assert q.is_empty() == True
    assert len(q._in_process) == 0
    assert len(q._published_hashes) == 0

def test_remove_from_empty_success(summer_breeze):
    q = FormulaCreatedQueue()
    q.publish(summer_breeze)
    q.remove(summer_breeze)
    assert q.is_empty() == True
    assert len(q._in_process) == 0
    assert len(q._published_hashes) == 0

def test_remove_correct_item_with_dupe_name(summer_breeze, another_summer_breeze):
    q = FormulaCreatedQueue()
    # test adding two formulas with the same name (dif formulas)
    # and removing only one - ensure the correct one removed - ensure the correct one remains

    q.publish(summer_breeze)
    q.publish(another_summer_breeze)
    # remove another_summer_breeze; summer_breeze remains
    q.remove(another_summer_breeze)
    assert q.get_next_item().name == "Summer Breeze"




