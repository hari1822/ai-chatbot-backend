from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas import ChatSessionResponse, ChatMessageCreate, ChatMessageResponse, APIResponse
from app.services import ChatService, openrouter_service
from app.routes.auth import get_current_user_dependency, UserResponse
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])

@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_chat_sessions(
    current_user: UserResponse = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get all chat sessions for the current user."""
    try:
        sessions = ChatService.get_user_chat_sessions(db, current_user.id)
        return [ChatSessionResponse.model_validate(session) for session in sessions]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch chat sessions"
        )

@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    title: str = "New Chat",
    current_user: UserResponse = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Create a new chat session."""
    try:
        session = ChatService.create_chat_session(db, current_user.id, title)
        return ChatSessionResponse.model_validate(session)
    
    except Exception as e:
        logger.error(f"Failed to create chat session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create chat session"
        )

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_session_messages(
    session_id: int,
    current_user: UserResponse = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get all messages for a specific chat session."""
    try:
        # Verify session belongs to user
        session = ChatService.get_session_by_id(db, session_id)
        if not session or session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        messages = ChatService.get_session_messages(db, session_id)
        return [ChatMessageResponse.model_validate(message) for message in messages]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch messages"
        )

@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
async def send_message(
    session_id: int,
    message: ChatMessageCreate,
    current_user: UserResponse = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Send a message to a chat session and get AI response."""
    try:
        # Verify session belongs to user
        session = ChatService.get_session_by_id(db, session_id)
        if not session or session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        # Add user message to database
        user_message = ChatService.add_message_to_session(
            db, session_id, message.content, "user"
        )
        
        # Get previous messages for context
        previous_messages = ChatService.get_session_messages(db, session_id)
        
        # Generate title for the chat if this is the first user message
        user_messages_count = len([msg for msg in previous_messages if msg.sender_type == "user"])
        if user_messages_count == 1:  # This is the first user message
            try:
                new_title = await openrouter_service.generate_chat_title(message.content)
                ChatService.update_session_title(db, session_id, new_title)
                logger.info(f"Updated session {session_id} title to: {new_title}")
            except Exception as e:
                logger.error(f"Failed to generate title for session {session_id}: {e}")
        
        # Format messages for OpenRouter API
        formatted_messages = openrouter_service.format_messages_for_api(previous_messages)
        
        # Generate AI response using OpenRouter
        logger.info(f"Generating AI response for session {session_id} with {len(formatted_messages)} messages")
        ai_response_text = await openrouter_service.generate_response(formatted_messages)
        
        # Add AI response to database
        ai_message = ChatService.add_message_to_session(
            db, session_id, ai_response_text, "bot"
        )
        
        logger.info(f"Successfully generated AI response for session {session_id}")
        return ChatMessageResponse.model_validate(ai_message)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send message to session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send message"
        )

@router.delete("/sessions/{session_id}", response_model=APIResponse)
async def delete_chat_session(
    session_id: int,
    current_user: UserResponse = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Delete a chat session."""
    try:
        # Verify session belongs to user
        session = ChatService.get_session_by_id(db, session_id)
        if not session or session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        # Delete session (this will cascade delete messages)
        db.delete(session)
        db.commit()
        
        return APIResponse(
            success=True,
            message="Chat session deleted successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete chat session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete chat session"
        )

# Optional: Streaming endpoint for better user experience
@router.post("/sessions/{session_id}/messages/stream")
async def send_message_stream(
    session_id: int,
    message: ChatMessageCreate,
    current_user: UserResponse = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Send a message and stream the AI response for better UX."""
    try:
        # Verify session belongs to user
        session = ChatService.get_session_by_id(db, session_id)
        if not session or session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        # Add user message to database
        user_message = ChatService.add_message_to_session(
            db, session_id, message.content, "user"
        )
        
        async def generate_stream():
            try:
                # Get previous messages for context
                previous_messages = ChatService.get_session_messages(db, session_id)
                
                # Generate title for the chat if this is the first user message
                user_messages_count = len([msg for msg in previous_messages if msg.sender_type == "user"])
                if user_messages_count == 1:  # This is the first user message
                    try:
                        new_title = await openrouter_service.generate_chat_title(message.content)
                        ChatService.update_session_title(db, session_id, new_title)
                        logger.info(f"Updated session {session_id} title to: {new_title}")
                    except Exception as e:
                        logger.error(f"Failed to generate title for session {session_id}: {e}")
                
                # Format messages for OpenRouter API
                formatted_messages = openrouter_service.format_messages_for_api(previous_messages)
                
                # Generate AI response using OpenRouter with streaming
                ai_response_text = await openrouter_service.generate_response(formatted_messages, stream=True)
                
                # Add AI response to database
                ai_message = ChatService.add_message_to_session(
                    db, session_id, ai_response_text, "bot"
                )
                
                # Stream the complete response
                response_data = {
                    "id": ai_message.id,
                    "content": ai_response_text,
                    "sender_type": "bot",
                    "created_at": ai_message.created_at.isoformat()
                }
                
                yield f"data: {json.dumps(response_data)}\n\n"
                yield f"data: [DONE]\n\n"
                
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                error_data = {"error": "Failed to generate response"}
                yield f"data: {json.dumps(error_data)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start streaming for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start streaming"
        )
