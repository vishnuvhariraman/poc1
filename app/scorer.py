from rapidfuzz import fuzz


def score_match(
    request_name: str,
    candidate: dict,
    request_dob: str | None,
    request_identifier_hashes: set[str],
):
    source = candidate["_source"]
    matched_fields = []
    reason_codes = []

    entity_type = source.get("entity_type")

    name_score = fuzz.token_sort_ratio(
        request_name,
        source.get("name_normalized", ""),
    )

    alias_score = max(
        [
            fuzz.token_sort_ratio(request_name, alias)
            for alias in source.get("aliases_normalized", [])
        ]
        or [0]
    )

    best_score = max(name_score, alias_score)

    if name_score >= alias_score:
        matched_fields.append("name")

        if name_score == 100:
            reason_codes.append("NAME_EXACT")
        elif name_score >= 90:
            reason_codes.append("NAME_FUZZY_STRONG")
        elif name_score >= 80:
            reason_codes.append("NAME_FUZZY_MEDIUM")
    else:
        matched_fields.append("alias")

        if alias_score == 100:
            reason_codes.append("ALIAS_EXACT")
        elif alias_score >= 90:
            reason_codes.append("ALIAS_FUZZY_STRONG")
        elif alias_score >= 80:
            reason_codes.append("ALIAS_FUZZY_MEDIUM")

    # Person scoring: name/alias + DOB/identifier improves confidence
    if entity_type == "PERSON":
        final = best_score * 0.7

        if request_dob and source.get("dob") == request_dob:
            final += 20
            matched_fields.append("dob")
            reason_codes.append("DOB_EXACT")

    # Organization scoring: strong name/alias match can stand alone
    elif entity_type == "ORGANIZATION":
        if best_score == 100:
            final = 90
        elif best_score >= 90:
            final = 85
        elif best_score >= 80:
            final = 75
        else:
            final = best_score * 0.7

    else:
        final = best_score * 0.7

    source_hashes = set(source.get("identifier_hashes", []))

    if request_identifier_hashes and source_hashes.intersection(request_identifier_hashes):
        final += 25
        matched_fields.append("identifier")
        reason_codes.append("IDENTIFIER_MATCH")

    return min(100.0, round(final, 2)), matched_fields, reason_codes