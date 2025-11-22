from flask import Flask, request, jsonify
from werkzeug.exceptions import BadRequest, HTTPException
from collections import deque
from threading import Lock
from OsmoCaseStudy.models.material import Material
from OsmoCaseStudy.models.fragrance_formula import FragranceFormula
from OsmoCaseStudy.database import FragranceDatabase
from OsmoCaseStudy.queue import FormulaCreatedQueue

from OsmoCaseStudy.utils import publish_with_retry


class FragranceServer: 
    """
    a REST API endpoint that accepts fragrance formula submissions and publishes them to a message queue
    """
    def __init__(self):
        self.app = Flask(__name__)
        self.q = FormulaCreatedQueue()
        self.db = FragranceDatabase()

        self.idempotency_cache = {} # Key: key from header, Value: the correct JSON response
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

            data = request.get_json()
            fragrance_formulas = self.validate_request(data)

            try:
                response = publish_with_retry(fragrance_formulas, self.db, self.q)
            except Exception as e:
                response = e
            
            with self.idempotency_lock:
                self.idempotency_cache[idempotency_key] = response

            return self.parse_response(response)
    
    def parse_response(self, response):
        # Response is either an Exception or None
        # that is to be able to support both results from `publish_with_retry`
        if response is None:
            return jsonify({"message": f"Formula(s) added!"}), 200
        else:
            raise response


    def validate_request(self, data: dict):
        if not data:
            raise BadRequest("Invalid or missing JSON")
        
        if isinstance(data, list):
            return [self.validate_formula(formula) for formula in data]
        elif isinstance(data, dict):
            return self.validate_formula(data)
        
    def validate_formula(self, formula: dict):
        if "name" not in formula:
            raise BadRequest("Missing field 'name' on fragrance formula")
        if "materials" not in formula:
            raise BadRequest("Missing field 'materials' on fragrance formula")
        
        try:
            formula_materials = self.validate_materials(formula["materials"])
            ## Note: List to tuple conversion intentional in order to make formulas hashable 
            fragrance_formula = FragranceFormula(formula["name"], tuple(formula_materials))
            return fragrance_formula
        except TypeError as e:
            ## Type errors are defined in model classes
            raise BadRequest("Invalid type in the request: " + str(e))

    def validate_materials(self, request_materials: list):
        if not isinstance(request_materials, list):
            raise BadRequest("A formula's materials must be a list")
        
        for material in request_materials:
            if "name" not in material:
                raise BadRequest("Missing field 'name' on a material")
            if "concentration" not in material:
                raise BadRequest("Missing field 'concentration' on a material")
        
        formula_materials = [
            Material(
                name=material["name"],
                concentration=material["concentration"]
            )
            for material in request_materials
        ]
        return formula_materials

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