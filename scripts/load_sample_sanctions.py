from opensearchpy import OpenSearch

from app.config import settings
from app.normalizer import normalize_text
from app.security import hmac_identifier


records = [
    {
        "source_record_id": "OFAC-1001",
        "list_source": "OFAC_SDN",
        "entity_type": "PERSON",
        "name": "John Adam Doe",
        "dob": "1980-01-15",
        "aliases": ["J. A. Doe", "John A Doe"],
        "identifier_hashes": [hmac_identifier("SYNTH-SSN-0001")],
    },
    {
        "source_record_id": "UN-2001",
        "list_source": "UN_CONSOLIDATED",
        "entity_type": "PERSON",
        "name": "Jonathon Doe",
        "dob": "1981-04-10",
        "aliases": ["John Doe Jr"],
        "identifier_hashes": [hmac_identifier("SYNTH-PASSPORT-0002")],
    },
    {
        "source_record_id": "EU-3001",
        "list_source": "EU_CONSOLIDATED",
        "entity_type": "ORGANIZATION",
        "name": "ABC Trading LLC",
        "dob": None,
        "aliases": ["ABC Trading", "A.B.C. Trading LLC"],
        "identifier_hashes": [hmac_identifier("SYNTH-TAX-ORG-0003")],
    },
    {
        "source_record_id": "OFAC-1002",
        "list_source": "OFAC_SDN",
        "entity_type": "ORGANIZATION",
        "name": "Global Export Ventures",
        "dob": None,
        "aliases": ["GEV"],
        "identifier_hashes": [hmac_identifier("SYNTH-TAX-ORG-0004")],
    },
]


def main():
    client = OpenSearch(hosts=[{"host": settings.opensearch_host, "port": settings.opensearch_port}], use_ssl=False, verify_certs=False)

    mapping = {
        "mappings": {
            "properties": {
                "source_record_id": {"type": "keyword"},
                "list_source": {"type": "keyword"},
                "entity_type": {"type": "keyword"},
                "name": {"type": "text"},
                "name_normalized": {"type": "text"},
                "aliases": {"type": "text"},
                "aliases_normalized": {"type": "text"},
                "dob": {"type": "keyword"},
                "identifier_hashes": {"type": "keyword"},
            }
        }
    }

    if client.indices.exists(settings.opensearch_index):
        client.indices.delete(index=settings.opensearch_index)
    client.indices.create(index=settings.opensearch_index, body=mapping)

    for i, record in enumerate(records):
        record["name_normalized"] = normalize_text(record["name"])
        record["aliases_normalized"] = [normalize_text(x) for x in record["aliases"]]
        client.index(index=settings.opensearch_index, id=str(i + 1), body=record, refresh=True)

    print(f"Loaded {len(records)} records into {settings.opensearch_index}")


if __name__ == "__main__":
    main()
