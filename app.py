from flask import Flask, request, jsonify
from collections import deque
from decimal import Decimal
from OsmoCaseStudy.models.material import Material
from OsmoCaseStudy.models.fragrance_formula import FragranceFormula
from werkzeug.exceptions import BadRequest, HTTPException

app = Flask(__name__)

formula_queue = deque()

@app.route("/formulas", methods=["POST"])
def submit_formula():
    data = request.get_json()

    fragrance_formulas = validate_request(data)

    formula_queue.extend(fragrance_formulas)
    return jsonify({"formula:": "formula", "status": "queued"}), 202

def validate_request(data):
    if not data:
        raise BadRequest("Invalid or missing JSON")
    
    if isinstance(data, list):
        return [validate_formula(formula) for formula in data]
    elif isinstance(data, dict):
        return [validate_formula(data)]
    
def validate_formula(formula):
    if "name" not in formula:
        raise BadRequest("Missing field 'name' on fragrance formula")
    if "materials" not in formula:
        raise BadRequest("Missing field 'materials' on fragrance formula")
    
    try:
        formula_materials = validate_materials(formula["materials"])
        fragrance_formula = FragranceFormula(formula["name"], formula_materials)
        return fragrance_formula
    except TypeError as e:
        ## Type errors are defined in model classes
        raise BadRequest("Invalid type in the request: " + str(e))

def validate_materials(request_materials):
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