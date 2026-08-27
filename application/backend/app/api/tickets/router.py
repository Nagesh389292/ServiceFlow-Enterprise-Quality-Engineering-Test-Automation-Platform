from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from app.api.deps import get_db, get_current_active_user, require_agent, require_admin
from app.models import (
    User, Ticket, TicketComment, TicketHistory, Attachment, 
    Category, Priority, TicketStatus, Notification
)
from app.schemas import (
    TicketResponse, TicketCreate, TicketUpdate, TicketAssign,
    TicketStatusChange, TicketPriorityChange, TicketEscalate, TicketClose,
    TicketCommentResponse, TicketCommentCreate, TicketHistoryResponse,
    AttachmentResponse, PaginatedResponse
)

router = APIRouter()


def generate_ticket_number() -> str:
    import random
    from datetime import datetime
    suffix = random.randint(1000, 9999)
    return f"TCK-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')[:17]}-{suffix}"



async def create_ticket_history(
    db: AsyncSession,
    ticket_id: int,
    field_name: str,
    old_value: Optional[str],
    new_value: Optional[str],
    changed_by: int
):
    history = TicketHistory(
        ticket_id=ticket_id,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        changed_by=changed_by
    )
    db.add(history)


async def create_notification(
    db: AsyncSession,
    user_id: int,
    title: str,
    message: str,
    reference_type: str = "ticket",
    reference_id: Optional[int] = None
):
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        reference_type=reference_type,
        reference_id=reference_id
    )
    db.add(notification)


@router.get("", response_model=PaginatedResponse)
async def list_tickets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[TicketStatus] = None,
    priority_id: Optional[int] = None,
    category_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
    creator_id: Optional[int] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = select(Ticket).options(
        selectinload(Ticket.category),
        selectinload(Ticket.priority),
        selectinload(Ticket.creator),
        selectinload(Ticket.assignee)
    )
    
    if current_user.role == "employee":
        query = query.where(Ticket.creator_id == current_user.id)
    elif current_user.role == "agent":
        query = query.where(or_(Ticket.assignee_id == current_user.id, Ticket.creator_id == current_user.id))
    
    if status:
        query = query.where(Ticket.status == status)
    if priority_id:
        query = query.where(Ticket.priority_id == priority_id)
    if category_id:
        query = query.where(Ticket.category_id == category_id)
    if assignee_id:
        query = query.where(Ticket.assignee_id == assignee_id)
    if creator_id:
        query = query.where(Ticket.creator_id == creator_id)
    if search:
        query = query.where(
            or_(
                Ticket.title.ilike(f"%{search}%"),
                Ticket.description.ilike(f"%{search}%"),
                Ticket.ticket_number.ilike(f"%{search}%")
            )
        )
    
    total_result = await db.execute(select(func.count(Ticket.id)).select_from(query.subquery()))
    total = total_result.scalar()
    
    result = await db.execute(
        query.order_by(Ticket.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    tickets = result.scalars().all()
    
    return PaginatedResponse(
        items=[TicketResponse.model_validate(t) for t in tickets],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


async def fetch_ticket_response(db: AsyncSession, ticket_id: int) -> Ticket:
    query = select(Ticket).options(
        selectinload(Ticket.category),
        selectinload(Ticket.priority),
        selectinload(Ticket.creator),
        selectinload(Ticket.assignee)
    ).where(Ticket.id == ticket_id)
    res = await db.execute(query)
    return res.scalar_one()


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    ticket_data: TicketCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(select(Category).where(Category.id == ticket_data.category_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Category not found")
    result = await db.execute(select(Priority).where(Priority.id == ticket_data.priority_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Priority not found")

    ticket = Ticket(
        ticket_number=generate_ticket_number(),
        title=ticket_data.title,
        description=ticket_data.description,
        priority_id=ticket_data.priority_id,
        category_id=ticket_data.category_id,
        creator_id=current_user.id,
        status=TicketStatus.OPEN
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    
    await create_notification(
        db, current_user.id, "Ticket Created",
        f"Your ticket {ticket.ticket_number} has been created",
        "ticket", ticket.id
    )
    await db.commit()
    
    return await fetch_ticket_response(db, ticket.id)


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = select(Ticket).options(
        selectinload(Ticket.category),
        selectinload(Ticket.priority),
        selectinload(Ticket.creator),
        selectinload(Ticket.assignee)
    ).where(Ticket.id == ticket_id)
    
    result = await db.execute(query)
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if current_user.role == "employee" and ticket.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this ticket")
    if current_user.role == "agent" and ticket.assignee_id != current_user.id and ticket.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this ticket")
    
    return ticket


@router.put("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: int,
    ticket_update: TicketUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = select(Ticket).where(Ticket.id == ticket_id)
    result = await db.execute(query)
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if current_user.role == "employee" and ticket.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this ticket")
    
    update_data = ticket_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        old_value = getattr(ticket, field)
        if old_value != value:
            await create_ticket_history(db, ticket_id, field, str(old_value) if old_value else None, str(value) if value else None, current_user.id)
            setattr(ticket, field, value)
    
    ticket.updated_at = datetime.utcnow()
    await db.commit()
    return await fetch_ticket_response(db, ticket.id)


@router.post("/{ticket_id}/assign", response_model=TicketResponse)
async def assign_ticket(
    ticket_id: int,
    assign_data: TicketAssign,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_agent)
):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    result = await db.execute(select(User).where(User.id == assign_data.assignee_id))
    assignee = result.scalar_one_or_none()
    if not assignee or assignee.role not in ["agent", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid assignee")
    
    old_assignee = ticket.assignee_id
    ticket.assignee_id = assign_data.assignee_id
    ticket.status = TicketStatus.ASSIGNED
    ticket.updated_at = datetime.utcnow()
    
    await create_ticket_history(db, ticket_id, "assignee_id", str(old_assignee) if old_assignee else None, str(assign_data.assignee_id), current_user.id)
    await create_ticket_history(db, ticket_id, "status", str(old_assignee), TicketStatus.ASSIGNED.value, current_user.id)
    
    await create_notification(
        db, assign_data.assignee_id, "Ticket Assigned",
        f"Ticket {ticket.ticket_number} has been assigned to you",
        "ticket", ticket.id
    )
    
    await db.commit()
    return await fetch_ticket_response(db, ticket.id)


@router.post("/{ticket_id}/status", response_model=TicketResponse)
async def change_ticket_status(
    ticket_id: int,
    status_data: TicketStatusChange,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if current_user.role == "employee" and ticket.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == "agent" and ticket.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    old_status = ticket.status
    ticket.status = status_data.status
    ticket.updated_at = datetime.utcnow()
    
    if status_data.status == TicketStatus.RESOLVED:
        ticket.resolved_at = datetime.utcnow()
    elif status_data.status == TicketStatus.CLOSED:
        ticket.closed_at = datetime.utcnow()
    
    await create_ticket_history(db, ticket_id, "status", old_status.value, status_data.status.value, current_user.id)
    await db.commit()
    return await fetch_ticket_response(db, ticket.id)


@router.post("/{ticket_id}/priority", response_model=TicketResponse)
async def change_ticket_priority(
    ticket_id: int,
    priority_data: TicketPriorityChange,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_agent)
):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    result = await db.execute(select(Priority).where(Priority.id == priority_data.priority_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Priority not found")
    
    old_priority = ticket.priority_id
    ticket.priority_id = priority_data.priority_id
    ticket.updated_at = datetime.utcnow()
    
    await create_ticket_history(db, ticket_id, "priority_id", str(old_priority), str(priority_data.priority_id), current_user.id)
    await db.commit()
    return await fetch_ticket_response(db, ticket.id)


@router.post("/{ticket_id}/escalate", response_model=TicketResponse)
async def escalate_ticket(
    ticket_id: int,
    escalate_data: TicketEscalate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_agent)
):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    old_status = ticket.status
    ticket.status = TicketStatus.ESCALATED
    ticket.updated_at = datetime.utcnow()
    
    await create_ticket_history(db, ticket_id, "status", old_status.value, TicketStatus.ESCALATED.value, current_user.id)
    
    comment = TicketComment(
        ticket_id=ticket_id,
        author_id=current_user.id,
        content=f"Escalated: {escalate_data.reason}",
        is_internal=True
    )
    db.add(comment)
    
    await create_notification(
        db, ticket.creator_id, "Ticket Escalated",
        f"Your ticket {ticket.ticket_number} has been escalated: {escalate_data.reason}",
        "ticket", ticket.id
    )
    
    await db.commit()
    return await fetch_ticket_response(db, ticket.id)


@router.post("/{ticket_id}/close", response_model=TicketResponse)
async def close_ticket(
    ticket_id: int,
    close_data: TicketClose,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if current_user.role == "employee" and ticket.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == "agent" and ticket.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    old_status = ticket.status
    ticket.status = TicketStatus.CLOSED
    ticket.closed_at = datetime.utcnow()
    ticket.updated_at = datetime.utcnow()
    
    await create_ticket_history(db, ticket_id, "status", old_status.value, TicketStatus.CLOSED.value, current_user.id)
    
    comment = TicketComment(
        ticket_id=ticket_id,
        author_id=current_user.id,
        content=f"Closed: {close_data.resolution}",
        is_internal=False
    )
    db.add(comment)
    await create_notification(
        db, ticket.creator_id, "Ticket Closed",
        f"Your ticket {ticket.ticket_number} has been closed: {close_data.resolution}",
        "ticket", ticket.id
    )
    
    await db.commit()
    return await fetch_ticket_response(db, ticket.id)


@router.post("/{ticket_id}/comments", response_model=TicketCommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
    ticket_id: int,
    comment_data: TicketCommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if current_user.role == "employee" and ticket.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == "agent" and ticket.assignee_id != current_user.id and ticket.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    comment = TicketComment(
        ticket_id=ticket_id,
        author_id=current_user.id,
        content=comment_data.content,
        is_internal=comment_data.is_internal
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment


@router.get("/{ticket_id}/comments", response_model=List[TicketCommentResponse])
async def get_comments(
    ticket_id: int,
    include_internal: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if current_user.role == "employee" and ticket.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == "agent" and ticket.assignee_id != current_user.id and ticket.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query = select(TicketComment).where(TicketComment.ticket_id == ticket_id)
    if not include_internal or current_user.role == "employee":
        query = query.where(TicketComment.is_internal == False)
    
    result = await db.execute(query.order_by(TicketComment.created_at))
    comments = result.scalars().all()
    return comments


@router.get("/{ticket_id}/history", response_model=List[TicketHistoryResponse])
async def get_history(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if current_user.role == "employee" and ticket.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == "agent" and ticket.assignee_id != current_user.id and ticket.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query = select(TicketHistory).where(TicketHistory.ticket_id == ticket_id).order_by(TicketHistory.changed_at)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/{ticket_id}/attachments", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    ticket_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if current_user.role == "employee" and ticket.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    import os
    upload_dir = f"/app/uploads/ticket_{ticket_id}"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    attachment = Attachment(
        ticket_id=ticket_id,
        filename=file.filename,
        file_path=file_path,
        file_size=len(content),
        mime_type=file.content_type or "application/octet-stream",
        uploaded_by=current_user.id
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)
    return attachment