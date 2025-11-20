from flask import Flask, request, jsonify
from werkzeug.exceptions import BadRequest, HTTPException
from collections import deque
from OsmoCaseStudy.models.material import Material
from OsmoCaseStudy.models.fragrance_formula import FragranceFormula
from OsmoCaseStudy.database import FragranceDatabase
from OsmoCaseStudy.queue import FragranceQueue

app = Flask(__name__)

q = FragranceQueue()
#start_consumer(queue)
db = FragranceDatabase()
queue = deque()

@app.route("/formulas", methods=["POST"])
def submit_formula():
    data = request.get_json()

    fragrance_formulas = validate_request(data)

    ##in a single step 
    # - add formula to db
    # - add to queue
    try:
        db.add_formulas(fragrance_formulas)
        #q.publish_formula_created(fragrance_formulas) ## todo handle multiple
        return jsonify({"message": f"Formula(s) added!"}), 200 ##todo improve message
    except Exception as e:
        db.remove_formulas(fragrance_formulas)
        raise e

def validate_request(data: dict):
    if not data:
        raise BadRequest("Invalid or missing JSON")
    
    if isinstance(data, list):
        return [validate_formula(formula) for formula in data]
    elif isinstance(data, dict):
        return [validate_formula(data)]
    
def validate_formula(formula: dict):
    if "name" not in formula:
        raise BadRequest("Missing field 'name' on fragrance formula")
    if "materials" not in formula:
        raise BadRequest("Missing field 'materials' on fragrance formula")
    
    try:
        formula_materials = validate_materials(formula["materials"])
        ## Note: List to tuple conversion intentional in order to make formulas hashable 
        fragrance_formula = FragranceFormula(formula["name"], tuple(formula_materials))
        return fragrance_formula
    except TypeError as e:
        ## Type errors are defined in model classes
        raise BadRequest("Invalid type in the request: " + str(e))

def validate_materials(request_materials: list):
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

@app.errorhandler(HTTPException)
def handle_http_error(e):
    """
    Neatly handles error output
    """
    response = {
        "error": e.name,
        "message": e.description,
        "status": e.code
    }
    return jsonify(response), e.code

if __name__ == "__main__":
    app.run(debug=True)