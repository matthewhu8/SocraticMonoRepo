from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import annoy
import os
import json

app = FastAPI(title="Vector Service")

# Initialize the model and index
model = SentenceTransformer('all-MiniLM-L6-v2')
INDEX_PATH = "data/vector_store/annoy_index.ann"
METADATA_PATH = "data/vector_store/metadata.json"

# Ensure data directory exists
os.makedirs("data/vector_store", exist_ok=True)

# Load or create index
def get_index():
    if os.path.exists(INDEX_PATH):
        index = annoy.AnnoyIndex(384, 'angular')  # 384 is the dimension of the embeddings
        index.load(INDEX_PATH)
        return index
    return annoy.AnnoyIndex(384, 'angular')

# Load or create metadata
def get_metadata():
    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, 'r') as f:
            return json.load(f)
    return {}

# Save metadata
def save_metadata(metadata):
    with open(METADATA_PATH, 'w') as f:
        json.dump(metadata, f)

# Models
class EmbeddingRequest(BaseModel):
    id: str
    text: str
    metadata: Optional[Dict[str, Any]] = {}

class SearchRequest(BaseModel):
    query: str
    n_results: int = 5

# Endpoints
@app.post("/embeddings")
async def store_embedding(request: EmbeddingRequest):
    # Generate embedding
    embedding = model.encode(request.text)
    
    # Get or create index
    index = get_index()
    metadata = get_metadata()
    
    # Add to index
    item_id = len(metadata)
    index.add_item(item_id, embedding)
    
    # Store metadata
    metadata[str(item_id)] = {
        "id": request.id,
        "text": request.text,
        "metadata": request.metadata
    }
    
    # Save both
    index.save(INDEX_PATH)
    save_metadata(metadata)
    
    return {"message": "Embedding stored successfully", "item_id": item_id}

@app.post("/search")
async def search_similar(request: SearchRequest):
    # Generate query embedding
    query_embedding = model.encode(request.query)
    
    # Get index and metadata
    index = get_index()
    metadata = get_metadata()
    
    # Search
    n_items = len(metadata)
    n_results = min(request.n_results, n_items)
    
    # Get nearest neighbors
    nearest_ids = index.get_nns_by_vector(
        query_embedding,
        n_results,
        include_distances=True
    )
    
    # Format results
    results = []
    for idx, distance in zip(nearest_ids[0], nearest_ids[1]):
        item_metadata = metadata[str(idx)]
        results.append({
            "id": item_metadata["id"],
            "text": item_metadata["text"],
            "metadata": item_metadata["metadata"],
            "distance": float(distance)
        })
    
    return results

@app.delete("/embeddings/{id}")
async def delete_embedding(id: str):
    # Get index and metadata
    index = get_index()
    metadata = get_metadata()
    
    # Find item_id for the given id
    item_id = None
    for idx, item in metadata.items():
        if item["id"] == id:
            item_id = int(idx)
            break
    
    if item_id is None:
        raise HTTPException(status_code=404, detail="Embedding not found")
    
    # Remove from metadata
    del metadata[str(item_id)]
    
    # Save updated metadata
    save_metadata(metadata)
    
    return {"message": "Embedding deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 