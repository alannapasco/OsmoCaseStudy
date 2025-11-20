import pytest
from decimal import Decimal

from OsmoCaseStudy.models.material import Material
from OsmoCaseStudy.models.fragrance_formula import FragranceFormula

# Fixtures for example Materials
@pytest.fixture(scope="module")
def bergamot_oil():
    return Material("Bergamot Oil", Decimal('15.5'))

@pytest.fixture(scope="module")
def lavender_absolute():
    return Material("Lavender Absolute", Decimal('10.0'))

@pytest.fixture(scope="module")
def Sandalwood():
    return Material("Sandalwood", Decimal('5.2'))

# Fixtures for example Fragrance Formulas
@pytest.fixture
def summer_breeze(bergamot_oil, lavender_absolute, Sandalwood):
    return FragranceFormula("Summer Breeze", [bergamot_oil, lavender_absolute, Sandalwood])
