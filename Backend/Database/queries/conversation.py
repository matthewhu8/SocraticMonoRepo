from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from ..models import ChatMessage, QuestionResult

def create_chat_message(
    db: Session,
    question_result_id: int,
    sender: str,
    content: str
) -> ChatMessage:
    """Create a new chat message."""
    message = ChatMessage(
        question_result_id=question_result_id,
        sender=sender,
        content=content,
        timestamp=datetime.now()
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

def get_chat_messages(
    db: Session,
    question_result_id: int,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Get chat messages for a question result."""
    query = db.query(ChatMessage)\
              .filter(ChatMessage.question_result_id == question_result_id)\
              .order_by(ChatMessage.timestamp)
    
    if limit:
        query = query.limit(limit)
    
    messages = query.all()
    return [
        {
            'id': msg.id,
            'sender': msg.sender,
            'content': msg.content,
            'timestamp': msg.timestamp
        }
        for msg in messages
    ]

def create_question_result(
    db: Session,
    test_result_id: int,
    question_id: int,
    student_answer: Optional[str] = None,
    is_correct: bool = False,
    time_spent: Optional[int] = None
) -> QuestionResult:
    """Create a new question result."""
    now = datetime.now()
    result = QuestionResult(
        test_result_id=test_result_id,
        question_id=question_id,
        student_answer=student_answer,
        isCorrect=is_correct,
        time_spent=time_spent,
        start_time=now,
        end_time=now
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result

def update_question_result(
    db: Session,
    question_result_id: int,
    student_answer: Optional[str] = None,
    is_correct: Optional[bool] = None,
    time_spent: Optional[int] = None
) -> QuestionResult:
    """Update a question result."""
    result = db.query(QuestionResult).filter(QuestionResult.id == question_result_id).first()
    if not result:
        raise ValueError(f"Question result with id {question_result_id} not found")
    
    if student_answer is not None:
        result.student_answer = student_answer
    if is_correct is not None:
        result.isCorrect = is_correct
    if time_spent is not None:
        result.time_spent = time_spent
    
    result.end_time = datetime.now()
    db.commit()
    db.refresh(result)
    return result 