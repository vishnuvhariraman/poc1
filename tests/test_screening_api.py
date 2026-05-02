from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    res = client.get('/health')
    assert res.status_code == 200


def test_no_hit(monkeypatch):
    monkeypatch.setattr('app.main.search_candidates', lambda *args, **kwargs: [])
    payload = {
        'request_id': 't-no-hit',
        'source_system': 'test',
        'entity_type': 'PERSON',
        'name': {'full_name': 'Random Person'},
        'identifiers': [{'type': 'SSN', 'value': 'SYNTH-SSN-X'}],
        'addresses': [],
        'screening_lists': ['OFAC_SDN']
    }
    res = client.post('/api/v1/screenings', json=payload)
    assert res.status_code == 200
    assert res.json()['decision'] == 'NO_HIT'


def test_potential_hit(monkeypatch):
    cand = [{'_id': '1', '_source': {
        'list_source': 'OFAC_SDN', 'source_record_id': 'OFAC-1', 'name': 'John Adam Doe',
        'name_normalized': 'john adam doe', 'aliases_normalized': ['john a doe'],
        'dob': '1980-01-15', 'identifier_hashes': []
    }}]
    monkeypatch.setattr('app.main.search_candidates', lambda *args, **kwargs: cand)
    payload = {
        'request_id': 't-hit',
        'source_system': 'test',
        'entity_type': 'PERSON',
        'name': {'full_name': 'John Adam Doe'},
        'dob': '1980-01-15',
        'identifiers': [],
        'addresses': [],
        'screening_lists': ['OFAC_SDN']
    }
    res = client.post('/api/v1/screenings', json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body['decision'] == 'POTENTIAL_HIT'
    assert len(body['matches']) >= 1
