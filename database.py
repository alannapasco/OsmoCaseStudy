from werkzeug.exceptions import Conflict
import pprint
from OsmoCaseStudy.models.fragrance_formula import FragranceFormula

class FragranceDatabase:
    def __init__(self):
        """
        Initializes a database for storing Fragrance Formula objects, 
        where formulas are unique. Formula uniqueness is defined by its material make-up.
        Formulas with the same name but different formulas are permitted.
        """
        self._db = {} ## Key: id (hashed formula), Value: the formula

    def add_formulas(self, formulas):
        if isinstance(formulas, list):
            for formula in formulas:
                self.add_formula(formula)
        elif isinstance(formulas, FragranceFormula):
            self.add_formula(formulas)

    def add_formula(self, formula: FragranceFormula):
        id = hash(formula)

        if self.is_duplicate(id):
            raise Conflict(f"This formula already exists in the database, either by the same name or another name: {formula}")
        
        self._db[id] = formula
        return id
    
    def remove_formulas(self, formulas):
        if isinstance(formulas, list):
            for formula in formulas:
                self.remove_formula(formula)
        elif isinstance(formulas, FragranceFormula):
            self.remove_formula(formulas) 

    def remove_formula(self, formula: FragranceFormula):
        id = hash(formula)
        # Gracefully handle when an ID isn't present
        # instead of a KeyError, just return None
        self._db.pop(id, None)

    def is_duplicate(self, id):
        return id in self._db
    
    def is_empty(self):
        return len(self._db) == 0
    
    def size(self):
        return len(self._db)
    
    def __str__(self):
        pprint(self._db)


