# FastAPI Sanctions Screening POC + Case Review UI

## Start full stack
```bash
docker compose up --build -d
```

## Load sample sanctions data (always loads 10)
```bash
docker compose exec screening-api sh -c "PYTHONPATH=/app python scripts/load_sample_sanctions.py"
```

## Verify OpenSearch count
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
curl.exe http://localhost:9200/sanctions-master-v1/_count
```
Expected: `count = 10`.

## Create PERSON multi-hit case (Raj Kumar Dev)
```bash
curl -s -X POST http://localhost:8000/api/v1/screenings -H 'Content-Type: application/json' -d '{"request_id":"req-multi-person","source_system":"crm","entity_type":"PERSON","name":{"full_name":"Raj Kumar Dev"},"dob":"1978-04-12","identifiers":[],"addresses":[],"screening_lists":["OFAC_SDN","UN_CONSOLIDATED","EU_CONSOLIDATED"]}'
```

## Create ORGANIZATION multi-hit case (Global Falcon Trading LLC)
```bash
curl -s -X POST http://localhost:8000/api/v1/screenings -H 'Content-Type: application/json' -d '{"request_id":"req-multi-org","source_system":"crm","entity_type":"ORGANIZATION","name":{"full_name":"Global Falcon Trading LLC"},"identifiers":[],"addresses":[],"screening_lists":["OFAC_SDN","UN_CONSOLIDATED","EU_CONSOLIDATED"]}'
```

## Open UI
- http://localhost:5173

## Review multi-hit case
1. Open Case Queue.
2. Click **View Details** on a case with `3 Matches` badge.
3. Compare screened entity vs all matched sanctions cards.

## Close as false positive
- In case detail, use **Close as False Positive** with optional comment and actor.

## Escalate to Level 2
- In case detail, use **Escalate to Level 2**.

## Run tests
```bash
PYTHONPATH=. pytest -q
```
