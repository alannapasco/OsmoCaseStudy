from werkzeug.exceptions import Conflict
from OsmoCaseStudy.models.material import Material
from OsmoCaseStudy.models.fragrance_formula import FragranceFormula

class FragranceDatabase:
    def __init__(self):
        """
        Initializes a database for storing Fragrance Formula objects, 
        where formulas are unique. Formula uniqueness is defined by its material make-up.
        Formulas with the same name but different formulas are permitted.
        """
        self._db = {}

    def add_formulas(self, formulas):
        if isinstance(formulas, list):
            for formula in formulas:
                self.add_formula(formula)
        elif isinstance(formulas, FragranceFormula):
            self.add_formula(formulas)

    def add_formula(self, formula: FragranceFormula):
        id = hash(formula)

        if self.is_duplicate(id):
            raise Conflict(f"This formula already exists in the database: {formula.materials}")
        
        self._db[id] = formula
    
    def remove_formulas(self, formulas):
        if isinstance(formulas, list):
            for formula in formulas:
                self.remove_formula(formula)
        elif isinstance(formulas, FragranceFormula):
            self.remove_formula(formulas)

    def remove_formula(self, formula: FragranceFormula):
        id = hash(formula)
        # instead of a KeyError, in the event an ID is not found return None
        self._db.pop(id, None)

    def is_duplicate(self, id):
        return id in self._db


