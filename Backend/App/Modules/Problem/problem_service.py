import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ...db.models import Test

class ProblemService:
    def create_test(self, db: Session, name: str, code: str, questions: List[Dict[str, Any]]) -> Dict:
        """
        Create a new test with the given code and questions.
        
        Args:
            db: Database session
            name: Test name
            code: Unique test code
            questions: List of question dictionaries
            
        Returns:
            Dict containing test info
        
        Raises:
            ValueError: If test code already exists
        """
        # Check if test code already exists
        print("create test called in problem service")
        try:
            existing_test = db.query(Test).filter(Test.code == code).first()
            if existing_test:
                raise ValueError(f"Test with code '{code}' already exists")
            
            # Create new test record
            test_record = Test(test_name=name, code=code, questions=json.dumps(questions))
            db.add(test_record)
            db.commit()
            db.refresh(test_record)
            
            return {"id": test_record.id, "code": test_record.code}
        except Exception as e:
            # Check if the error is due to missing name column
            if "no such column: tests.name" in str(e):
                print("Warning: 'name' column not found in tests table. Using alternative approach.")
                # Try creating the test without the name column
                from sqlalchemy.sql import text
                try:
                    # First check if test exists
                    result = db.execute(text("SELECT id FROM tests WHERE code = :code"), {"code": code})
                    if result.fetchone():
                        raise ValueError(f"Test with code '{code}' already exists")
                    
                    # Insert without name column
                    result = db.execute(
                        text("INSERT INTO tests (code, questions) VALUES (:code, :questions)"),
                        {"code": code, "questions": json.dumps(questions)}
                    )
                    db.commit()
                    
                    # Get the created record ID
                    result = db.execute(text("SELECT id FROM tests WHERE code = :code"), {"code": code})
                    test_id = result.fetchone()[0]
                    
                    return {"id": test_id, "code": code}
                except Exception as inner_e:
                    db.rollback()
                    print(f"Error in fallback method: {inner_e}")
                    raise inner_e
            else:
                # Re-raise other exceptions
                raise e
        
    def get_test_by_code(self, db: Session, code: str) -> Optional[Dict]:
        """
        Retrieve a test by its code.
        
        Args:
            db: Database session
            code: Test code to look up
            
        Returns:
            Test data as dictionary or None if not found
        """
        print("get test by code called in problem service")
        test = db.query(Test).filter(Test.code == code).first()
        if not test:
            return None
        
        print("test found", test)
        return {
            "id": test.id,
            "code": test.code,
            "questions": json.loads(test.questions),
            "name": test.test_name
        }
    
    def get_test_question(self, db: Session, test_code: str, question_index: int) -> Optional[Dict]:
        """
        Get a specific question from a test
        
        Args:
            db: Database session
            test_code: Test code
            question_index: Index of the question in the test (0-based)
            
        Returns:
            Dict containing question data or None if not found
        """
        print(f"Getting question at index {question_index} from test {test_code}")
        
        # Convert question_index to int if it's a string
        try:
            idx = int(question_index)
        except (ValueError, TypeError):
            print(f"Invalid question index: {question_index}")
            return None
        
        # Get the test by code
        test = self.get_test_by_code(db, test_code)
        if not test:
            print(f"Test not found with code: {test_code}")
            return None
        
        # Get questions from the test
        questions = test.get("questions", [])
        if not questions or idx < 0 or idx >= len(questions):
            print(f"Question index {idx} out of range (0-{len(questions)-1})" if questions else "No questions in test")
            return None
        
        # Return the question at the specified index
        question = questions[idx]
        print(f"Found question: {question.get('public_question') or question.get('publicQuestion', 'No question text')[:50]}...")
        return question