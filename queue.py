from queue import Queue
from dataclasses import dataclass

@dataclass
class FormulaCreatedEvent:
    formula_name: str
    formula_hash: int
    
class FragranceQueue:
    def __init__(self):
        """
        Initializes a queue for processing formula created events.
        """
        self._formula_created_queue = Queue()

    def publish_formula_created(self, formula):
        event = FormulaCreatedEvent(formula.name, hash(formula))
        self._formula_created_queue.put(event)
    
    def get_next_event(self, block=True, timeout=None):
        # block = queue waits for an item instead of raising queue.empty immeudately
        # timeout = specifies how long to wait if block == True, or None == wait forever
        return self._formula_created_queue.get(block=block, timeout=timeout)
    
    def task_done(self):
        self._formula_created_queue.task_done()

    def is_empty(self):
        return self._formula_created_queue.empty()
    

def process_formula_events(queue: FragranceQueue):
    while True:
        event = queue.get_next_event()
        print(f"[Consumer] Processing formula created: {event.formula_name} (hash: {event.formula_hash})")
        queue.task_done()

def start_consumer(queue: FragranceQueue):
    import threading
    thread = threading.Thread(target=process_formula_events, args=(queue,), daemon=True)
    thread.start()
    
