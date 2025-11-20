import pytest
from decimal import Decimal

from OsmoCaseStudy.models.material import Material
from OsmoCaseStudy.models.fragrance_formula import FragranceFormula

def test_material_creation(bergamot_oil):
    assert bergamot_oil.name == "Bergamot Oil"
    assert bergamot_oil.concentration == Decimal('15.5')

def test_fragrance_formula_creation(summer_breeze):
    assert summer_breeze.name == "Summer Breeze"
    assert len(summer_breeze.materials) == 3
    assert summer_breeze.materials[0].name == "Bergamot Oil"
    assert summer_breeze.materials[0].concentration == Decimal('15.5')

def test_fragrance_forumla_hashing(summer_breeze, winter_breeze, winter_breeze_dupe):
    assert hash(summer_breeze) != hash(winter_breeze)
    assert hash(winter_breeze_dupe) == hash(winter_breeze) == hash(winter_breeze_dupe)

