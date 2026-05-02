from rapidfuzz import fuzz


def score_match(request_name: str, candidate: dict, request_dob: str | None, request_identifier_hashes: set[str]):
    source = candidate["_source"]
    matched_fields = []
    reason_codes = []

    name_score = fuzz.token_sort_ratio(request_name, source.get("name_normalized", ""))
    alias_score = max([fuzz.token_sort_ratio(request_name, a) for a in source.get("aliases_normalized", [])] or [0])
    final = max(name_score, alias_score) * 0.7

    if name_score >= alias_score:
        matched_fields.append("name")
    else:
        matched_fields.append("alias")

    if request_dob and source.get("dob") == request_dob:
        final += 20
        matched_fields.append("dob")
        reason_codes.append("DOB_EXACT")

    source_hashes = set(source.get("identifier_hashes", []))
    if request_identifier_hashes and source_hashes.intersection(request_identifier_hashes):
        final += 25
        matched_fields.append("identifier")
        reason_codes.append("IDENTIFIER_MATCH")

    return min(100.0, round(final, 2)), matched_fields, reason_codes
