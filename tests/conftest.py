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
def sandalwood():
    return Material("Sandalwood", Decimal('5.2'))

@pytest.fixture(scope="module")
def amber():
    return Material("Amber", Decimal('14.3'))

@pytest.fixture(scope="module")
def jasmine():
    return Material("Jasmine", Decimal('50.3'))

# Fixtures for example Fragrance Formulas
@pytest.fixture(scope="module")
def summer_breeze(bergamot_oil, lavender_absolute, sandalwood):
    return FragranceFormula("Summer Breeze", [bergamot_oil, lavender_absolute, sandalwood])

@pytest.fixture(scope="module")
def winter_breeze(bergamot_oil, amber, jasmine):
    return FragranceFormula("Summer Breeze", [bergamot_oil, amber, jasmine])
