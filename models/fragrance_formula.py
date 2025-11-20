
from .material import Material

class FragranceFormula:
    def __init__(self, name:str, materials:tuple[Material]):
        """
        Initializes a Fragrance Formula object with a name (string) and a formula (tuple[Material]).
        """

        if not isinstance(name, str):
            raise TypeError("Formula name must be a string")
        if not isinstance(materials, tuple): #Note: this only checks that formula is a tuple, not that it's a tuple of Material specifically. That is handled by validators during request validation. 
            raise TypeError("Formula must contain a tuple of materials")

        self.name = name
        self.materials = materials

    def __hash__(self):
        # Note: create hash based on formula only, not name, because python's string hash
        # may have different results across different runs, and we will use this hash as 
        # a unique identifier and need to get the same hash code in future runs to query the db
        return hash((self.materials))
    
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.materials == other.materials

    def to_dict(self):
        return {
            "name": self.name,
            "materials": [materials.to_dict() for materials in self.materials]
        }

    def __str__(self):
        return f"FragranceFormula(name={self.name!r}, formula={self.materials})"
    