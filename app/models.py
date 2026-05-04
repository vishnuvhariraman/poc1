import enum
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import JSON, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Decision(str, enum.Enum):
    NO_HIT = "NO_HIT"
    POTENTIAL_HIT = "POTENTIAL_HIT"


class EntityType(str, enum.Enum):
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"


class IdentifierType(str, enum.Enum):
    SSN = "SSN"
    TAX_ID = "TAX_ID"
    PASSPORT = "PASSPORT"
    NATIONAL_ID = "NATIONAL_ID"


class NameModel(BaseModel):
    full_name: str
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None


class IdentifierModel(BaseModel):
    type: IdentifierType
    value: str


class AddressModel(BaseModel):
    line1: str
    city: str
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str


class ScreeningRequest(BaseModel):
    request_id: str
    source_system: str
    entity_type: EntityType
    name: NameModel
    dob: Optional[date] = None
    identifiers: list[IdentifierModel] = Field(default_factory=list)
    addresses: list[AddressModel] = Field(default_factory=list)
    screening_lists: list[str] = Field(default_factory=lambda: ["OFAC_SDN", "UN_CONSOLIDATED", "EU_CONSOLIDATED"])


class MatchModel(BaseModel):
    match_id: str
    list_source: str
    source_record_id: str
    matched_name: str
    score: float
    matched_fields: list[str]
    reason_codes: list[str]


class ScreeningResponse(BaseModel):
    request_id: str
    decision: Decision
    screening_time_ms: int
    screening_version: str
    lists_screened: list[str]
    case_id: Optional[int] = None
    matches: list[MatchModel]


class ScreeningRequestORM(Base):
    __tablename__ = "screening_requests"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    source_system: Mapped[str] = mapped_column(String(100))
    entity_type: Mapped[str] = mapped_column(String(20))
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ScreeningMatchORM(Base):
    __tablename__ = "screening_matches"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    screening_request_id: Mapped[int] = mapped_column(ForeignKey("screening_requests.id"), index=True)
    match_id: Mapped[str] = mapped_column(String(100))
    list_source: Mapped[str] = mapped_column(String(50))
    source_record_id: Mapped[str] = mapped_column(String(100))
    matched_name: Mapped[str] = mapped_column(String(255))
    score: Mapped[float] = mapped_column(Float)
    matched_fields: Mapped[dict] = mapped_column(JSON)
    reason_codes: Mapped[dict] = mapped_column(JSON)




class CaseActionType(str, enum.Enum):
    CLOSE_FALSE_POSITIVE = "CLOSE_FALSE_POSITIVE"
    ESCALATE_LEVEL_2 = "ESCALATE_LEVEL_2"


class CaseORM(Base):
    __tablename__ = "cases"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    screening_request_id: Mapped[int] = mapped_column(ForeignKey("screening_requests.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="OPEN")
    current_level: Mapped[int] = mapped_column(Integer, default=1)
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CaseActionORM(Base):
    __tablename__ = "case_actions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), index=True)
    action: Mapped[str] = mapped_column(String(50))
    actor: Mapped[str] = mapped_column(String(100))
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CaseQueueItem(BaseModel):
    case_id: int
    request_id: str
    status: str
    current_level: int
    created_at: datetime
    match_count: int
    highest_score: float
    entity_type: str
    screened_name: str
    lists_matched: list[str]


class CaseActionRequest(BaseModel):
    action: CaseActionType
    comment: Optional[str] = None
    actor: str = "demo-user"
