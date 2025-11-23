from werkzeug.exceptions import BadRequest
from OsmoCaseStudy.models.material import Material
from OsmoCaseStudy.models.fragrance_formula import FragranceFormula

# A file for validating functions
# Separated out from app.py simply for organization 

def validate_request(request: dict):
    if not request:
        raise BadRequest("Invalid or missing JSON")
    
    if isinstance(request, list):
        return [validate_formula(formula_dict) for formula_dict in request]
    elif isinstance(request, dict):
        return validate_formula(request)
    
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