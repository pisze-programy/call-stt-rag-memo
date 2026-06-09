from fastapi import APIRouter
from pydantic import BaseModel
from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.database.qdrant import qdrant, COLLECTION_NAME
from app.modules.stt_manager import embed_text, interpret_search_query

router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    phone: str
    limit: int

@router.post("/search-notes")
async def search_notes(request: SearchRequest):
    query_vector = await embed_text(request.query)
    limit = request.limit if request.limit else 5

    results = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=Filter(
            must=[FieldCondition(key="caller_id", match=MatchValue(value=request.phone))]
        ),
        limit=limit,
        with_payload=True,
        with_vectors=False,
    )

    context = "\n\n--- NOTE START ---\n".join([hit.payload.get("text", "") for hit in results.points])
    answer = await interpret_search_query(request.query, context)

    return {"answer": answer, "context": context}