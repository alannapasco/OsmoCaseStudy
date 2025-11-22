
import time
from werkzeug.exceptions import Conflict

def publish_with_retry(formulas, db, queue, retries=3, base_delay=1.0, max_delay=10.0):
    """
    Attempts to 
    - store one or many formulas to a database and
    - publish the formula(s) to a messaging queue 
    with exponential backoff.
    """
    for attempt in range(retries):
        try:
            db.add_formulas(formulas)
            queue.publish(formulas)
            return
        except Exception as e:
            # Rollback first:
            db.remove_formulas(formulas) # if formula isn't found, returns None 
            queue.remove(formulas)  # theoretically we should almost never get here because if both the db and the queue were both updated, it should have been a success. But to cover all cases, we do handle cleaning up the queue as part of the rollback strategy. Perhaps network was lost immeduately after publishing to queue but before returning success message. 

            if attempt == retries - 1:
                # when final attempt has failed
                # if isinstance(e, Conflict):
                #     if queue.already_processed(formulas): ##TODO this only handles one
                #         return # this means the request came in twice
                raise 

            # Exponential backoff:
            delay = min(base_delay * (2 ** attempt), max_delay) #formula for delay can be made more complex by adding "jitter" - a randomized small number to add to the delay that changes every time we reach here so that the delay doesn't grow 'perfectly' exponentially but slightly differently each time it grows. 
            time.sleep(delay)