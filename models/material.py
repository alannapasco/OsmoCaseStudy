from decimal import Decimal, InvalidOperation

class Material:
    def __init__(self, name: str, concentration: Decimal):
        """
        Initializes a Material object with a name (string) and a concentration (Decimal).
        """

        if not isinstance(name, str):
            raise TypeError("Material name must be a string")
        self.name = name
        
        if not isinstance(concentration, Decimal):
            try:
                self.concentration = Decimal(str(concentration))
            except Exception: 
                raise TypeError("Material concentration must be a decimal")
        else:
            self.concentration = concentration
    
    def __eq__(self, other):
        if not isinstance(other, Material):
            return NotImplemented
        ## compare value, not identity in memory
        return (self.name, self.concentration) == (other.name, other.concentration)

    def __hash__(self):
        return hash((self.name, self.concentration))
    
    def to_dict(self):
        return {
            "name": self.name,
            "concentration": float(self.concentration)
        }
    
    def __str__(self):
        return f"Material(name={self.name!r}, concentration={self.concentration})"

    
        