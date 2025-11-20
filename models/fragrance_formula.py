
from .material import Material
from typing import List

class FragranceFormula:
    def __init__(self, name:str, materials:List[Material]):
        """
        Initializes a Fragrance Formula object with a name (string) and a formula (list[Material]).
        """

        if not isinstance(name, str):
            raise TypeError("Formula name must be a string")
        if not isinstance(materials, list): #Note: this only checks that formula is a list, not that it's a list of Material specifically. That is handled by validators during request validation. 
            raise TypeError("Formula must contain a list of materials")

        self.name = name
        self.materials = materials

    def to_dict(self):
        return {
            "name": self.name,
            "materials": [materials.to_dict() for materials in self.materials]
        }


    def __str__(self):
        return f"FragranceFormula(name={self.name!r}, formula={self.materials})"