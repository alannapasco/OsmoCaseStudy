from decimal import Decimal

class Material:
    def __init__(self, name: str, concentration: Decimal):
        """
        Initializes a Material object with a name (string) and a concentration (Decimal).
        """

        if not isinstance(name, str):
            raise TypeError("Name must be a string.")
        if not isinstance(concentration, Decimal):
            raise TypeError("Concentration must be a decimal.")

        self.name = name
        self.concentration = concentration

        def __str__(self):
            return f"Material(name={self.name!r}, concentration={self.concentration})"

    
        