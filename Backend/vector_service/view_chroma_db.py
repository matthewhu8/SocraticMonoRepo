#!/usr/bin/env python3
"""
Script to view the contents of a local ChromaDB instance.
This script is for local development only.
"""
import os
import chromadb
from chromadb.config import Settings
from pprint import pprint
import sys

# Change this to your ChromaDB directory
CHROMA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")

def main():
    print(f"Connecting to ChromaDB at: {CHROMA_DIR}")
    
    # Initialize ChromaDB client with local persistence
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    
    # Get all collections
    collections = client.list_collections()
    
    if not collections:
        print("No collections found in the database.")
        return
    
    print(f"\nFound {len(collections)} collections:")
    for i, collection in enumerate(collections):
        print(f"\n{'='*50}")
        print(f"COLLECTION {i+1}: {collection.name}")
        print(f"{'='*50}")
        
        # Get collection details
        coll_details = client.get_collection(collection.name)
        
        # Get all documents (limit to 100 to avoid huge outputs)
        try:
            results = coll_details.get(limit=100)
            
            # Print collection stats
            doc_count = len(results['ids']) if results['ids'] else 0
            print(f"\nTotal documents: {doc_count}")
            
            if doc_count == 0:
                print("Collection is empty.")
                continue
                
            # Print some sample documents
            max_samples = min(5, doc_count)
            print(f"\nShowing {max_samples} sample documents:")
            
            for i in range(max_samples):
                print(f"\n--- Document {i+1} ---")
                print(f"ID: {results['ids'][i]}")
                
                # Print document content with truncation if too long
                doc_content = results['documents'][i]
                if isinstance(doc_content, str) and len(doc_content) > 200:
                    print(f"Content: {doc_content[:200]}... (truncated)")
                else:
                    print(f"Content: {doc_content}")
                
                # Print metadata
                print(f"Metadata: {results['metadatas'][i]}")
                
                # Optionally show embedding dimensions
                if 'embeddings' in results and results['embeddings']:
                    embedding = results['embeddings'][i]
                    print(f"Embedding: [{embedding[0]:.4f}, {embedding[1]:.4f}, ...] (dimension: {len(embedding)})")
            
            if doc_count > max_samples:
                print(f"\n... and {doc_count - max_samples} more documents")
        
        except Exception as e:
            print(f"Error accessing collection: {str(e)}")
    
    # Add a section for exploring with custom queries
    print("\n\n" + "="*50)
    print("INTERACTIVE QUERY SECTION")
    print("="*50)
    
    if not collections:
        return
        
    # List collections for selection
    print("\nAvailable collections:")
    for i, collection in enumerate(collections):
        print(f"{i+1}. {collection.name}")
    
    try:
        choice = input("\nEnter collection number to query (or 'q' to quit): ")
        if choice.lower() == 'q':
            return
            
        coll_index = int(choice) - 1
        if coll_index < 0 or coll_index >= len(collections):
            print("Invalid collection number.")
            return
            
        collection = client.get_collection(collections[coll_index].name)
        
        query = input("\nEnter search query: ")
        limit = input("Number of results to return (default: 5): ")
        limit = int(limit) if limit.isdigit() else 5
        
        # Perform query
        results = collection.query(
            query_texts=[query],
            n_results=limit,
            include=["documents", "metadatas", "distances"]
        )
        
        if not results['documents'][0]:
            print("\nNo results found.")
            return
            
        print(f"\nFound {len(results['documents'][0])} results:")
        
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0], 
            results['metadatas'][0], 
            results['distances'][0]
        )):
            print(f"\n--- Result {i+1} (Distance: {distance:.4f}) ---")
            
            # Print document content with truncation if too long
            if isinstance(doc, str) and len(doc) > 200:
                print(f"Content: {doc[:200]}... (truncated)")
            else:
                print(f"Content: {doc}")
            
            # Print metadata
            print(f"Metadata: {metadata}")
            
    except Exception as e:
        print(f"Error during interactive query: {str(e)}")

if __name__ == "__main__":
    main()