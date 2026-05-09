"""
Chat/Messaging routes for negotiations on listings
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from typing import List, Optional
from datetime import datetime
import json

from models.database import get_db, Message, User, Listing, BlockedUser
from schemas.schemas import MessageCreate, MessageResponse, ConversationResponse
from core.security import get_current_user
from .users import get_current_admin_user

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
    
    # Check if blocked
    block_exists = db.query(BlockedUser).filter(
        or_(
            and_(BlockedUser.blocker_id == current_user.id, BlockedUser.blocked_id == message.receiver_id),
            and_(BlockedUser.blocker_id == message.receiver_id, BlockedUser.blocked_id == current_user.id)
        )
    ).first()
    
    if block_exists:
        raise HTTPException(
            status_code=403, 
            detail="Cannot send message. One of the users has blocked the other."
        )
    
    # Create message
    db_message = Message(
        content=message.content,
        sender_id=current_user.id,
        receiver_id=message.receiver_id,
        listing_id=message.listing_id
    )
    db.add(db_message)
    
    # Mark all previous messages from this receiver to the sender as read
    # because sending a reply implies seeking the previous messages
    db.query(Message).filter(
        Message.sender_id == message.receiver_id,
        Message.receiver_id == current_user.id,
        Message.is_read == False
    ).update({"is_read": True})
    
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
    # For SQLite compatibility, use CASE instead of least/greatest
    from sqlalchemy import case
    other_user_id = case(
        (Message.sender_id == current_user.id, Message.receiver_id),
        else_=Message.sender_id
    )
    
    subquery = db.query(
        func.max(Message.id).label('last_message_id')
    ).filter(
        or_(
            Message.sender_id == current_user.id,
            Message.receiver_id == current_user.id
        )
    ).group_by(
        other_user_id
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
        
        if not other_user:
            continue
            
        # Count unread messages (user-wide, not just for this listing)
        unread_count = db.query(Message).filter(
            Message.sender_id == other_user_id,
            Message.receiver_id == current_user.id,
            Message.is_read == False
        ).count()
        
        # Determine online status (last seen within 5 minutes)
        is_online = False
        if other_user.last_seen:
            diff = datetime.utcnow() - other_user.last_seen
            if diff.total_seconds() < 300:  # 5 minutes
                is_online = True
        
        # Get listing info (if available)
        listing = None
        listing_image = None
        listing_price = None
        listing = None
        
        # Get the listing_id from the message, or find the most recent non-null listing_id in this conversation
        listing_id = msg.listing_id
        if not listing_id:
            # Look for any previous message in this conversation that has a listing_id
            first_listing_msg = db.query(Message).filter(
                or_(
                    and_(Message.sender_id == current_user.id, Message.receiver_id == other_user.id),
                    and_(Message.sender_id == other_user.id, Message.receiver_id == current_user.id)
                ),
                Message.listing_id.isnot(None)
            ).order_by(Message.id.desc()).first()
            if first_listing_msg:
                listing_id = first_listing_msg.listing_id

        if listing_id:
            listing = db.query(Listing).filter(Listing.id == listing_id).first()
            if listing and listing.images:
                try:
                    images = json.loads(listing.images)
                    if images and len(images) > 0:
                        listing_image = images[0]
                    listing_price = listing.price
                except:
                    pass

        conversations.append(ConversationResponse(
            user_id=other_user.id,
            username=other_user.username,
            avatar_url=getattr(other_user, 'avatar_url', None),
            listing_id=listing_id,
            listing_title=listing.title if listing else None,
            listing_image=listing_image,
            listing_price=listing_price,
            last_message=msg.content,
            last_message_time=msg.created_at,
            unread_count=unread_count,
            last_seen=other_user.last_seen,
            is_online=is_online
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
    
    # Get messages between current user and specified user across all listings
    messages = db.query(Message).filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.receiver_id == user_id),
            and_(Message.sender_id == user_id, Message.receiver_id == current_user.id)
        )
    ).order_by(Message.created_at.asc()).all()
    
    # Populate listing images in responses
    response_messages = []
    for m in messages:
        msg_resp = MessageResponse.from_orm(m)
        if m.listing:
            try:
                images = json.loads(m.listing.images)
                if images and len(images) > 0:
                    msg_resp.listing_image = images[0]
            except:
                pass
        response_messages.append(msg_resp)

    # Mark all received messages from this user as read
    # (Regardless of listing, to keep unread counts consistent with UI)
    db.query(Message).filter(
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

@router.delete("/conversation/{user_id}")
def delete_conversation(
    user_id: int,
    db: Session = Depends(get_db),
    current_user_token = Depends(get_current_user)
):
    """Delete entire conversation with a specific user"""
    # Get current user from database
    current_user = db.query(User).filter(User.username == current_user_token.username).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="Current user not found")
    
    # Delete all messages between current user and specified user
    deleted_count = db.query(Message).filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.receiver_id == user_id),
            and_(Message.sender_id == user_id, Message.receiver_id == current_user.id)
        )
    ).delete(synchronize_session=False)
    
    db.commit()
    
    return {"message": f"Successfully deleted {deleted_count} messages in conversation"}

@router.get("/admin/conversation/{user1_id}/{user2_id}", response_model=List[MessageResponse])
def get_conversation_admin(
    user1_id: int,
    user2_id: int,
    listing_id: Optional[int] = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Get conversation between two users (admin only)"""
    query = db.query(Message).filter(
        or_(
            and_(Message.sender_id == user1_id, Message.receiver_id == user2_id),
            and_(Message.sender_id == user2_id, Message.receiver_id == user1_id)
        )
    )
    
    if listing_id:
        query = query.filter(Message.listing_id == listing_id)
        
    messages = query.order_by(Message.created_at.asc()).all()
    
    result = []
    for m in messages:
        sender = db.query(User).filter(User.id == m.sender_id).first()
        receiver = db.query(User).filter(User.id == m.receiver_id).first()
        listing = db.query(Listing).filter(Listing.id == m.listing_id).first() if m.listing_id else None
        
        result.append(MessageResponse(
            id=m.id,
            content=m.content,
            sender_id=m.sender_id,
            receiver_id=m.receiver_id,
            listing_id=m.listing_id,
            is_read=m.is_read,
            created_at=m.created_at,
            sender_username=sender.username if sender else "Unknown",
            receiver_username=receiver.username if receiver else "Unknown",
            listing_title=listing.title if listing else None
        ))
    return result
