from collections import deque
from werkzeug.exceptions import InternalServerError
from dataclasses import dataclass, field
from threading import Lock
import time

from OsmoCaseStudy.models.fragrance_formula import FragranceFormula

@dataclass
class FormulaCreatedEvent:
    name: str
    id: int
    created_timestamp: int = field(default_factory=time.time_ns)

@dataclass
class InProcessEvent:
    event: FormulaCreatedEvent
    ack_deadline: float
    
class FormulaCreatedQueue:
    def __init__(self, process_timeout=30):
        """
        Initializes a queue for publishing a events when formulas are created.

        This queue can be used to notify other components when a new formula has been added and requires further processing. Only the formula name and hashcode (id) are stored in the queue. The hashcode can be used to look up the formula in the db, and the name can be used for quick logging etc that should not require an entire lookup.
        """
        # Represent the 3 stages of event processing
        self._formula_created_queue = deque() # new events, waiting to be processed
        self._in_process = {} # Key: id, Value: InProcessEvent - event fetched by consumer, being processed
        self._published_hashes = set() # set of all id's of formulas that have been published
        
        self._lock = Lock()
        self.process_timeout = process_timeout
        
    def publish(self, formulas):
        if isinstance(formulas, list):
            for formula in formulas:
                self.publish_one(formula)
        elif isinstance(formulas, FragranceFormula):
            self.publish_one(formulas)

    def publish_one(self, formula):
        id = hash(formula) # db also uses hash as id/Key

        if id in self._published_hashes:
            # we have already published that this formula has been created - do not publish it again
            raise InternalServerError(f"This formula already exists in the queue")
        
        event = FormulaCreatedEvent(formula.name, id)
        with self._lock:
            self._formula_created_queue.append(event)
            self._published_hashes.add(id)
        return id

    def get_next_item(self):
        with self._lock:
            # return unack'ed messages to queue if process-timeout expired
            now = time.time()
            # gather list of all events that are still "processing" but have exceeded their ack deadline (default: 30 seconds)
            expired = [id for id, event in self._in_process.items() if event.ack_deadline <= now]
            for id in expired:
                # prioritize items that have been waiting a long time; append them to left (benefits of deque)
                self._formula_created_queue.appendleft(self._in_process.pop(id).event)

            if not self._formula_created_queue:
                return None
            
            next_item = self._formula_created_queue.popleft()
            self._in_process[next_item.id] = InProcessEvent(
                event=next_item,
                ack_deadline=time.time() + self.process_timeout
            )
            return next_item
        
    def ack(self, id: int):
        # for client to call when the "processing" is complete
        with self._lock:
            return self._in_process.pop(id, None) is not None

    def is_empty(self):
        return len(self._formula_created_queue) == 0 
    
    def size(self):
        return len(self._formula_created_queue)
    
    def already_processed(self, formula):
        # only used in unit tests eg assert already-published
        return hash(formula) in self._published_hashes
    
    def remove(self, formulas):
        if isinstance(formulas, list):
            for formula in formulas:
                self.remove_one(formula)
        elif isinstance(formulas, FragranceFormula):
            self.remove_one(formulas)

    def remove_one(self, formula):
        id = hash(formula)

        with self._lock:
            # clean up all three elements helping support the queue
            # don't let a ValueError from one block another
            try:
                self.remove_event_from_queue_by_id(id)
            except ValueError:
                pass

            try:
                self._in_process.pop(id, None)
            except ValueError:
                pass

            try:
                # Remove from published hashes to allow retry
                self._published_hashes.discard(id)
            except ValueError:
                pass

    def remove_event_from_queue_by_id(self, id: int):
        # the Deque built-in .remove() function already operates at O(n)
        # therefore this could be made more efficient
        for event in self._formula_created_queue:
            if event.id == id:
                self._formula_created_queue.remove(event)
                return True
        return False