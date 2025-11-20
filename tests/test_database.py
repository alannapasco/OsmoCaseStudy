import pytest
from OsmoCaseStudy.models.material import Material
from OsmoCaseStudy.models.fragrance_formula import FragranceFormula
from OsmoCaseStudy.database import FragranceDatabase

def test_add_formula_success(summer_breeze):
    db = FragranceDatabase()
    db.add_formulas(summer_breeze)

def test_add_formulas_success(summer_breeze, winter_breeze):
    db = FragranceDatabase()
    db.add_formulas([summer_breeze, winter_breeze])

def test_add_formula_failure_identical_dupes(summer_breeze):
    db = FragranceDatabase()
    db.add_formulas(summer_breeze)
    with pytest.raises(Exception) as e_info:
        db.add_formulas(summer_breeze)
    assert "This formula already exists in the database" in str(e_info.value)

def test_add_formulas_failure_different_name_dupe(winter_breeze, winter_breeze_dupe):
    db = FragranceDatabase()
    with pytest.raises(Exception) as e_info:
        db.add_formulas([winter_breeze, winter_breeze_dupe])
    assert "This formula already exists in the database" in str(e_info.value)

def test_remove_formulas(summer_breeze, winter_breeze):
    db = FragranceDatabase()
    db.add_formulas([summer_breeze, winter_breeze])
    db.remove_formulas([summer_breeze, winter_breeze])
