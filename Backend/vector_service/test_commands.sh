#!/bin/bash

# Test 1: Store Hidden Value
echo "Testing store_hidden_value endpoint..."
curl -X POST http://localhost:8002/store_hidden_value \
  -H "Content-Type: application/json" \
  -d '{
    "problem_id": "algebra_101_1",
    "content": "What is the value of x in the equation x + 2y = 30?",
    "metadata": {
      "test_code": "algebra_101",
      "question_id": 1,
      "answer": "x = 3",
      "subject": "mathematics",
      "topic": "linear_equations",
      "hidden_values": {
        "answer": "x = 3",
        "hint1": "Solve for x in terms of y",
        "hint2": "When y = 13.5, what is x?"
      }
    }
  }'

echo -e "\n\n# Test 2: Search Hidden Values"
echo "Testing search_hidden_values endpoint..."
curl -X POST http://localhost:8002/search_hidden_values \
  -H "Content-Type: application/json" \
  -d '{
    "problem_id": "algebra_101_1",
    "query": "How do I find x in the equation?"
  }'

echo -e "\n\n# Test 3: Store Problem"
echo "Testing /problems/ endpoint..."
curl -X POST http://localhost:8002/problems/ \
  -H "Content-Type: application/json" \
  -d '{
    "id": "algebra_101_1",
    "text": "What is the value of x in the equation x + 2y = 30?",
    "metadata": {
      "test_code": "algebra_101",
      "question_id": 1,
      "answer": "x = 3",
      "subject": "mathematics",
      "topic": "linear_equations",
      "hidden_values": {
        "answer": "x = 3",
        "hint1": "Solve for x in terms of y",
        "hint2": "When y = 13.5, what is x?"
      }
    }
  }'

echo -e "\n\n# Test 4: Get Similar Problems"
echo "Testing /problems/{problem_id}/similar endpoint..."
curl -X GET "http://localhost:8002/problems/algebra_101_1/similar?limit=2" \
  -H "Content-Type: application/json"

echo -e "\n\n# Test 5: Get Problem Topic"
echo "Testing /problems/{problem_id}/topic endpoint..."
curl -X GET "http://localhost:8002/problems/algebra_101_1/topic" \
  -H "Content-Type: application/json"

echo -e "\n\n# Test 6: Store Teaching Material"
echo "Testing store_teaching_material endpoint..."
curl -X POST http://localhost:8002/store_teaching_material \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "linear_equations",
    "content": "Linear equations with two variables can be solved by isolating one variable. For example, in x + 2y = 30, we can isolate x as x = 30 - 2y.",
    "metadata": {
      "grade_level": "middle_school",
      "author": "Math Teacher",
      "subject": "mathematics"
    }
  }'

echo -e "\n\n# Test 7: Search Materials"
echo "Testing search_materials endpoint..."
curl -X POST http://localhost:8002/search_materials \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How to solve for x in linear equations",
    "problem_id": "algebra_101_1",
    "topic": "linear_equations",
    "limit": 2
  }' 