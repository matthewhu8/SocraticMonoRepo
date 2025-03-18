from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
from VectorDatabase import vector_db

app = FastAPI(title="Vector Service")

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
    hidden_value: str

class StoreProblemRequest(BaseModel):
    problem_id: str
    text: str
    metadata: Optional[Dict[str, Any]] = {}

class StoreTeachingMaterialRequest(BaseModel):
    topic: str
    content: str
    metadata: Optional[Dict[str, Any]] = {}

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]

# Endpoints
@app.post("/problems/")
async def store_problem(request: StoreProblemRequest):
    """Store a problem in the vector database."""
    vector_db.store_problem(
        problem_id=request.id,
        content=request,
        metadata=request.metadata
    )
    return {"message": "Problem stored successfully"}

@app.post("/store_hidden_value")
async def store_hidden_value(request: StoreHiddenValueRequest):
    """Store a hidden value in the vector database."""
    vector_db.store_hidden_value(
        problem_id=request.problem_id,
        hidden_value=request.hidden_value
    )
    return {"message": "Hidden value stored successfully"}

@app.get("/problems/{problem_id}/similar")
async def get_similar_problems(problem_id: str, limit: int = 5):
    """Find problems similar to the given problem ID."""
    results = vector_db.find_similar_problems_by_id(problem_id, limit)
    return {"results": results}

@app.get("/problems/{problem_id}/topic")
async def get_problem_topic(problem_id: str):
    """Get the topic of a specific problem."""
    return vector_db.get_problem_topic(problem_id)

@app.post("/search")
async def search_problems(query: str, n_results: int = 5):
    """Search for problems similar to the query."""
    results = vector_db.search_problems(query, n_results)
    return results

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