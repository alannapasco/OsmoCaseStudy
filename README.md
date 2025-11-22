# OsmoCaseStudy
Welcome to the Fragrance Formula Processor

## Setup
Python Version: 3.11.7

1. Clone the Repo
```
git clone https://github.com/your-username/osmo-case-study.git
cd OsmoCaseStudy
```

2. Create and activate a virtual environment
```
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies, set environment variables
```
pip install --upgrade pip
pip install -r requirements.txt
export FLASK_APP=OsmoCaseStudy.app:create_app
export FLASK_ENV=development
```

4. Use Flask to run 
```
flask run
```

Now, open a second terminal and test sending requests:
```
curl -X POST http://127.0.0.1:5000/formulas \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: 123e7-45345-4" \
  -d '{"name": "Summer Breeze", "materials":[{"name":"Bergamot Oil","concentration":15.5},{"name":"Lavender Absolute","concentration":10.0}]}'
```

See Appendix for more example requests to copy/paste.


## Testing

### Unit Testing
Test Framework: Pytest & unittest

To run tests: 
From within `/OsmoCaseStudy` run `pytest`

There are a few significant test classes:
- `test_atomicity.py` -> `test_queue.py`
- `test_validations` -> first 4 tests test idempotency 
- `test_database.py` (tests duplicate detection)

The atomicity unit tests tests successful and unsuccessful retries by mocking the queue and db and ensuring that each call to the respective element was called the correct expected number of times. E.g if there is a failure on the first try and then success on the second, the rollback strategy section should only be called once. Then, the `test_queue.py` tests that clean up took place in the event of an error. Specifically, the tests for `remove()`. 

Tests for idempotency are found in both the `test_validations` and `test_database.py` classes. 
- `test_submit_formula_idempotent_key_success`: tests that 2 consecutive requests with the same idempotency key and formulas both return 200 success, and do NOT raise a `Conflict` error for the second duplicate request.
- `test_submit_formula_valid_duplicate`: tests that 2 consecutive requests with different idempotency keys but the same formulas do correctly return a `Conflict` error on the second request. 


### Calling the API locally
See Appendix below for sample valid and invalid requests.


## Duplicate Detection Strategy  

I feel there are two interpretations of 'duplicate request':
1. Two consecutive requests where the second one is sent accidentally (idempotency) - e.g. user clicks "submit" button twice really quickly but by accident. 
    - Result: user should NOT see a "formula already exists" error
2. Two consecutive requests where the second one is sent on purpose, but contains a formula that's already been added to the system. (equality checking/hashing)
    - Result: user SHOULD see a "formula already exists" error

To solve the first: I learned too late in the project that Flask's `POST` requests are the only non-idempotent requests within Flask, and therefore I needed to manually implament handling an idempotent key and further behavior. To solve idempotency I require an idempotency key to be passed in request headers, build a cache of said keys, and in subsequent calls check that the key is NOT present in the cache before processing the request. If it is, do not perform the process -- just return the same result as the first request.

To solve the second: Formula uniqueness is defined by its material make-up, not by its name. That means formulas with the same name but different formulas are permitted, and we cannot use formula `name` as its unique identifier. Initially I implemented the `materials` field on `FragranceFormula` as a list of `Material`. However, `list` in Python is not hashable, and I needed a way to extract a unique identifier from a list of materials where two separate lists of the same materials would return the same unique identifier. I converted the list of `Material` to a tuple of `Material` because tuples *are* hashable in Python. Finally, my database stores the hashed materials as Key and the full `FragranceFormula` object as Value. This achieves two things:
1. Two formulas with the same name but different formulas can both exist in the database and be treated as unique.
2. Two formulas with different names (or same names) but the **same formula** are not allowed -- the second submission will face a Conflict error. 

## Design Decisions
1. **Float vs Decimal to represent `Concentration`**: Performing arithmatic on floating-point numbers is known to create unexpected results. There may come a time that this API will support modifying existing formulas by adding/subtracting to/from an element's concentration. E.g. "Add 0.1 to Jasmine". In the real world, I would ask a chemist/scientist how to handle this -- because truly I don't know if it makes sense to add/subtract from a concentration within a formula. But I chose the more precise representation. Float is better for representing numbers that are expected to be approximate, but we want precision. 
2. **OOP vs Functional Programming**: As a Java developer I'm more comfortable with OOP, so you may notice this code base is structured a lot like a Java project, just in Python. 
3. **Flask vs Django vs FastAPI**: While chosing a framework, my priorities were:
    - low learning curve (first Python API for me)
    - high documentation/adtoption for online searching errors
FastAPI and Django seemed like good choices because of how extensive their built-in features are, BUT for the purpose of this assignment I wanted to maintain manual control over things like serialization and validation, not offload that to a framework. FastAPI even has a feature that writes its own documentation - but I'm a skeptic and wouldn't trust a tool to do that. So I chose Flask in order to maintain control over the implementation. *However* in the real world I would likely select Django for its templates and ease of use with visual UIs. 
4. **API accepts a list out of the box**: This was something I learned at AWS -> always think far into the future. While the assignment implied to accept one formula at a time, I implemented the API to accept either a list of formulas or a single formula so that as we hypothetically expand in the future to accept large-scale formula submissions we do not risk breaking backward compatibility. NOTE: This implementation is not savy because it was not a requirement of the case story - if the API encounters one dupe in the list then it stops and does not continue processing the rest. 
5. **Database design**: Originally I approached the assignment by persisting formulas in a database-like structure wrapped around a Python dictionary and enforcing idempotency in that class. I later realized I could have handled idempotency directly in the queue class and did not need the database. However, in the real world we will have separate databases and queues, so I kept this implementation as-is, even if overkill for this assignment. 
The wrapper class enables the following:
    - enables adding many formulas at once
    - handles calling `hash()` on the formulas before storing them
    - gracefully handles removing items that don't exist
    - gracefully handles attempting to add duplicate items, or formulas that already exist (even with a different name_)
6. **Idempotency**: 
    1. The message queue mostly relies on the database to ensure idempotency. This should be de-coupled in the real world. But for now, I wanted to distinctly handle idempotency separately from the message queue just as an organizational preference. All duplicate detection logic is in the db class and performed before storing an item, and also before enqueing an item. 
    2. If a client accidentally submits a request twice (e.g. customer clicks "submit" twice very quickly) then the first time the request will go through correctly, then the second time the request will raise a Conflict error. 
7. **Rollback Strategy**: In the event of a network drop or other error anywhere in the process of adding a formula, we must clean up every single container that holds information for this process. The rollback strategy includes retries with exponential backoff so that it waits slightly longer with each retry. That is because as we go through more retries, it becomes more clear that the issue may be more serious/need more time. The rollback strategy steps are:
  - remove formula from storage/db
  - remove formula queue + downstream all three containers used within the queue to track info
  - define # of retries (default 3) 
  - exponential backoff: define delay that grows with every retry (base delay is 1 second)
  - retry all steps from the beginning the number of retries until a sure failure is detected - then fail 




## Production Considerations 
1. **In-memory Queue vs Cloud Queue** - The assignment states to implement in-memory queue. For prod, we would use a much more scalable, flexible queue like SQS. This would ensure queue data is distributed across machines to be durable for customers.
2. **Frameworks** - For a more scalable project, I would use Django over Flask in prod. Django comes with much more automation, templates, built-in auth, etc. 
3. **Error Messages** - as a project scales, it's best practice to store error message text in a separate file and reference the messages. That way there is a single point of control for defining verbiage that might need to be used in multiple places, e.g. where the error is thrown and in its unit test. 
4. **Error during rollback?** - What happens if you:
    1. Add item to db 
    2. Error arises
    3. Start rollback
    4. Another error (network drop) interrupts the rollback and data is not cleaned up?
  
  ...I believe the rollback strategy in prod should consider this and perhaps implement what I believe is a dead letter queue, or basically a queue to track things to clean up by an additional async process, when network has resumed. 


## Appendix 

### Valid Requests 
curl -X POST http://127.0.0.1:5000/formulas \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: 123e7-45345-4" \
  -d '{"name": "Summer Breeze", "materials":[{"name":"Bergamot Oil","concentration":15.5},{"name":"Lavender Absolute","concentration":10.0}]}'

curl -X POST http://127.0.0.1:5000/formulas \
-H "Content-Type: application/json" \
-H "Idempotency-Key: 1234567890" \
-d '{"name": "Winter Breeze", "materials":[{"name":"Bergamot Oil","concentration":15.5},{"name":"Sandalwood","concentration":5.0}]}'

curl -X POST http://127.0.0.1:5000/formulas \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: 123e4567-e89b-12d3-a456-426614174000" \
  -d '[  
        {
          "name": "Summer Breeze",
          "materials": [
            {"name":"Bergamot Oil","concentration":15.5},
            {"name":"Lavender Absolute","concentration":10.0}
          ]
        },
        {
          "name": "Winter Breeze",
          "materials": [
            {"name":"Bergamot Oil","concentration":15.5},
            {"name":"Sandalwood","concentration":5.0}
          ]
        }
      ]'


### Invalid Requests
Missing idempotency key
curl -X POST http://127.0.0.1:5000/formulas \
  -H "Content-Type: application/json" \
  -d '{"name": "Summer Breeze", "materials":[{"name":"Bergamot Oil","concentration":15.5},{"name":"Lavender Absolute","concentration":10.0}]}'
