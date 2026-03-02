from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from models.database import get_db, SupportTicket, User, Notification
from schemas.schemas import SupportTicketCreate, SupportTicketResponse, TicketStatusUpdate
from core.security import get_current_user
from datetime import datetime

router = APIRouter()

@router.post("/tickets", response_model=SupportTicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    ticket: SupportTicketCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new support ticket or bug report"""
    print(f"DEBUG: Creating ticket: {ticket}")
    db_ticket = SupportTicket(
        user_id=current_user.id,
        ticket_type=ticket.ticket_type,
        subject=ticket.subject,
        description=ticket.description,
        attachment_url=ticket.attachment_url,
        status="open"
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket

@router.get("/my-tickets", response_model=List[SupportTicketResponse])
def get_my_tickets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all tickets submitted by the current user"""
    return db.query(SupportTicket).filter(SupportTicket.user_id == current_user.id).all()

@router.get("/admin/tickets", response_model=List[SupportTicketResponse])
def get_all_tickets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all tickets (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    # Joining with user to ensure we have profile info
    return db.query(SupportTicket).join(User).all()

@router.patch("/admin/tickets/{ticket_id}/status", response_model=SupportTicketResponse)
def update_ticket_status(
    ticket_id: int,
    status_update: TicketStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a ticket's status (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    db_ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    db_ticket.status = status_update.status
    
    # Create notification for user
    notification = Notification(
        user_id=db_ticket.user_id,
        title="Ticket Status Updated",
        message=f"Your {db_ticket.ticket_type} ticket '{db_ticket.subject}' status has been updated to '{status_update.status}'.",
        link="/profile" # Redirect to support section
    )
    db.add(notification)
    
    db.commit()
    db.refresh(db_ticket)
    return db_ticket
