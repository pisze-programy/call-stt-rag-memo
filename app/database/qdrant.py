import os

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

qdrant = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_KEY"))
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION")

def init_qdrant():
    collections = qdrant.get_collections().collections

    assert COLLECTION_NAME

    exists = any(c.name == COLLECTION_NAME for c in collections)

    if exists:
        return

    qdrant.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=1536,
            distance=Distance.COSINE,
        ),
    )