from flask import Flask, request, jsonify
from werkzeug.exceptions import BadRequest, HTTPException, Conflict
from threading import Lock
import time
from OsmoCaseStudy.database import FragranceDatabase
from OsmoCaseStudy.queue import FormulaCreatedQueue
from OsmoCaseStudy.validations import validate_request

class FragranceServer: 
    """
    a REST API endpoint that:
    - accepts fragrance formula submissions
    - saves them to a database and
    - publishes them to a message queue that could inform downstream services that a new formula has been added
    """
    def __init__(self):
        self.app = Flask(__name__)
        self.db = FragranceDatabase()
        self.q = FormulaCreatedQueue()

        self.idempotency_cache = {} # Key: key from header, Value: response from submit_formula
        self.idempotency_lock = Lock()

        self.register_routes() 

        # This is for neatly printing error messages to output
        self.app.register_error_handler(HTTPException, self.handle_http_error)

    def register_routes(self):
        @self.app.route("/formulas", methods=["POST"])
        def submit_formula():
            
            ## Handle idempotency 
            idempotency_key = request.headers.get("Idempotency-Key")
            if not idempotency_key:
                raise BadRequest("Missing Idempotency-Key header")
            with self.idempotency_lock:
                if idempotency_key in self.idempotency_cache:
                    # Return same response as original request
                    response = self.idempotency_cache[idempotency_key]
                    return self.parse_response(response)

            ## Gather data from request
            data = request.get_json()
            fragrance_formulas = validate_request(data)

            ## Process request
            try:
                response = self.publish_with_retry(fragrance_formulas, self.db, self.q)
            except Exception as e:
                response = e
            
            with self.idempotency_lock:
                self.idempotency_cache[idempotency_key] = response

            return self.parse_response(response)
        
    def publish_with_retry(self, formulas, db, queue, retries=3, base_delay=1.0, max_delay=10.0):
        """
        Attempts to 
        - store one or many formulas to a database and
        - publish the formula(s) to a messaging queue
        and implements a rollback strategy with exponential backoff.
        """
        for attempt in range(retries):
            try:
                db.add_formulas(formulas)
                queue.publish(formulas)
                return None # represents success
            except Conflict as e:
                raise # duplicate formula entry to db - no need to rollback
            except Exception as e:
                # Rollback first: - to maintain atomicity
                db.remove_formulas(formulas)
                queue.remove(formulas) 

                if attempt == retries - 1:
                    # when final attempt has failed
                    raise

                # Exponential backoff: - to not overload the server with instintaneous requests 
                delay = min(base_delay * (2 ** attempt), max_delay) #formula for delay can be made more complex by adding "jitter" - a randomized small number to add to delay that changes every time we reach here so that the delay doesn't grow 'perfectly' exponentially but slightly differently each time it grows. 
                time.sleep(delay)
        
    def parse_response(self, response):
        """
        Either returns a success JSON response or raises an Exception.
        `response` is either:
         - None: represents successful processing 
         - an Exception: represents what went wrong during publishing
        in order to support both results from `publish_with_retry()`
        """
        if response is None:
            return jsonify({"message": f"Formula(s) added!"}), 200
        else:
            raise response

    def handle_http_error(self, e):
        """
        Neatly handles error output
        """
        response = {
            "error": e.name,
            "message": e.description,
            "status": e.code
        }
        return jsonify(response), e.code
    
    def run(self, **kwargs):
        self.app.run(**kwargs)

def create_app():
    # Needed for flask to find and create the app at launch
    server = FragranceServer()
    return server.app

if __name__ == "__main__":
    server = FragranceServer()
    server.run(debug=True)