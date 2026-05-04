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
        "name_normalized": "john adam doe",
        "aliases": ["J. A. Doe", "John A Doe"],
        "aliases_normalized": ["j a doe", "john a doe"],
        "dob": "1980-01-15",
        "identifier_hashes": [hmac_identifier("SYNTH-SSN-0001")],
        "active": True,
    },
    {
        "source_record_id": "UN-2001",
        "list_source": "UN_CONSOLIDATED",
        "entity_type": "PERSON",
        "name": "Jonathon Doe",
        "name_normalized": "jonathon doe",
        "aliases": ["John Doe Jr"],
        "aliases_normalized": ["john doe jr"],
        "dob": "1981-04-10",
        "identifier_hashes": [hmac_identifier("SYNTH-PASSPORT-0002")],
        "active": True,
    },
    {
        "source_record_id": "EU-3001",
        "list_source": "EU_CONSOLIDATED",
        "entity_type": "ORGANIZATION",
        "name": "ABC Trading LLC",
        "name_normalized": "abc trading llc",
        "aliases": ["ABC Trading", "A.B.C. Trading LLC"],
        "aliases_normalized": ["abc trading", "a b c trading llc"],
        "dob": None,
        "identifier_hashes": [hmac_identifier("SYNTH-TAX-ORG-0003")],
        "active": True,
    },
    {
        "source_record_id": "OFAC-1002",
        "list_source": "OFAC_SDN",
        "entity_type": "ORGANIZATION",
        "name": "Global Export Ventures",
        "name_normalized": "global export ventures",
        "aliases": ["GEV"],
        "aliases_normalized": ["gev"],
        "dob": None,
        "identifier_hashes": [hmac_identifier("SYNTH-TAX-ORG-0004")],
        "active": True,
    },
    {
        "source_record_id": "OFAC-MULTI-PERSON-001",
        "list_source": "OFAC_SDN",
        "entity_type": "PERSON",
        "name": "Raj Kumar Dev",
        "name_normalized": "raj kumar dev",
        "aliases": ["Rajesh Kumar Dev", "R K Dev", "Raj K Dev"],
        "aliases_normalized": ["rajesh kumar dev", "r k dev", "raj k dev"],
        "dob": "1978-04-12",
        "identifier_hashes": [],
        "active": True,
    },
    {
        "source_record_id": "UN-MULTI-PERSON-002",
        "list_source": "UN_CONSOLIDATED",
        "entity_type": "PERSON",
        "name": "Rajesh K Dev",
        "name_normalized": "rajesh k dev",
        "aliases": ["Raj Kumar Dev", "Rajesh Dev", "R Kumar Dev"],
        "aliases_normalized": ["raj kumar dev", "rajesh dev", "r kumar dev"],
        "dob": "1978-04-12",
        "identifier_hashes": [],
        "active": True,
    },
    {
        "source_record_id": "EU-MULTI-PERSON-003",
        "list_source": "EU_CONSOLIDATED",
        "entity_type": "PERSON",
        "name": "Raj Kumer Dev",
        "name_normalized": "raj kumer dev",
        "aliases": ["Raj Kumar Dev", "R K Dev"],
        "aliases_normalized": ["raj kumar dev", "r k dev"],
        "dob": "1978-04-12",
        "identifier_hashes": [],
        "active": True,
    },
    {
        "source_record_id": "OFAC-MULTI-ORG-001",
        "list_source": "OFAC_SDN",
        "entity_type": "ORGANIZATION",
        "name": "Global Falcon Trading LLC",
        "name_normalized": "global falcon trading llc",
        "aliases": ["Global Falcon Trade LLC", "Falcon Global Trading", "G F Trading LLC"],
        "aliases_normalized": ["global falcon trade llc", "falcon global trading", "g f trading llc"],
        "dob": None,
        "identifier_hashes": [],
        "active": True,
    },
    {
        "source_record_id": "UN-MULTI-ORG-002",
        "list_source": "UN_CONSOLIDATED",
        "entity_type": "ORGANIZATION",
        "name": "Global Falcon Trading Limited",
        "name_normalized": "global falcon trading limited",
        "aliases": ["Global Falcon Trading LLC", "Falcon Trading Limited"],
        "aliases_normalized": ["global falcon trading llc", "falcon trading limited"],
        "dob": None,
        "identifier_hashes": [],
        "active": True,
    },
    {
        "source_record_id": "EU-MULTI-ORG-003",
        "list_source": "EU_CONSOLIDATED",
        "entity_type": "ORGANIZATION",
        "name": "Global Falkan Trading LLC",
        "name_normalized": "global falkan trading llc",
        "aliases": ["Global Falcon Trading", "GF Trading LLC"],
        "aliases_normalized": ["global falcon trading", "gf trading llc"],
        "dob": None,
        "identifier_hashes": [],
        "active": True,
    },
]

REQUIRED_SCHEMA_KEYS = {
    "source_record_id",
    "list_source",
    "entity_type",
    "name",
    "name_normalized",
    "aliases",
    "aliases_normalized",
    "dob",
    "identifier_hashes",
    "active",
}


def _validate_record(record: dict):
    missing = REQUIRED_SCHEMA_KEYS.difference(record.keys())
    if missing:
        raise ValueError(f"Record {record.get('source_record_id')} missing keys: {sorted(missing)}")


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
                "active": {"type": "boolean"},
            }
        }
    }

    if client.indices.exists(settings.opensearch_index):
        client.indices.delete(index=settings.opensearch_index)
    client.indices.create(index=settings.opensearch_index, body=mapping)

    for i, record in enumerate(records):
        _validate_record(record)
        record["name_normalized"] = normalize_text(record["name"])
        record["aliases_normalized"] = [normalize_text(x) for x in record["aliases"]]
        client.index(index=settings.opensearch_index, id=str(i + 1), body=record, refresh=True)

    print(f"Loaded {len(records)} records into {settings.opensearch_index}")


if __name__ == "__main__":
    main()
