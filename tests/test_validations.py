import pytest
from werkzeug.exceptions import BadRequest
from OsmoCaseStudy.app import FragranceServer
from OsmoCaseStudy.models.material import Material
from OsmoCaseStudy.models.fragrance_formula import FragranceFormula

@pytest.fixture
def server():
    return FragranceServer()

@pytest.fixture
def client(server):
    # Flask test client for simulating requests
    # This is the only testclass that will test using client simulator.
    # The rest will test assuming valid input from client.
    with server.app.test_client() as client:
        yield client


###################
# Idempotency Tests
###################
def test_submit_formula_valid(client, summer_breeze):
    payload = summer_breeze.to_dict()

    response = client.post(
        "/formulas",
        json=payload,
        headers={"Idempotency-Key": "test-key-123"}
    )

    assert response.status_code == 200
    assert "message" in response.get_json() 
    assert "Formula(s) added!" in response.get_json()["message"]

def test_submit_formula_idempotent_key_missing(client, summer_breeze):
    payload = summer_breeze.to_dict()

    response = client.post(
        "/formulas",
        json=payload,
    )

    assert response.status_code == 400
    assert "message" in response.get_json()
    assert "Missing Idempotency-Key header" in response.get_json()["message"]    

def test_submit_formula_idempotent_key_success(client, summer_breeze):
    payload = summer_breeze.to_dict()

    response = client.post(
        "/formulas",
        json=payload,
        headers={"Idempotency-Key": "test-key-123"}
    )
    assert response.status_code == 200

    response = client.post(
        "/formulas",
        json=payload,
        headers={"Idempotency-Key": "test-key-123"}
    )
    assert response.status_code == 200 ## same result, no error

def test_submit_formula_valid_duplicate(client, summer_breeze):
    # "valid" duplicate meaning it's not an accidental duplicate submission
    # the user tried to add the same formula in two separate requests
    payload = summer_breeze.to_dict()

    response = client.post(
        "/formulas",
        json=payload,
        headers={"Idempotency-Key": "test-key-123"}
    )
    assert response.status_code == 200

    response = client.post(
        "/formulas",
        json=payload,
        headers={"Idempotency-Key": "test-abc"}
    )
    assert response.status_code == 409 # conflict error - already exists 

    response = client.post(
        "/formulas",
        json=payload,
        headers={"Idempotency-Key": "test-abc"}
    )
    assert response.status_code == 409 # return same, stored results again

##################
# Validation Tests
##################
def test_submit_multiple_formulas_valid(client, summer_breeze, winter_breeze):
    payload = [summer_breeze.to_dict(), winter_breeze.to_dict()]

    response = client.post(
        "/formulas",
        json=payload,
        headers={"Idempotency-Key": "test-key-123"}
    )

    assert response.status_code == 200
    assert "message" in response.get_json()
    assert "Formula(s) added!" in response.get_json()["message"]

#### Invalid Request Object Type Tests

def test_submit_formula_invalid_name(client, jasmine, bergamot_oil):
    payload = {
        "name": 500,
        "materials": [jasmine.to_dict(), bergamot_oil.to_dict()]
    }

    response = client.post(
        "/formulas",
        json=payload,
        headers={"Idempotency-Key": "test-key-123"}
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Bad Request"
    assert "Formula name must be a string" in response.get_json()["message"]

def test_submit_formula_invalid_materials(client):
    payload = {
        "name": "Winter Bloom",
        "materials": "not a list of materials"
    }

    response = client.post(
        "/formulas",
        json=payload,
        headers={"Idempotency-Key": "test-key-123"}
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Bad Request"
    assert "A formula's materials must be a list" in response.get_json()["message"]

def test_submit_formula_invalid_material_name(client):
    payload = {
        "name": "Summer Breeze", 
        "materials":[{"name":500,"concentration":"test"}]
    }

    response = client.post(
        "/formulas",
        json=payload,
        headers={"Idempotency-Key": "test-key-123"}
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Bad Request"
    assert "Material name must be a string" in response.get_json()["message"]

def test_submit_formula_invalid_material_concentration(client):
    payload = {
        "name": "Summer Breeze", 
        "materials":[{"name":"Bergamot Oil","concentration":"test"}]
    }

    response = client.post(
        "/formulas",
        json=payload,
        headers={"Idempotency-Key": "test-key-123"}
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Bad Request"
    assert "Material concentration must be a decimal" in response.get_json()["message"]

def test_omit_info_formula(client, jasmine, bergamot_oil):
    payload = {
        "materials": [jasmine.to_dict(), bergamot_oil.to_dict()]
    }

    response = client.post(
        "/formulas",
        json=payload,
        headers={"Idempotency-Key": "test-key-123"}
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Bad Request"
    assert "Missing field 'name' on fragrance formula" in response.get_json()["message"]

    payload = {
        "name": "Summer Breeze"
    }

    response = client.post(
        "/formulas",
        json=payload,
        headers={"Idempotency-Key": "test-key-123"}
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Bad Request"
    assert "Missing field 'materials' on fragrance formula" in response.get_json()["message"]

def test_omit_info_materials(client, jasmine, bergamot_oil):
    payload = {
        "name": "Summer Breeze", 
        "materials":[{"concentration":14.0}]
    }

    response = client.post(
        "/formulas",
        json=payload,
        headers={"Idempotency-Key": "test-key-123"}
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Bad Request"
    assert "Missing field 'name' on a material" in response.get_json()["message"]

    payload = {
        "name": "Summer Breeze", 
        "materials":[{"name":"Bergamot Oil"}]
    }

    response = client.post(
        "/formulas",
        json=payload,
        headers={"Idempotency-Key": "test-key-123"}
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Bad Request"
    assert "Missing field 'concentration' on a material" in response.get_json()["message"]



   