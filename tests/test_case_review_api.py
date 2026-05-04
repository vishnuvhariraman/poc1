from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models import CaseORM, ScreeningMatchORM, ScreeningRequestORM

client = TestClient(app)


def _seed_case():
    db = SessionLocal()
    req = ScreeningRequestORM(request_id="case-req-1", source_system="test", entity_type="PERSON", payload={"name": {"full_name": "Raj Kumar Dev"}})
    db.add(req)
    db.commit()
    db.refresh(req)
    db.add_all([
        ScreeningMatchORM(screening_request_id=req.id, match_id="m1", list_source="OFAC_SDN", source_record_id="OFAC-MULTI-PERSON-001", matched_name="Raj Kumar Dev", score=95, matched_fields=["name"], reason_codes=["DOB_EXACT"]),
        ScreeningMatchORM(screening_request_id=req.id, match_id="m2", list_source="UN_CONSOLIDATED", source_record_id="UN-MULTI-PERSON-002", matched_name="Rajesh K Dev", score=90, matched_fields=["alias"], reason_codes=[]),
        ScreeningMatchORM(screening_request_id=req.id, match_id="m3", list_source="EU_CONSOLIDATED", source_record_id="EU-MULTI-PERSON-003", matched_name="Raj Kumer Dev", score=89, matched_fields=["alias"], reason_codes=[]),
    ])
    db.commit()
    case = CaseORM(screening_request_id=req.id, reason="test")
    db.add(case)
    db.commit()
    db.refresh(case)
    db.close()
    return case.id


def test_cases_endpoints_and_actions():
    case_id = _seed_case()
    q = client.get('/api/v1/cases')
    assert q.status_code == 200
    assert any(c['case_id'] == case_id for c in q.json())

    d = client.get(f'/api/v1/cases/{case_id}')
    assert d.status_code == 200
    assert len(d.json()['matches']) >= 3

    a = client.post(f'/api/v1/cases/{case_id}/actions', json={"action": "ESCALATE_LEVEL_2", "comment": "needs L2", "actor": "demo-user"})
    assert a.status_code == 200
    assert a.json()['status'] == 'ESCALATED_LEVEL_2'
