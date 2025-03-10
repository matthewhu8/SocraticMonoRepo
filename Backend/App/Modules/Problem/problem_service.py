import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from Database.queries.test import create_test, get_test_by_code, get_test_question # type: ignore

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
        return create_test(db, name, code, questions)
    
    def get_test_by_code(self, db: Session, code: str) -> Optional[Dict]:
        """
        Retrieve a test by its code.
        
        Args:
            db: Database session
            code: Test code to look up
            
        Returns:
            Test data as dictionary or None if not found
        """
        return get_test_by_code(db, code)
    
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
        return get_test_question(db, test_code, question_index)