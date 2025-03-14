from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import os
import json
from threading import Lock
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
from datetime import datetime

app = FastAPI(title="Vector Service")

# Initialize the model
model = SentenceTransformer('all-MiniLM-L6-v2')
DIMENSION = 384  # Dimension of the embeddings

# Milvus connection settings
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = int(os.getenv("MILVUS_PORT", "19530"))

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
                    # Connect to Milvus
                    connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
                    
                    # Initialize collections if they don't exist
                    self._init_collections()
                    self._initialized = True

    def _init_collections(self):
        """Initialize Milvus collections for hidden values and teaching materials."""
        # Hidden Values Collection Schema
        hidden_values_fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="problem_id", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=DIMENSION),
            FieldSchema(name="created_at", dtype=DataType.INT64),
            FieldSchema(name="metadata", dtype=DataType.JSON)
        ]
        hidden_values_schema = CollectionSchema(
            fields=hidden_values_fields,
            description="Collection for storing hidden values and their embeddings"
        )

        # Teaching Materials Collection Schema
        teaching_materials_fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="topic", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=DIMENSION),
            FieldSchema(name="created_at", dtype=DataType.INT64),
            FieldSchema(name="metadata", dtype=DataType.JSON)
        ]
        teaching_materials_schema = CollectionSchema(
            fields=teaching_materials_fields,
            description="Collection for storing teaching materials and their embeddings"
        )

        # Create collections if they don't exist
        if not utility.has_collection(HIDDEN_VALUES_COLLECTION):
            self.hidden_values = Collection(
                name=HIDDEN_VALUES_COLLECTION,
                schema=hidden_values_schema
            )
            self.hidden_values.create_index(
                field_name="embedding",
                index_params={"metric_type": "COSINE", "index_type": "IVF_FLAT", "params": {"nlist": 1024}}
            )
        else:
            self.hidden_values = Collection(name=HIDDEN_VALUES_COLLECTION)

        if not utility.has_collection(TEACHING_MATERIALS_COLLECTION):
            self.teaching_materials = Collection(
                name=TEACHING_MATERIALS_COLLECTION,
                schema=teaching_materials_schema
            )
            self.teaching_materials.create_index(
                field_name="embedding",
                index_params={"metric_type": "COSINE", "index_type": "IVF_FLAT", "params": {"nlist": 1024}}
            )
        else:
            self.teaching_materials = Collection(name=TEACHING_MATERIALS_COLLECTION)

    def store_hidden_value(self, problem_id: str, content: str, metadata: Dict[str, Any]):
        """Store a hidden value with its embedding."""
        embedding = model.encode(content)
        entities = [
            [problem_id],
            [content],
            [embedding.tolist()],
            [int(datetime.now().timestamp())],
            [metadata]
        ]
        self.hidden_values.insert(entities)
        self.hidden_values.flush()

    def store_teaching_material(self, topic: str, content: str, metadata: Dict[str, Any]):
        """Store a teaching material with its embedding."""
        embedding = model.encode(content)
        entities = [
            [topic],
            [content],
            [embedding.tolist()],
            [int(datetime.now().timestamp())],
            [metadata]
        ]
        self.teaching_materials.insert(entities)
        self.teaching_materials.flush()

    def search_hidden_values(self, problem_id: str, query: str, limit: int = 5) -> Dict[str, Any]:
        """Search for hidden values specific to a problem."""
        self.hidden_values.load()
        query_embedding = model.encode(query)
        
        # Search for similar vectors
        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10}
        }
        results = self.hidden_values.search(
            data=[query_embedding.tolist()],
            anns_field="embedding",
            param=search_params,
            limit=1,  # We only need the best match for this problem
            output_fields=["metadata"],
            expr=f'problem_id == "{problem_id}"'
        )
        
        # Get the hidden values from the best match
        hits = results[0]
        if hits:
            hit = hits[0]  # Get the best match
            return hit.entity.get('metadata', {}).get('hidden_values', {})
        return {}

    def search_teaching_materials(self, query: str, topic: Optional[str] = None, limit: int = 3) -> List[Dict[str, Any]]:
        """Search for relevant teaching materials."""
        self.teaching_materials.load()
        query_embedding = model.encode(query)
        
        # Build search expression
        expr = f'topic == "{topic}"' if topic else None
        
        # Search for similar vectors
        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10}
        }
        results = self.teaching_materials.search(
            data=[query_embedding.tolist()],
            anns_field="embedding",
            param=search_params,
            limit=limit,
            output_fields=["topic", "content", "metadata", "created_at"],
            expr=expr
        )
        
        # Format results
        formatted_results = []
        for hits in results:
            for hit in hits:
                formatted_results.append({
                    "content": hit.entity.get('content'),
                    "metadata": hit.entity.get('metadata'),
                    "similarity": float(hit.score)
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