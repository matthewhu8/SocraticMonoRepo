from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from typing import Optional, Union

from ..database.database import get_db
from ..database.models import StudentUser, TeacherUser
from .utils import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> Union[StudentUser, TeacherUser]:
    """Get the current user from the JWT token.
    Can return either a student or teacher user."""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: Optional[int] = payload.get("sub")
        user_type: Optional[str] = payload.get("type")
        
        if user_id is None or user_type is None:
            raise credentials_exception
        
        # Check if it's a student or teacher
        if user_type == "student":
            user = db.query(StudentUser).filter(StudentUser.id == int(user_id)).first()
        elif user_type == "teacher":
            user = db.query(TeacherUser).filter(TeacherUser.id == int(user_id)).first()
        else:
            raise credentials_exception
        
        if user is None:
            raise credentials_exception
            
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )
            
        return user
    
    except JWTError:
        raise credentials_exception

async def get_current_student(
    current_user: Union[StudentUser, TeacherUser] = Depends(get_current_user)
) -> StudentUser:
    """Get the current student user, raising an exception if it's a teacher."""
    if not isinstance(current_user, StudentUser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a student user"
        )
    return current_user

async def get_current_teacher(
    current_user: Union[StudentUser, TeacherUser] = Depends(get_current_user)
) -> TeacherUser:
    """Get the current teacher user, raising an exception if it's a student."""
    if not isinstance(current_user, TeacherUser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a teacher user"
        )
    return current_user 