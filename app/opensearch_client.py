from opensearchpy import OpenSearch

from app.config import settings


def get_client() -> OpenSearch:
    return OpenSearch(
        hosts=[{"host": settings.opensearch_host, "port": settings.opensearch_port}],
        use_ssl=False,
        verify_certs=False,
    )


def search_candidates(name_normalized: str, entity_type: str, screening_lists: list[str], size: int = 20):
    client = get_client()
    query = {
        "size": size,
        "query": {
            "bool": {
                "must": [
                    {"terms": {"list_source": screening_lists}},
                    {"term": {"entity_type": entity_type}},
                ],
                "should": [
                    {"match": {"name_normalized": {"query": name_normalized, "boost": 3}}},
                    {"match": {"aliases_normalized": {"query": name_normalized}}},
                ],
                "minimum_should_match": 1,
            }
        },
    }
    response = client.search(index=settings.opensearch_index, body=query)
    return response["hits"]["hits"]
