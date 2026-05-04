from rapidfuzz import fuzz
from scripts.load_sample_sanctions import REQUIRED_SCHEMA_KEYS, records


def test_loader_has_expected_count_and_schema():
    assert len(records) == 10
    for record in records:
        assert REQUIRED_SCHEMA_KEYS.issubset(record.keys())


def _is_candidate_match(request_name: str, record: dict) -> bool:
    if fuzz.token_sort_ratio(request_name, record["name_normalized"]) >= 80:
        return True
    return any(fuzz.token_sort_ratio(request_name, alias) >= 80 for alias in record["aliases_normalized"])


def test_raj_kumar_dev_matches_at_least_three_records():
    request_name = "raj kumar dev"
    person_records = [r for r in records if r["entity_type"] == "PERSON"]
    matched = [r for r in person_records if _is_candidate_match(request_name, r)]
    assert len(matched) >= 3


def test_global_falcon_trading_llc_matches_at_least_three_records():
    request_name = "global falcon trading llc"
    org_records = [r for r in records if r["entity_type"] == "ORGANIZATION"]
    matched = [r for r in org_records if _is_candidate_match(request_name, r)]
    assert len(matched) >= 3
