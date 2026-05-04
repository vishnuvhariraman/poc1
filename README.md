# FastAPI Sanctions Screening POC

## Start services
```bash
docker compose up --build -d
```

## Load sample sanctions data into OpenSearch
```bash
docker compose exec screening-api python scripts/load_sample_sanctions.py
```

The loader is repeatable and recreates `sanctions-master-v1` with **10** records each time.

## Verify loaded count is 10
```bash
curl -s http://localhost:9200/sanctions-master-v1/_count
```

Expected response includes:
```json
{"count":10,...}
```

## Multi-hit PERSON test (Raj Kumar Dev)
```bash
curl -s -X POST http://localhost:8000/api/v1/screenings \
  -H 'Content-Type: application/json' \
  -d '{
  "request_id": "req-multi-person-001",
  "source_system": "crm",
  "entity_type": "PERSON",
  "name": {"full_name": "Raj Kumar Dev"},
  "dob": "1978-04-12",
  "identifiers": [],
  "addresses": [],
  "screening_lists": ["OFAC_SDN", "UN_CONSOLIDATED", "EU_CONSOLIDATED"]
}'
```

Expected: `POTENTIAL_HIT` with at least 3 matches.

## Multi-hit ORGANIZATION test (Global Falcon Trading LLC)
```bash
curl -s -X POST http://localhost:8000/api/v1/screenings \
  -H 'Content-Type: application/json' \
  -d '{
  "request_id": "req-multi-org-001",
  "source_system": "crm",
  "entity_type": "ORGANIZATION",
  "name": {"full_name": "Global Falcon Trading LLC"},
  "identifiers": [],
  "addresses": [],
  "screening_lists": ["OFAC_SDN", "UN_CONSOLIDATED", "EU_CONSOLIDATED"]
}'
```

Expected: `POTENTIAL_HIT` with at least 3 matches.

## Call screening API (baseline POTENTIAL_HIT)
```bash
curl -s -X POST http://localhost:8000/api/v1/screenings \
  -H 'Content-Type: application/json' \
  -d '{
  "request_id": "req-001",
  "source_system": "crm",
  "entity_type": "PERSON",
  "name": {"full_name": "John Adam Doe", "first_name": "John", "last_name": "Doe"},
  "dob": "1980-01-15",
  "identifiers": [{"type": "SSN", "value": "SYNTH-SSN-0001"}],
  "addresses": [{"line1": "1 Main St", "city": "Austin", "state": "TX", "postal_code": "73301", "country": "US"}],
  "screening_lists": ["OFAC_SDN", "UN_CONSOLIDATED", "EU_CONSOLIDATED"]
}'
```

## Call screening API (NO_HIT)
```bash
curl -s -X POST http://localhost:8000/api/v1/screenings \
  -H 'Content-Type: application/json' \
  -d '{
  "request_id": "req-002",
  "source_system": "crm",
  "entity_type": "ORGANIZATION",
  "name": {"full_name": "Sunrise Bakery Inc"},
  "identifiers": [{"type": "TAX_ID", "value": "SYNTH-TAX-9999"}],
  "addresses": [{"line1": "22 Lake St", "city": "Denver", "state": "CO", "postal_code": "80014", "country": "US"}],
  "screening_lists": ["OFAC_SDN", "UN_CONSOLIDATED", "EU_CONSOLIDATED"]
}'
```

## View cases in PostgreSQL
```bash
docker compose exec postgres psql -U screening -d screening_db -c "select * from cases order by id desc;"
```

## Run tests
```bash
pytest -q
```
