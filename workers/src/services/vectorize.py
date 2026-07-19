"""Vectorize service for product embeddings and similarity search."""

import json
import js
from pyodide.ffi import to_js as _to_js
from js import Object


def to_js(obj):
    return _to_js(obj, dict_converter=Object.fromEntries)


EMBEDDING_MODEL = "@cf/baai/bge-m3"
VECTOR_DIMENSION = 1024


class VectorizeService:
    """Vectorize service for product embeddings and similarity search."""

    def __init__(self, env):
        self.env = env
        self.ai = env.AI
        self.index = env.VECTORIZE

    async def upsert_product(self, product_id: str, text: str, metadata: dict) -> bool:
        """Generate embedding and upsert to Vectorize index."""
        try:
            # Generate embedding
            result = await self.ai.run(
                EMBEDDING_MODEL,
                {"text": [text]},
            )
            
            # Extract vector (handle different response formats)
            if isinstance(result, dict) and "data" in result:
                vector = result["data"][0]
            elif isinstance(result, list):
                vector = result[0]
            else:
                vector = result
            
            if not vector or len(vector) != VECTOR_DIMENSION:
                print(json.dumps({
                    "event": "vectorize_upsert_error",
                    "product_id": product_id,
                    "error": f"Invalid vector dimension: {len(vector) if vector else 0}",
                }))
                return False
            
            # Upsert to Vectorize
            await self.index.upsert([
                {
                    "id": product_id,
                    "values": vector,
                    "metadata": metadata,
                }
            ])
            
            print(json.dumps({
                "event": "vectorize_upsert_ok",
                "product_id": product_id,
            }))
            return True
            
        except Exception as e:
            print(json.dumps({
                "event": "vectorize_upsert_error",
                "product_id": product_id,
                "error": str(e),
            }))
            return False

    async def delete_product(self, product_id: str) -> bool:
        """Delete a product vector from the index."""
        try:
            await self.index.delete([product_id])
            return True
        except Exception as e:
            print(json.dumps({
                "event": "vectorize_delete_error",
                "product_id": product_id,
                "error": str(e),
            }))
            return False

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: dict = None,
    ) -> list[dict]:
        """Search for similar products by query text."""
        try:
            # Generate query embedding
            result = await self.ai.run(
                EMBEDDING_MODEL,
                {"text": [query]},
            )
            
            if isinstance(result, dict) and "data" in result:
                vector = result["data"][0]
            elif isinstance(result, list):
                vector = result[0]
            else:
                vector = result
            
            if not vector:
                return []
            
            # Query Vectorize
            query_options = {
                "vector": vector,
                "topK": top_k,
                "returnValues": True,
                "returnMetadata": True,
            }
            
            if filter_metadata:
                query_options["filter"] = filter_metadata
            
            results = await self.index.query(**query_options)
            
            matches = results.get("matches", [])
            return [
                {
                    "product_id": match.get("id"),
                    "score": match.get("score", 0),
                    "metadata": match.get("metadata", {}),
                }
                for match in matches
            ]
            
        except Exception as e:
            print(json.dumps({
                "event": "vectorize_search_error",
                "query": query[:100],
                "error": str(e),
            }))
            return []