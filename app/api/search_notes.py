from fastapi import APIRouter
from pydantic import BaseModel
from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.database.qdrant import qdrant, COLLECTION_NAME
from app.modules.stt_manager import embed_text

router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    phone: str
    limit: int

@router.post("/search-notes")
async def search_notes(request: SearchRequest):
    query_vector = await embed_text(request.query)
    limit = request.limit if request.limit else 5

    results = qdrant.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        query_filter=Filter(
            must=[FieldCondition(key="caller_id", match=MatchValue(value=request.phone))]
        ),
        limit=limit
    )

    return [
        {"text": hit.payload.get("text"), "score": hit.score}
        for hit in results
    ]