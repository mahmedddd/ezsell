"""
Chat/Messaging routes for negotiations on listings
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from typing import List
from datetime import datetime

from models.database import get_db, Message, User, Listing
from schemas.schemas import MessageCreate, MessageResponse, ConversationResponse
from core.security import get_current_user

router = APIRouter(prefix="/messages", tags=["messages"])

@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def send_message(
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_user_token = Depends(get_current_user)
):
    """Send a message to another user about a listing"""
    
    # Get current user from database
    current_user = db.query(User).filter(User.username == current_user_token.username).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="Current user not found")
    
    # Check if receiver exists
    receiver = db.query(User).filter(User.id == message.receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")
    
    # Check if listing exists (if provided)
    listing = None
    if message.listing_id:
        listing = db.query(Listing).filter(Listing.id == message.listing_id).first()
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
    
    # Create message
    db_message = Message(
        content=message.content,
        sender_id=current_user.id,
        receiver_id=message.receiver_id,
        listing_id=message.listing_id
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    # Prepare response
    response = MessageResponse(
        id=db_message.id,
        content=db_message.content,
        sender_id=db_message.sender_id,
        receiver_id=db_message.receiver_id,
        listing_id=db_message.listing_id,
        is_read=db_message.is_read,
        created_at=db_message.created_at,
        sender_username=current_user.username,
        receiver_username=receiver.username,
        listing_title=listing.title if listing else None
    )
    
    return response

@router.get("/conversations", response_model=List[ConversationResponse])
def get_conversations(
    db: Session = Depends(get_db),
    current_user_token = Depends(get_current_user)
):
    """Get all conversations for current user with unread counts"""
    
    # Get current user from database
    current_user = db.query(User).filter(User.username == current_user_token.username).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="Current user not found")
    
    # Get all unique users the current user has chatted with
    subquery = db.query(
        func.max(Message.id).label('last_message_id')
    ).filter(
        or_(
            Message.sender_id == current_user.id,
            Message.receiver_id == current_user.id
        )
    ).group_by(
        func.least(Message.sender_id, Message.receiver_id),
        func.greatest(Message.sender_id, Message.receiver_id),
        Message.listing_id
    ).subquery()
    
    # Get last messages
    last_messages = db.query(Message).join(
        subquery,
        Message.id == subquery.c.last_message_id
    ).all()
    
    conversations = []
    for msg in last_messages:
        # Determine other user
        other_user_id = msg.receiver_id if msg.sender_id == current_user.id else msg.sender_id
        other_user = db.query(User).filter(User.id == other_user_id).first()
        
        # Count unread messages
        unread_count = db.query(Message).filter(
            Message.sender_id == other_user_id,
            Message.receiver_id == current_user.id,
            Message.listing_id == msg.listing_id,
            Message.is_read == False
        ).count()
        
        # Get listing info
        listing = None
        if msg.listing_id:
            listing = db.query(Listing).filter(Listing.id == msg.listing_id).first()
        
        conversations.append(ConversationResponse(
            user_id=other_user.id,
            username=other_user.username,
            avatar_url=other_user.avatar_url,
            listing_id=msg.listing_id,
            listing_title=listing.title if listing else None,
            last_message=msg.content,
            last_message_time=msg.created_at,
            unread_count=unread_count
        ))
    
    # Sort by last message time
    conversations.sort(key=lambda x: x.last_message_time, reverse=True)
    
    return conversations

@router.get("/conversation/{user_id}/{listing_id}", response_model=List[MessageResponse])
def get_conversation_messages(
    user_id: int,
    listing_id: int,
    db: Session = Depends(get_db),
    current_user_token = Depends(get_current_user)
):
    """Get all messages in a conversation about a specific listing"""
    
    # Get current user from database
    current_user = db.query(User).filter(User.username == current_user_token.username).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="Current user not found")
    
    # Get messages between current user and specified user about this listing
    messages = db.query(Message).filter(
        Message.listing_id == listing_id,
        or_(
            and_(Message.sender_id == current_user.id, Message.receiver_id == user_id),
            and_(Message.sender_id == user_id, Message.receiver_id == current_user.id)
        )
    ).order_by(Message.created_at.asc()).all()
    
    # Mark received messages as read
    db.query(Message).filter(
        Message.listing_id == listing_id,
        Message.sender_id == user_id,
        Message.receiver_id == current_user.id,
        Message.is_read == False
    ).update({"is_read": True})
    db.commit()
    
    # Prepare response with usernames
    response_messages = []
    for msg in messages:
        sender = db.query(User).filter(User.id == msg.sender_id).first()
        receiver = db.query(User).filter(User.id == msg.receiver_id).first()
        listing = db.query(Listing).filter(Listing.id == msg.listing_id).first()
        
        response_messages.append(MessageResponse(
            id=msg.id,
            content=msg.content,
            sender_id=msg.sender_id,
            receiver_id=msg.receiver_id,
            listing_id=msg.listing_id,
            is_read=msg.is_read,
            created_at=msg.created_at,
            sender_username=sender.username if sender else None,
            receiver_username=receiver.username if receiver else None,
            listing_title=listing.title if listing else None
        ))
    
    return response_messages

@router.get("/listing/{listing_id}", response_model=List[MessageResponse])
def get_listing_messages(
    listing_id: int,
    db: Session = Depends(get_db),
    current_user_token = Depends(get_current_user)
):
    """Get all messages for a listing (for listing owner)"""
    
    # Get current user from database
    current_user = db.query(User).filter(User.username == current_user_token.username).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="Current user not found")
    
    # Verify listing ownership
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    if listing.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view these messages")
    
    # Get all messages about this listing
    messages = db.query(Message).filter(
        Message.listing_id == listing_id
    ).order_by(Message.created_at.desc()).all()
    
    response_messages = []
    for msg in messages:
        sender = db.query(User).filter(User.id == msg.sender_id).first()
        receiver = db.query(User).filter(User.id == msg.receiver_id).first()
        
        response_messages.append(MessageResponse(
            id=msg.id,
            content=msg.content,
            sender_id=msg.sender_id,
            receiver_id=msg.receiver_id,
            listing_id=msg.listing_id,
            is_read=msg.is_read,
            created_at=msg.created_at,
            sender_username=sender.username if sender else None,
            receiver_username=receiver.username if receiver else None,
            listing_title=listing.title
        ))
    
    return response_messages

@router.get("/unread/count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user_token = Depends(get_current_user)
):
    """Get total unread message count"""
    try:
        # Get current user from database
        current_user = db.query(User).filter(User.username == current_user_token.username).first()
        if not current_user:
            # Return 0 instead of error if user not found
            return {"unread_count": 0}
        
        count = db.query(Message).filter(
            Message.receiver_id == current_user.id,
            Message.is_read == False
        ).count()
        
        return {"unread_count": count}
    except Exception as e:
        # Return 0 on any error to avoid breaking the UI
        print(f"Error getting unread count: {str(e)}")
        return {"unread_count": 0}

@router.patch("/{message_id}/read")
def mark_message_read(
    message_id: int,
    db: Session = Depends(get_db),
    current_user_token = Depends(get_current_user)
):
    """Mark a message as read"""
    # Get current user from database
    current_user = db.query(User).filter(User.username == current_user_token.username).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="Current user not found")
    
    message = db.query(Message).filter(Message.id == message_id).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    if message.receiver_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    message.is_read = True
    db.commit()
    
    return {"message": "Message marked as read"}
