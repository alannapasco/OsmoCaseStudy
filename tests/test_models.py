import pytest
from decimal import Decimal

from OsmoCaseStudy.models.material import Material
from OsmoCaseStudy.models.fragrance_formula import FragranceFormula

def test_material_creation(bergamot_oil):
    assert bergamot_oil.name == "Bergamot Oil"
    assert bergamot_oil.concentration == Decimal('15.5')

def test_fragrance_formula_creation(summer_breeze):
    assert summer_breeze.name == "Summer Breeze"
    assert len(summer_breeze.formula) == 3
    assert summer_breeze.formula[0].name == "Bergamot Oil"
    assert summer_breeze.formula[0].concentration == Decimal('15.5')

