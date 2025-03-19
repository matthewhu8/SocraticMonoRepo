#!/usr/bin/env python3
"""
Simple script to view the contents of ChromaDB using your existing VectorDatabase implementation.
"""
from app.VectorDatabase import vector_db
import os

# Path where ChromaDB is stored
CHROMA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
print(f"ChromaDB location: {CHROMA_DIR}")

def print_separator(title):
    print(f"\n{'='*50}")
    print(f" {title}")
    print(f"{'='*50}")

# Function to show collection contents
def show_collection(collection, name):
    print_separator(f"COLLECTION: {name}")
    
    try:
        # Get all documents using your existing functions
        if name == "problems":
            # Use the search function to get all problems
            results = vector_db.search_problems("", limit=100)
            
            if not results:
                print(f"No documents found in {name} collection.")
                return
                
            print(f"Found {len(results)} documents:")
            for i, result in enumerate(results[:5]):  # Show first 5
                print(f"\n--- Document {i+1} ---")
                print(f"ID: {result.get('id', 'N/A')}")
                
                # Print document content with truncation if too long
                content = result.get('text', '')
                if len(content) > 200:
                    print(f"Content: {content[:200]}... (truncated)")
                else:
                    print(f"Content: {content}")
                
                # Print metadata
                print(f"Metadata: {result.get('metadata', {})}")
                print(f"Similarity Score: {result.get('similarity_score', 'N/A')}")
            
            if len(results) > 5:
                print(f"\n... and {len(results) - 5} more documents")
                
        elif name == "teaching_materials":
            # Use the search function to get teaching materials
            results = vector_db.search_teaching_materials("", limit=100)
            
            if not results:
                print(f"No documents found in {name} collection.")
                return
                
            print(f"Found {len(results)} documents:")
            for i, result in enumerate(results[:5]):  # Show first 5
                print(f"\n--- Document {i+1} ---")
                
                # Print document content with truncation if too long
                content = result.get('content', '')
                if len(content) > 200:
                    print(f"Content: {content[:200]}... (truncated)")
                else:
                    print(f"Content: {content}")
                
                # Print metadata
                print(f"Metadata: {result.get('metadata', {})}")
                print(f"Similarity: {result.get('similarity', 'N/A')}")
            
            if len(results) > 5:
                print(f"\n... and {len(results) - 5} more documents")
                
        else:
            print(f"Collection '{name}' view not implemented.")
            
    except Exception as e:
        print(f"Error accessing collection: {str(e)}")

# Interactive search function
def interactive_search():
    print_separator("INTERACTIVE SEARCH")
    print("1. Search problems")
    print("2. Search teaching materials")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ")
    
    if choice == "1":
        query = input("Enter search query for problems: ")
        limit = input("Number of results (default: 5): ")
        limit = int(limit) if limit.strip().isdigit() else 5
        
        print("\nSearching problems...")
        results = vector_db.search_problems(query, limit=limit)
        
        if not results:
            print("No results found.")
            return
            
        print(f"Found {len(results)} results:")
        for i, result in enumerate(results):
            print(f"\n--- Result {i+1} ---")
            print(f"ID: {result.get('id', 'N/A')}")
            
            # Print document content with truncation if too long
            content = result.get('text', '')
            if len(content) > 200:
                print(f"Content: {content[:200]}... (truncated)")
            else:
                print(f"Content: {content}")
            
            # Print metadata
            print(f"Metadata: {result.get('metadata', {})}")
            print(f"Similarity Score: {result.get('similarity_score', 'N/A')}")
            
    elif choice == "2":
        query = input("Enter search query for teaching materials: ")
        limit = input("Number of results (default: 5): ")
        limit = int(limit) if limit.strip().isdigit() else 5
        
        print("\nSearching teaching materials...")
        results = vector_db.search_teaching_materials(query, limit=limit)
        
        if not results:
            print("No results found.")
            return
            
        print(f"Found {len(results)} results:")
        for i, result in enumerate(results):
            print(f"\n--- Result {i+1} ---")
            
            # Print document content with truncation if too long
            content = result.get('content', '')
            if len(content) > 200:
                print(f"Content: {content[:200]}... (truncated)")
            else:
                print(f"Content: {content}")
            
            # Print metadata
            print(f"Metadata: {result.get('metadata', {})}")
            print(f"Similarity: {result.get('similarity', 'N/A')}")
            
    elif choice == "3":
        return
    else:
        print("Invalid choice.")

def main():
    print("\nViewing ChromaDB contents using your existing VectorDatabase...")
    
    # Show all collections
    print_separator("COLLECTIONS")
    collections = ["problems", "teaching_materials", "hidden_values"]
    print(f"Available collections: {', '.join(collections)}")
    
    # Show contents of each collection
    show_collection(vector_db.problems, "problems")
    show_collection(vector_db.teaching_materials, "teaching_materials")
    
    # Interactive search
    while True:
        interactive_search()
        
        continue_search = input("\nDo you want to perform another search? (y/n): ")
        if continue_search.lower() != 'y':
            break

if __name__ == "__main__":
    main() 