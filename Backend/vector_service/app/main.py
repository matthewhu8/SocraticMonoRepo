from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import os
import json
from threading import Lock
from datetime import datetime
import chromadb
from chromadb.utils import embedding_functions

app = FastAPI(title="Vector Service")

# Initialize the model
model_name = 'all-MiniLM-L6-v2'
model = SentenceTransformer(model_name)
DIMENSION = 384  # Dimension of the embeddings

# Chroma settings
CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")

# Collection names
HIDDEN_VALUES_COLLECTION = "hidden_values"
TEACHING_MATERIALS_COLLECTION = "teaching_materials"

class VectorDatabase:
    _instance = None
    _lock = Lock()
    _initialized = False

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(VectorDatabase, cls).__new__(cls)
            return cls._instance

    def __init__(self):
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    try:
                        # Initialize Chroma client with persistence
                        self.client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIRECTORY)
                        
                        # Initialize sentence transformer for embeddings
                        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                            model_name=model_name
                        )
                        
                        # Create collections
                        self.hidden_values = self.client.get_or_create_collection(
                            name=HIDDEN_VALUES_COLLECTION,
                            embedding_function=self.embedding_function
                        )
                        
                        self.teaching_materials = self.client.get_or_create_collection(
                            name=TEACHING_MATERIALS_COLLECTION,
                            embedding_function=self.embedding_function
                        )
                        
                        self._initialized = True
                    except Exception as e:
                        print(f"Failed to initialize Chroma: {str(e)}")
                        raise

    def store_hidden_value(self, problem_id: str, content: str, metadata: Dict[str, Any]):
        """Store a hidden value with its embedding."""
        # Format metadata to match the expected structure
        metadata_with_hidden_values = {
            "problem_id": problem_id,
            "created_at": int(datetime.now().timestamp()),
            "metadata": {
                "hidden_values": metadata
            }
        }
        
        self.hidden_values.add(
            documents=[content],
            metadatas=[metadata_with_hidden_values],
            ids=[f"{problem_id}_{int(datetime.now().timestamp())}"]
        )

    def store_teaching_material(self, topic: str, content: str, metadata: Dict[str, Any]):
        """Store a teaching material with its embedding."""
        metadata_obj = {
            "topic": topic,
            "created_at": int(datetime.now().timestamp()),
            "metadata": metadata
        }
        
        self.teaching_materials.add(
            documents=[content],
            metadatas=[metadata_obj],
            ids=[f"{topic}_{int(datetime.now().timestamp())}"]
        )

    def search_hidden_values(self, problem_id: str, query: str, limit: int = 5) -> Dict[str, Any]:
        """Search for hidden values specific to a problem."""
        # Query with where filter to match problem_id
        results = self.hidden_values.query(
            query_texts=[query],
            where={"problem_id": problem_id},
            n_results=1  # Original code only returns the best match
        )
        
        # Format results to match the original implementation
        if results and results['metadatas'] and results['metadatas'][0]:
            # Extract hidden_values from metadata to match original format
            return results['metadatas'][0][0].get('metadata', {}).get('hidden_values', {})
        return {}

    def search_teaching_materials(self, query: str, topic: Optional[str] = None, limit: int = 3) -> List[Dict[str, Any]]:
        """Search for relevant teaching materials."""
        # Build where clause if topic is provided
        where_clause = {"topic": topic} if topic else None
        
        # Query the collection
        results = self.teaching_materials.query(
            query_texts=[query],
            where=where_clause,
            n_results=limit
        )
        
        # Format results to match the original implementation
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i].get('metadata', {}),
                    # Convert distance to similarity score (1 - distance for cosine)
                    "similarity": 1 - results['distances'][0][i] if 'distances' in results and results['distances'][0] else 0.0
                })
        
        return formatted_results

# Initialize vector database singleton
vector_db = VectorDatabase()

# Models
class HiddenValueRequest(BaseModel):
    query: str
    problem_id: str

class HiddenValueResponse(BaseModel):
    hidden_values: Dict[str, Any]
    has_hidden_values: bool

class MaterialSearchRequest(BaseModel):
    query: str
    problem_id: str
    topic: Optional[str] = None
    limit: int = 3

class MaterialSearchResponse(BaseModel):
    results: List[Dict[str, Any]]

class StoreHiddenValueRequest(BaseModel):
    problem_id: str
    content: str
    metadata: Optional[Dict[str, Any]] = {}

class StoreTeachingMaterialRequest(BaseModel):
    topic: str
    content: str
    metadata: Optional[Dict[str, Any]] = {}

# Endpoints
@app.post("/store_hidden_value")
async def store_hidden_value(request: StoreHiddenValueRequest):
    """Store a hidden value in the vector database."""
    vector_db.store_hidden_value(
        problem_id=request.problem_id,
        content=request.content,
        metadata=request.metadata
    )
    return {"message": "Hidden value stored successfully"}

@app.post("/store_teaching_material")
async def store_teaching_material(request: StoreTeachingMaterialRequest):
    """Store a teaching material in the vector database."""
    vector_db.store_teaching_material(
        topic=request.topic,
        content=request.content,
        metadata=request.metadata
    )
    return {"message": "Teaching material stored successfully"}

@app.post("/search_hidden_values", response_model=HiddenValueResponse)
async def search_hidden_values(request: HiddenValueRequest):
    """Search for hidden values specific to a problem."""
    hidden_values = vector_db.search_hidden_values(
        problem_id=request.problem_id,
        query=request.query
    )
    return HiddenValueResponse(
        hidden_values=hidden_values,
        has_hidden_values=len(hidden_values) > 0
    )

@app.post("/search_materials", response_model=MaterialSearchResponse)
async def search_materials(request: MaterialSearchRequest):
    """Search for relevant teaching materials and resources."""
    results = vector_db.search_teaching_materials(
        query=request.query,
        topic=request.topic,
        limit=request.limit
    )
    return MaterialSearchResponse(results=results)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 