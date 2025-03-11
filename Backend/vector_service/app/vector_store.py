import os
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import annoy
import json

class VectorStore:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorStore, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.dimension = 384  # Dimension of the embeddings
            self.index = annoy.AnnoyIndex(self.dimension, 'angular')
            self.metadata_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'vector_store', 'metadata.json')
            self.index_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'vector_store', 'index.ann')
            
            # Create data directory if it doesn't exist
            os.makedirs(os.path.dirname(self.metadata_file), exist_ok=True)
            
            # Load existing data if available
            self.metadata = self._load_metadata()
            self._load_index()
            self._initialized = True

    def _load_metadata(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_metadata(self):
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f)

    def _load_index(self):
        if os.path.exists(self.index_file):
            self.index.load(self.index_file)

    def _save_index(self):
        self.index.save(self.index_file)

    def store_problem(self, problem_id: str, text: str, metadata: Dict[str, Any]):
        """Store a problem in the vector database."""
        # Generate embedding
        embedding = self.model.encode(text)
        
        # Add to index
        self.index.add_item(len(self.metadata), embedding)
        
        # Store metadata
        self.metadata[problem_id] = {
            'text': text,
            'metadata': metadata,
            'index': len(self.metadata) - 1
        }
        
        # Save to disk
        self._save_metadata()
        self._save_index()

    def find_similar_problems(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find similar problems using a text query."""
        # Generate query embedding
        query_embedding = self.model.encode(query)
        
        # Find nearest neighbors
        nearest_neighbors = self.index.get_nns_by_vector(
            query_embedding, 
            limit, 
            include_distances=True
        )
        
        # Get results with metadata
        results = []
        for idx, distance in zip(nearest_neighbors[0], nearest_neighbors[1]):
            for problem_id, data in self.metadata.items():
                if data['index'] == idx:
                    results.append({
                        'id': problem_id,
                        'text': data['text'],
                        'metadata': data['metadata'],
                        'similarity_score': 1 - (distance / 2)  # Convert distance to similarity score
                    })
                    break
        
        return results

    def find_similar_problems_by_id(self, problem_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find similar problems using a problem ID."""
        if problem_id not in self.metadata:
            raise ValueError(f"Problem ID {problem_id} not found")
            
        problem_data = self.metadata[problem_id]
        problem_embedding = self.model.encode(problem_data['text'])
        
        # Find nearest neighbors
        nearest_neighbors = self.index.get_nns_by_vector(
            problem_embedding, 
            limit + 1,  # +1 because the problem itself will be included
            include_distances=True
        )
        
        # Get results with metadata
        results = []
        for idx, distance in zip(nearest_neighbors[0], nearest_neighbors[1]):
            for pid, data in self.metadata.items():
                if data['index'] == idx:
                    results.append({
                        'id': pid,
                        'text': data['text'],
                        'metadata': data['metadata'],
                        'similarity_score': 1 - (distance / 2)  # Convert distance to similarity score
                    })
                    break
        
        # Remove the problem itself from results
        results = [r for r in results if r['id'] != problem_id]
        return results[:limit] 