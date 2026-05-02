import time
from datetime import date

from fastapi import BackgroundTasks, Depends, FastAPI
from sqlalchemy.orm import Session

from app.case_service import create_case_async
from app.config import settings
from app.database import engine, get_db
from app.models import Base, Decision, MatchModel, ScreeningMatchORM, ScreeningRequest, ScreeningRequestORM, ScreeningResponse
from app.normalizer import normalize_text
from app.opensearch_client import search_candidates
from app.scorer import score_match
from app.security import hmac_identifier

app = FastAPI(title=settings.app_name)
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
