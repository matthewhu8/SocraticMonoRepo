#!/usr/bin/env python3
"""
Test script to verify ChromaDB connection and functionality.
"""
from app.VectorDatabase import vector_db
import os
import uuid

# Check if chroma_db directory exists
CHROMA_DIR = "./chroma_db"
print(f"Checking for ChromaDB directory at: {os.path.abspath(CHROMA_DIR)}")
if os.path.exists(CHROMA_DIR):
    print(f"✅ ChromaDB directory exists")
else:
    print(f"❌ ChromaDB directory does not exist, it will be created during testing")

# Generate a unique test ID
test_id = str(uuid.uuid4())[:8]
print(f"\nRunning test with ID: {test_id}")

# Test 1: Store and retrieve a problem
test_problem = f"This is a test problem {test_id}"
test_metadata = {"topic": "testing", "subject": "vectors"}

print("\n1. Testing problem storage...")
try:
    vector_db.store_problem(
        problem_id=f"test-{test_id}",
        content=test_problem,
        metadata=test_metadata
    )
    print("✅ Problem stored successfully")
except Exception as e:
    print(f"❌ Error storing problem: {str(e)}")

# Test 2: Search for the problem
print("\n2. Testing problem retrieval...")
try:
    results = vector_db.search_problems(
        query=f"test problem {test_id}", 
        limit=1
    )
    
    if results and len(results) > 0:
        print("✅ Problem retrieved successfully")
        print(f"   Result: {results[0]}")
    else:
        print("❌ Problem not found in search results")
except Exception as e:
    print(f"❌ Error searching for problem: {str(e)}")

# Test 3: Store and retrieve a hidden value
print("\n3. Testing hidden value storage...")
try:
    vector_db.store_hidden_value(
        problem_id=f"test-{test_id}",
        hidden_value=f"x={test_id}"
    )
    print("✅ Hidden value stored successfully")
except Exception as e:
    print(f"❌ Error storing hidden value: {str(e)}")

# Test 4: Store and retrieve teaching material
print("\n4. Testing teaching material storage...")
try:
    vector_db.store_teaching_material(
        topic="testing",
        content=f"This is test teaching material {test_id}",
        metadata={"source": "test script"}
    )
    print("✅ Teaching material stored successfully")
except Exception as e:
    print(f"❌ Error storing teaching material: {str(e)}")

print("\n5. Testing teaching material retrieval...")
try:
    results = vector_db.search_teaching_materials(
        query=f"test teaching material {test_id}",
        limit=1
    )
    
    if results and len(results) > 0:
        print("✅ Teaching material retrieved successfully")
        print(f"   Result: {results[0]}")
    else:
        print("❌ Teaching material not found in search results")
except Exception as e:
    print(f"❌ Error searching for teaching material: {str(e)}")

print("\nChromaDB Test Summary:")
print("=====================")
print("✅ Test completed - check the results above for any issues")
print(f"ChromaDB location: {os.path.abspath(CHROMA_DIR)}")
print("To view the data, you can use Chroma's Python client API or a visualization tool") 