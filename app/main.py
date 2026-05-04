import time

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.case_service import create_case_async
from app.config import settings
from app.database import engine, get_db
from app.models import (
    Base,
    CaseActionORM,
    CaseActionRequest,
    CaseQueueItem,
    CaseORM,
    Decision,
    MatchModel,
    ScreeningMatchORM,
    ScreeningRequest,
    ScreeningRequestORM,
    ScreeningResponse,
)
from app.normalizer import normalize_text
from app.opensearch_client import search_candidates
from app.scorer import score_match
from app.security import hmac_identifier

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/v1/screenings", response_model=ScreeningResponse)
def screen_entity(payload: ScreeningRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    start = time.perf_counter()
    normalized_name = normalize_text(payload.name.full_name)
    identifier_hashes = {hmac_identifier(i.value) for i in payload.identifiers}

    candidates = search_candidates(normalized_name, payload.entity_type.value, payload.screening_lists)

    matches: list[MatchModel] = []
    for cand in candidates:
        score, matched_fields, reason_codes = score_match(
            normalized_name,
            cand,
            payload.dob.isoformat() if payload.dob else None,
            identifier_hashes,
        )
        if score >= settings.score_threshold:
            src = cand["_source"]
            matches.append(
                MatchModel(
                    match_id=f"m-{cand['_id']}",
                    list_source=src["list_source"],
                    source_record_id=src["source_record_id"],
                    matched_name=src["name"],
                    score=score,
                    matched_fields=matched_fields,
                    reason_codes=reason_codes,
                )
            )

    decision = Decision.POTENTIAL_HIT if matches else Decision.NO_HIT

    safe_payload = payload.model_dump(mode="json")
    for i in safe_payload.get("identifiers", []):
        i["value"] = "REDACTED"

    req_row = ScreeningRequestORM(
        request_id=payload.request_id,
        source_system=payload.source_system,
        entity_type=payload.entity_type.value,
        payload=safe_payload,
    )
    db.add(req_row)
    db.commit()
    db.refresh(req_row)

    for m in matches:
        db.add(
            ScreeningMatchORM(
                screening_request_id=req_row.id,
                match_id=m.match_id,
                list_source=m.list_source,
                source_record_id=m.source_record_id,
                matched_name=m.matched_name,
                score=m.score,
                matched_fields=m.matched_fields,
                reason_codes=m.reason_codes,
            )
        )
    db.commit()

    case_id = None
    if decision == Decision.POTENTIAL_HIT:
        background_tasks.add_task(create_case_async, req_row.id, "Potential sanctions match")
        case_id = req_row.id

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    return ScreeningResponse(
        request_id=payload.request_id,
        decision=decision,
        screening_time_ms=elapsed_ms,
        screening_version=settings.screening_version,
        lists_screened=payload.screening_lists,
        case_id=case_id,
        matches=matches,
    )


@app.get("/api/v1/cases", response_model=list[CaseQueueItem])
def list_cases(db: Session = Depends(get_db)):
    cases = db.query(CaseORM).order_by(CaseORM.created_at.desc()).all()
    items = []
    for case in cases:
        req = db.query(ScreeningRequestORM).filter(ScreeningRequestORM.id == case.screening_request_id).first()
        matches = db.query(ScreeningMatchORM).filter(ScreeningMatchORM.screening_request_id == case.screening_request_id).all()
        items.append(
            CaseQueueItem(
                case_id=case.id,
                request_id=req.request_id if req else "",
                status=case.status,
                current_level=case.current_level,
                created_at=case.created_at,
                match_count=len(matches),
                highest_score=max([m.score for m in matches] or [0]),
                entity_type=req.entity_type if req else "",
                screened_name=(req.payload.get("name", {}).get("full_name", "") if req and req.payload else ""),
                lists_matched=sorted(list({m.list_source for m in matches})),
            )
        )
    return items


@app.get("/api/v1/cases/{case_id}")
def case_detail(case_id: int, db: Session = Depends(get_db)):
    case = db.query(CaseORM).filter(CaseORM.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    req = db.query(ScreeningRequestORM).filter(ScreeningRequestORM.id == case.screening_request_id).first()
    matches = db.query(ScreeningMatchORM).filter(ScreeningMatchORM.screening_request_id == case.screening_request_id).all()
    actions = db.query(CaseActionORM).filter(CaseActionORM.case_id == case_id).order_by(CaseActionORM.created_at.desc()).all()

    return {
        "case": {
            "case_id": case.id,
            "status": case.status,
            "current_level": case.current_level,
            "created_at": case.created_at,
            "reason": case.reason,
            "match_count": len(matches),
            "highest_score": max([m.score for m in matches] or [0]),
        },
        "screening_request": {
            "request_id": req.request_id if req else None,
            "source_system": req.source_system if req else None,
            "entity_type": req.entity_type if req else None,
            "payload": req.payload if req else None,
        },
        "matches": [
            {
                "score": m.score,
                "matched_fields": m.matched_fields,
                "reason_codes": m.reason_codes,
                "list_source": m.list_source,
                "source_record_id": m.source_record_id,
                "matched_name": m.matched_name,
            }
            for m in matches
        ],
        "actions": [
            {
                "action": a.action,
                "actor": a.actor,
                "comment": a.comment,
                "created_at": a.created_at,
            }
            for a in actions
        ],
    }


@app.post("/api/v1/cases/{case_id}/actions")
def case_action(case_id: int, payload: CaseActionRequest, db: Session = Depends(get_db)):
    case = db.query(CaseORM).filter(CaseORM.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if payload.action.value == "CLOSE_FALSE_POSITIVE":
        case.status = "CLOSED_FALSE_POSITIVE"
    elif payload.action.value == "ESCALATE_LEVEL_2":
        case.status = "ESCALATED_LEVEL_2"
        case.current_level = 2

    db.add(CaseActionORM(case_id=case_id, action=payload.action.value, actor=payload.actor, comment=payload.comment))
    db.commit()
    db.refresh(case)
    return {"case_id": case.id, "status": case.status, "current_level": case.current_level}
