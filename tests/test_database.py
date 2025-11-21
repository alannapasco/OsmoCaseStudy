import pytest
from werkzeug.exceptions import Conflict
from decimal import Decimal

from OsmoCaseStudy.database import FragranceDatabase
from OsmoCaseStudy.models.material import Material
from OsmoCaseStudy.models.fragrance_formula import FragranceFormula

def test_add_formula_success(summer_breeze):
    db = FragranceDatabase()
    db.add_formulas(summer_breeze)

def test_add_formulas_success(summer_breeze, winter_breeze):
    db = FragranceDatabase()
    db.add_formulas([summer_breeze, winter_breeze])

def test_add_formula_failure_identical_dupe_in_memory(summer_breeze):
    db = FragranceDatabase()
    db.add_formulas(summer_breeze)
    with pytest.raises(Conflict) as e_info:
        db.add_formulas(summer_breeze)
    assert "This formula already exists in the database" in str(e_info.value)

def test_add_formula_failure_identical_dupe_values(summer_breeze):
    db = FragranceDatabase()
    db.add_formulas(summer_breeze)

    bo = Material("Bergamot Oil", Decimal('15.5'))
    la = Material("Lavender Absolute", Decimal('10.0'))
    s = Material("Sandalwood", Decimal('5.2'))
    identical = FragranceFormula("Summer Breeze", tuple([bo, la, s]))

    with pytest.raises(Conflict) as e_info:
        db.add_formulas(identical)
    assert "This formula already exists in the database" in str(e_info.value)

def test_add_formulas_failure_different_name_dupe(winter_breeze, winter_breeze_dupe):
    db = FragranceDatabase()
    with pytest.raises(Conflict) as e_info:
        db.add_formulas([winter_breeze, winter_breeze_dupe])
    assert "This formula already exists in the database" in str(e_info.value)

def test_remove_formulas(summer_breeze, winter_breeze):
    db = FragranceDatabase()
    db.add_formulas([summer_breeze, winter_breeze])
    db.remove_formulas([summer_breeze, winter_breeze])
    assert db.is_empty()
