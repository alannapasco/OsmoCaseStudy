# OsmoCaseStudy
Welcome to the Fragrance Formula Processor

```
Code Review Agenda
|
|-- Data Definitions / Model / Schema
|
|-- Input Validation
|
|-- API Entry-point: submit_formula
|    |
|    |-- function: publish_with_retry
|        |
|        |-- database
|        |     |
|        |     |-- function: add_formula
|        |     |
|        |     |-- function: is_duplicate
|        |
|        |-- queue
|        |     |
|        |     |-- function: publish
|        |     |
|        |     |-- function: get_next_item
|        |     |
|        |     |-- function: ack
|        |
|        |-- rollback strategy (atomicity) - remove from db,queue
|        |
|    |-- idempotency handling
```

## Setup
Python Version: 3.11.7

1. Clone the Repo
```
git clone https://github.com/<your-username>/osmo-case-study.git
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
- `test_database.py` -> tests duplicate detection

The atomicity unit tests test successful and unsuccessful retries by mocking errors at different points of program flow and checking that the add/remove methods on the db and queue have been called the correct number of times. E.g if there is a failure on the first try and then success on the second, the rollback strategy section should only be called once. Then, the `test_queue.py`, specifically, the tests for `remove()`, tests that clean up took place in the event of an error. 

Tests for idempotency are found in both the `test_validations` and `test_database.py` classes. 
In `test_validations`:
- `test_submit_formula_idempotent_key_success`: tests that 2 consecutive requests with the same idempotency key and formulas both return 200 success, and do NOT raise a `Conflict` error for the second duplicate request.
- `test_submit_formula_valid_duplicate`: tests that 2 consecutive requests with different idempotency keys but the same formulas do correctly return a `Conflict` error on the second request. 


### Calling the API locally
See Appendix below for sample valid and invalid requests.


## Duplicate Detection Strategy  

I feel there are two interpretations of 'duplicate request':
1. Two consecutive requests where the second one is sent accidentally (idempotency) - e.g. user clicks "submit" button twice really quickly but by accident. 
    - Result: user should NOT see a "formula already exists" error
2. Two consecutive requests where the second one is sent on purpose, but contains a formula that's already been added to the system. (equality checking/hashing).
    - Result: user SHOULD see a "formula already exists" error

To solve the first: I learned late in the project that Flask's `POST` requests are the only non-idempotent requests within Flask, and therefore I needed to manually implament handling an idempotent key and further behavior. To solve idempotency I require an idempotency key to be passed in request headers, build a cache of said keys, and in subsequent calls check that the key is NOT present in the cache before processing the request. If it is, do not perform the process -- just return the same result as the first request, which is found in the cache. 

To solve the second: Formula uniqueness is defined by its material make-up, not by its name. That means formulas with the same name but different formulas are permitted, and we cannot use formula `name` as its unique identifier. Initially I implemented the `materials` field on `FragranceFormula` as a list of `Material`. However, `list` in Python is not hashable, and I needed a way to extract a unique identifier from a list of materials where two separate lists of the same materials would return the same unique identifier. I converted the list of `Material` to a tuple of `Material` because tuples *are* hashable in Python. Finally, my database stores the hashed materials as Key and the full `FragranceFormula` object as Value. This achieves two things:
1. Two formulas with the same name but different formulas can both exist in the database and be treated as unique.
2. Two formulas with different names (or same names) but the **same formula** are not allowed -- the second submission will face a Conflict error. 

## Design Decisions
**Atomicity and Rollback Strategy** 
In the event of a network drop or other error anywhere in the process of adding a formula, we must clean up every single container that holds information for this process. The rollback strategy includes retries with exponential backoff so that it waits slightly longer with each retry. That is because as we go through more retries, it becomes more clear that the issue may be more serious/need more time. The rollback strategy steps are:
    - remove formula from storage/db
    - remove formula queue + downstream all three containers used within the queue to track info
    - define # of retries (default 3) 
    - exponential backoff: define delay that grows with every retry (base delay is 1 second)
    - retry all steps from the beginning for the number of retries until a sure failure is detected - then fail 

**Error during rollback?** - What happens if you:
  1. Add item to db 
  2. Error arises
  3. Start rollback
  4. Another error (network drop) interrupts the rollback and data is not cleaned up?
  
  ...I believe the rollback strategy in prod should consider this and perhaps implement what I believe is a dead letter queue, or basically a queue to track things to clean up by an additional async process, when network has resumed. 

**Queue Design**
Trade offs:
1. **Python Queue vs Deque** - Originally I chose to represent the queue as a Python Queue but realized quickly that a Deque was more versatile. Example: `in get_next_item()` I chose to re-prioritize queue items that have been waiting beyond 30 seconds. That's only possible because Deques allow you to append to "left" aka add to the front/top priority of the queue, whereas Queue is more simple and only performs FIFO. 
2. **remove_event_from_queue_by_id() function efficienty** - deque's .remove() functions at O(n) time, but since we only have `id` at the time of removal we need to search our queue at O(n) for the event with that id, and *then* call .reomove() on it, which then also functions at O(n). Overall it could be made more efficient, but since removal is not called during successful requests, I did not spend more time trying to make it more efficient. I would list it as a fast-follow in a real world scenario.
- 

### Further design decisions not specifically requested but took note of: 
1. **Float vs Decimal to represent `Concentration`**: Performing arithmatic on floating-point numbers is known to create unexpected results. There may come a time that this API will support modifying existing formulas by adding/subtracting to/from an element's concentration. E.g. "Add 0.1 to Jasmine". In the real world, I would ask a chemist/scientist how to handle this -- because truly I don't know if it makes sense to add/subtract from a concentration within a formula. But I chose the more precise representation. Float is better for representing numbers that are expected to be approximate, but we want precision. 
2. **OOP vs Functional Programming**: As a Java developer I'm more comfortable with OOP, so you may notice this code base is structured a lot like a Java project, just in Python. 
3. **Flask vs Django vs FastAPI**: While chosing a framework, my priorities were:
    - low learning curve (first Python API for me)
    - high documentation/adtoption for online searching errors
FastAPI and Django seemed like good choices because of how extensive their built-in features are, BUT for the purpose of this assignment I wanted to maintain manual control over things like serialization and validation, not offload that to a framework. FastAPI even has a feature that writes its own documentation - but I'm a skeptic and wouldn't trust a tool to do that. So I chose Flask in order to maintain control over the implementation. *However* in the real world I would likely select Django for its templates and ease of use with visual UIs. 
4. **API accepts a list out of the box**: *THIS MAY HAVE BUGS* This was something I learned at AWS -> always think far into the future. While the assignment implied to accept one formula at a time, I implemented the API to accept either a list of formulas or a single formula so that as we hypothetically expand in the future to accept large-scale formula submissions we do not risk breaking backward compatibility. NOTE: This implementation is not savy because it was not a requirement of the case story - if the API encounters one dupe in the list then it stops and does not continue processing the rest. 
5. **Database design**: I approached the assignment by persisting formulas in a database-like structure wrapped around a Python dictionary and handling duplicates in that class. I later realized I could have handled duplicates directly in the queue class and did not need the database. However, in the real world we will have separate databases and queues, so I kept this implementation as-is, even if overkill for this assignment. 
The wrapper class enables the following:
    - enables adding many formulas at once
    - handles calling `hash()` on the formulas before storing them
    - gracefully handles attempts to remove items that don't exist
    - gracefully handles attempting to add duplicate items, or formulas that already exist (even with a different name) 


## Production Considerations 
1. **In-memory Queue vs Cloud Queue** - The assignment states to implement in-memory queue. For prod, we would use a much more scalable, flexible queue like Amazon SQS. This would ensure queue data is distributed across machines to be durable for customers.
2. **Frameworks** - For a more scalable project, I would use Django over Flask in prod. Django comes with much more automation, templates, built-in auth, and in general is heavier but better for scalability. 
3. **Error Messages** - as a project scales, it's best practice to store error message text in a separate file and reference the messages. That way there is a single point of control for defining verbiage that might need to be used in multiple places, e.g. where the error is thrown and in its unit test. 



## Appendix 

### Valid Requests
```
curl -X POST http://127.0.0.1:5000/formulas \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: 123e7-45345-4" \
  -d '{"name": "Summer Breeze", "materials":[{"name":"Bergamot Oil","concentration":15.5},{"name":"Lavender Absolute","concentration":10.0}]}'

curl -X POST http://127.0.0.1:5000/formulas \
-H "Content-Type: application/json" \
-H "Idempotency-Key: 1234567890" \
-d '{"name": "Winter Breeze", "materials":[{"name":"Bergamot Oil","concentration":15.5},{"name":"Sandalwood","concentration":5.0}]}'
```


### Invalid Requests
Missing idempotency key
```
curl -X POST http://127.0.0.1:5000/formulas \
  -H "Content-Type: application/json" \
  -d '{"name": "Summer Breeze", "materials":[{"name":"Bergamot Oil","concentration":15.5},{"name":"Lavender Absolute","concentration":10.0}]}'
```

The following two requests send consecutively will return a Conflict error (duplicate add to the database)
```
curl -X POST http://127.0.0.1:5000/formulas \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: 123e7-45345-4" \
  -d '{"name": "Summer Breeze", "materials":[{"name":"Bergamot Oil","concentration":15.5},{"name":"Lavender Absolute","concentration":10.0}]}'

curl -X POST http://127.0.0.1:5000/formulas \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: abcdefg-abc" \
  -d '{"name": "Summer Breeze", "materials":[{"name":"Bergamot Oil","concentration":15.5},{"name":"Lavender Absolute","concentration":10.0}]}'
```

  