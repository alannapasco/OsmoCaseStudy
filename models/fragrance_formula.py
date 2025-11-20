
from .material import Material
from typing import List

class FragranceFormula:
    def __init__(self, name:str, formula:List[Material]):
        """
        Initializes a Fragrance Formula object with a name (string) and a formula (list<Materials>).
        """

        if not isinstance(name, str):
            raise TypeError("Name must be a string.")
        if not isinstance(formula, list): ##TODO: this only checks that formula is a list, not that it's a list OF Material
            raise TypeError("Formula must be a list of Material.")

        self.name = name
        self.formula = formula

        def __str__(self):
            return f"FragranceFormula(name={self.name!r}, formula={self.formula})"