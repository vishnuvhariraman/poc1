from app.models import ScreeningRequest
from app.normalizer import normalize_screening_request
from app.security import hmac_identifier


def test_normalize_screening_request_name_dob_identifiers_and_addresses():
    payload = ScreeningRequest(
        request_id="req-1",
        source_system="unit-test",
        entity_type="PERSON",
        name={"full_name": "  José  A.   Núñez-Smith!! "},
        dob="1980-01-15",
        identifiers=[
            {"type": "SSN", "value": "123-45-6789"},
            {"type": "PASSPORT", "value": "AB 123456"},
        ],
        addresses=[
            {
                "line1": "  123, Main St. ",
                "city": " São   Paulo ",
                "state": " SP ",
                "postal_code": " 01000-000 ",
                "country": " Brésil ",
            },
            {
                "line1": "5 Rue de l'Université",
                "city": "Paris",
                "country": "France",
            },
        ],
        screening_lists=["OFAC_SDN", "EU_CONSOLIDATED"],
    )

    normalized = normalize_screening_request(payload)

    assert normalized["normalized_name"] == "jose a nunez smith"
    assert normalized["normalized_entity_type"] == "person"
    assert normalized["dob"] == "1980-01-15"
    assert normalized["screening_lists"] == ["OFAC_SDN", "EU_CONSOLIDATED"]

    assert normalized["identifiers"] == [
        {"type": "SSN", "value_hash": hmac_identifier("123-45-6789")},
        {"type": "PASSPORT", "value_hash": hmac_identifier("AB 123456")},
    ]
    assert "value" not in normalized["identifiers"][0]

    assert normalized["addresses"][0] == {
        "line1": "123 main st",
        "city": "sao paulo",
        "state": "sp",
        "postal_code": "01000 000",
        "country": "bresil",
    }
    assert normalized["addresses"][1]["line1"] == "5 rue de l universite"
    assert normalized["countries"] == ["bresil", "france"]
