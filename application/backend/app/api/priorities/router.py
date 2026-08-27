from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.api.deps import get_db, require_admin, get_current_active_user
from app.models import Priority, User
from app.schemas import PriorityResponse, PriorityCreate, PaginatedResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_priorities(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = select(Priority)
    if active_only:
        query = query.where(Priority.is_active == True)
    
    total_result = await db.execute(select(func.count(Priority.id)).where(Priority.is_active == True if active_only else True))
    total = total_result.scalar()
    
    result = await db.execute(
        query.offset((page - 1) * page_size).limit(page_size).order_by(Priority.id)
    )
    priorities = result.scalars().all()
    
    return PaginatedResponse(
        items=[PriorityResponse.model_validate(p) for p in priorities],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.post("", response_model=PriorityResponse, status_code=status.HTTP_201_CREATED)
async def create_priority(
    priority_data: PriorityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    result = await db.execute(select(Priority).where(Priority.name == priority_data.name))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Priority already exists")

    priority = Priority(
        name=priority_data.name,
        display_name=priority_data.display_name,
        sla_hours=priority_data.sla_hours,
        color=priority_data.color
    )
    db.add(priority)
    await db.commit()
    await db.refresh(priority)
    return priority


@router.get("/{priority_id}", response_model=PriorityResponse)
async def get_priority(
    priority_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(select(Priority).where(Priority.id == priority_id))
    priority = result.scalar_one_or_none()
    if not priority:
        raise HTTPException(status_code=404, detail="Priority not found")
    return priority