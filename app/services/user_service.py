from sqlalchemy.orm import Session
from app.models.user import User, ChatSession, ChatMessage
from app.schemas import UserCreate, ChatMessageCreate
from app.utils.auth import get_password_hash, verify_password
from typing import Optional, List

class UserService:
    @staticmethod
    def create_user(db: Session, user: UserCreate) -> User:
        """Create a new user."""
        hashed_password = get_password_hash(user.password)
        db_user = User(
            email=user.email,
            name=user.name,
            hashed_password=hashed_password
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email."""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user = UserService.get_user_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

class ChatService:
    @staticmethod
    def create_chat_session(db: Session, user_id: int, title: str = "New Chat") -> ChatSession:
        """Create a new chat session."""
        session = ChatSession(user_id=user_id, title=title)
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    
    @staticmethod
    def get_user_chat_sessions(db: Session, user_id: int) -> List[ChatSession]:
        """Get all chat sessions for a user."""
        return db.query(ChatSession).filter(ChatSession.user_id == user_id).order_by(ChatSession.updated_at.desc()).all()
    
    @staticmethod
    def add_message_to_session(db: Session, session_id: int, content: str, sender_type: str) -> ChatMessage:
        """Add a message to a chat session."""
        message = ChatMessage(
            session_id=session_id,
            content=content,
            sender_type=sender_type
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        
        # Update session's updated_at timestamp
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if session:
            from sqlalchemy import func
            session.updated_at = func.now()
            db.commit()
        
        return message
    
    @staticmethod
    def get_session_messages(db: Session, session_id: int) -> List[ChatMessage]:
        """Get all messages for a chat session."""
        return db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()
    
    @staticmethod
    def get_session_by_id(db: Session, session_id: int) -> Optional[ChatSession]:
        """Get chat session by ID."""
        return db.query(ChatSession).filter(ChatSession.id == session_id).first()
    
    @staticmethod
    def update_session_title(db: Session, session_id: int, title: str) -> Optional[ChatSession]:
        """Update chat session title."""
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if session:
            session.title = title
            db.commit()
            db.refresh(session)
        return session
