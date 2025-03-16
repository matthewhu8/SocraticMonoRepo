from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
from datetime import datetime
from threading import Lock
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document

app = FastAPI(title="Vector Service")

# Settings
CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
MODEL_NAME = 'all-MiniLM-L6-v2'

# Collection names
HIDDEN_VALUES_COLLECTION = "hidden_values"
TEACHING_MATERIALS_COLLECTION = "teaching_materials"
PROBLEMS_COLLECTION = "problems"

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
                        # Initialize embedding function
                        self.embeddings = SentenceTransformerEmbeddings(
                            model_name=MODEL_NAME
                        )
                        
                        # Initialize vector stores for different collections
                        self.hidden_values = Chroma(
                            collection_name=HIDDEN_VALUES_COLLECTION,
                            embedding_function=self.embeddings,
                            persist_directory=CHROMA_PERSIST_DIRECTORY
                        )
                        
                        self.teaching_materials = Chroma(
                            collection_name=TEACHING_MATERIALS_COLLECTION,
                            embedding_function=self.embeddings,
                            persist_directory=CHROMA_PERSIST_DIRECTORY
                        )
                        
                        self.problems = Chroma(
                            collection_name=PROBLEMS_COLLECTION,
                            embedding_function=self.embeddings,
                            persist_directory=CHROMA_PERSIST_DIRECTORY
                        )
                        
                        self._initialized = True
                    except Exception as e:
                        print(f"Failed to initialize vector stores: {str(e)}")
                        raise

    def store_hidden_value(self, problem_id: str, content: str, metadata: Dict[str, Any]):
        """Store a hidden value with its embedding."""
        # Create a LangChain Document
        document = Document(
            page_content=content,
            metadata={
                "problem_id": problem_id,
                "created_at": int(datetime.now().timestamp()),
                **metadata  # Include all other metadata
            }
        )
        
        # Add document to Chroma
        self.hidden_values.add_documents([document])

    def store_problem(self, problem_id: str, content: str, metadata: Dict[str, Any]):
        """Store a problem with its embedding."""
        # Create a LangChain Document
        document = Document(
            page_content=content,
            metadata={
                "problem_id": problem_id,
                "created_at": int(datetime.now().timestamp()),
                **metadata  # Include all other metadata
            }
        )
        
        # Add document to Chroma
        self.problems.add_documents([document])

    def store_teaching_material(self, topic: str, content: str, metadata: Dict[str, Any]):
        """Store a teaching material with its embedding."""
        document = Document(
            page_content=content,
            metadata={
                "topic": topic,
                "created_at": int(datetime.now().timestamp()),
                **metadata
            }
        )
        
        self.teaching_materials.add_documents([document])

    def search_hidden_values(self, problem_id: str, query: str, limit: int = 5) -> Dict[str, Any]:
        """Search for hidden values specific to a problem."""
        # Create filter for specific problem_id
        filter_dict = {"problem_id": problem_id}
        
        # Perform similarity search with metadata filter
        results = self.hidden_values.similarity_search_with_score(
            query,
            k=1,  # Original code only returns the best match
            filter=filter_dict
        )
        
        if results:
            doc, score = results[0]
            # Return hidden_values from metadata
            return doc.metadata.get("hidden_values", {})
        return {}

    def search_problems(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for problems similar to the query."""
        # Perform similarity search
        results = self.problems.similarity_search_with_score(
            query,
            k=limit
        )
        
        # Format results
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "id": doc.metadata.get("problem_id", ""),
                "text": doc.page_content,
                "metadata": {k: v for k, v in doc.metadata.items() if k not in ["problem_id", "created_at"]},
                "similarity_score": 1 - (score / 2)  # Convert distance to similarity score
            })
        
        return formatted_results

    def find_similar_problems_by_id(self, problem_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find problems similar to the given problem ID."""
        # Get the problem document
        filter_dict = {"problem_id": problem_id}
        results = self.problems.similarity_search_with_score(
            "",  # Empty query to get exact match
            k=1,
            filter=filter_dict
        )
        
        if not results:
            return []
            
        # Use the content of the found problem as query
        doc, _ = results[0]
        query_text = doc.page_content
        
        # Search for similar problems excluding the original
        similar_results = self.problems.similarity_search_with_score(
            query_text,
            k=limit + 1  # +1 to account for the original problem
        )
        
        # Format and filter results
        formatted_results = []
        for doc, score in similar_results:
            # Skip the original problem
            if doc.metadata.get("problem_id") == problem_id:
                continue
                
            formatted_results.append({
                "id": doc.metadata.get("problem_id", ""),
                "text": doc.page_content,
                "metadata": {k: v for k, v in doc.metadata.items() if k not in ["problem_id", "created_at"]},
                "similarity_score": 1 - (score / 2)  # Convert distance to similarity score
            })
        
        return formatted_results[:limit]

    def get_problem_topic(self, problem_id: str) -> Dict[str, Any]:
        """Get the topic of a specific problem."""
        filter_dict = {"problem_id": problem_id}
        results = self.problems.similarity_search_with_score(
            "",  # Empty query to get exact match
            k=1,
            filter=filter_dict
        )
        
        if results:
            doc, _ = results[0]
            return {
                "topic": doc.metadata.get("topic", ""),
                "subject": doc.metadata.get("subject", "")
            }
        return {"topic": "", "subject": ""}

    def search_teaching_materials(self, query: str, topic: Optional[str] = None, limit: int = 3) -> List[Dict[str, Any]]:
        """Search for relevant teaching materials."""
        # Create filter if topic is provided
        filter_dict = {"topic": topic} if topic else None
        
        # Perform similarity search with optional filter
        results = self.teaching_materials.similarity_search_with_score(
            query,
            k=limit,
            filter=filter_dict
        )
        
        # Format results
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "content": doc.page_content,
                "metadata": {k: v for k, v in doc.metadata.items() if k not in ["topic", "created_at"]},
                "similarity": 1 - (score / 2)  # Convert distance to similarity score
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

class StoreProblemRequest(BaseModel):
    id: str
    text: str
    metadata: Optional[Dict[str, Any]] = {}

class StoreTeachingMaterialRequest(BaseModel):
    topic: str
    content: str
    metadata: Optional[Dict[str, Any]] = {}

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]

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

@app.post("/problems/")
async def store_problem(request: StoreProblemRequest):
    """Store a problem in the vector database."""
    vector_db.store_problem(
        problem_id=request.id,
        content=request.text,
        metadata=request.metadata
    )
    return {"message": "Problem stored successfully"}

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