from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..models import Test, Question, TestQuestion

def create_test(db: Session, name: str, code: str, questions: List[Dict[str, Any]]) -> Dict:
    """Create a new test with the given code and questions."""
    existing_test = db.query(Test).filter(Test.code == code).first()
    if existing_test:
        raise ValueError(f"Test with code '{code}' already exists")
    
    # Create new test record
    test_record = Test(test_name=name, code=code)
    db.add(test_record)
    db.flush()  # Flush to get the test_id
    
    # Create questions and link them to the test
    for idx, q_data in enumerate(questions):
        question = Question(
            public_question=q_data['public_question'],
            hidden_values=q_data.get('hidden_values', {}),
            answer=q_data['answer'],
            teacher_instructions=q_data.get('teacher_instructions'),
            subject=q_data.get('subject'),
            topic=q_data.get('topic')
        )
        db.add(question)
        db.flush()  # Flush to get the question_id
        
        # Create test_question link with position
        test_question = TestQuestion(
            test_id=test_record.id,
            question_id=question.id,
            position=idx
        )
        db.add(test_question)
    
    db.commit()
    return {"id": test_record.id, "code": test_record.code}

def get_test_by_code(db: Session, code: str) -> Optional[Dict]:
    """Retrieve a test by its code."""
    test = db.query(Test).filter(Test.code == code).first()
    if not test:
        return None
    
    # Get questions ordered by position
    questions_data = []
    for q in db.query(Question, TestQuestion)\
               .join(TestQuestion, Question.id == TestQuestion.question_id)\
               .filter(TestQuestion.test_id == test.id)\
               .order_by(TestQuestion.position)\
               .all():
        question, test_question = q
        questions_data.append({
            'id': question.id,
            'public_question': question.public_question,
            'hidden_values': question.hidden_values,
            'answer': question.answer,
            'teacher_instructions': question.teacher_instructions,
            'subject': question.subject,
            'topic': question.topic
        })
    
    return {
        "id": test.id,
        "code": test.code,
        "name": test.test_name,
        "questions": questions_data
    }

def get_test_question(db: Session, test_code: str, question_index: int) -> Optional[Dict]:
    """Get a specific question from a test."""
    try:
        idx = int(question_index)
    except (ValueError, TypeError):
        return None
    
    # Get the question at the specified position
    result = db.query(Question)\
              .join(TestQuestion, Question.id == TestQuestion.question_id)\
              .join(Test, Test.id == TestQuestion.test_id)\
              .filter(Test.code == test_code)\
              .filter(TestQuestion.position == idx)\
              .first()
    
    if not result:
        return None
    
    return {
        'id': result.id,
        'public_question': result.public_question,
        'hidden_values': result.hidden_values,
        'answer': result.answer,
        'teacher_instructions': result.teacher_instructions,
        'subject': result.subject,
        'topic': result.topic
    } 