# OsmoCaseStudy
Welcome to the Fragrand Formula Processor

## Setup 

## Testing

## Duplicate Detection Strategy  

## Design Decisions

## Production Considerations 


##good requests 
curl -X POST http://127.0.0.1:5000/formulas \
-H "Content-Type: application/json" \
-d '{"name": "Summer Breeze", "materials":[{"name":"Bergamot Oil","concentration":15.5},{"name":"Lavender Absolute","concentration":10.0}]}'

curl -X POST http://127.0.0.1:5000/formulas \
  -H "Content-Type: application/json" \
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

## Bad request
curl -X POST http://127.0.0.1:5000/formulas \
-H "Content-Type: application/json" \
-d '{"name": "Summer Breeze", "materials":[{"name":"oktest","concentration":15.5},{"name":"Lavender Absolute","concentration":10.0}]}'

curl -X POST http://127.0.0.1:5000/formulas \
-H "Content-Type: application/json" \
-d '{"name": "Summer Breeze", "materials":[{"name":"Bergamot Oil","concentration":"test"}]}'