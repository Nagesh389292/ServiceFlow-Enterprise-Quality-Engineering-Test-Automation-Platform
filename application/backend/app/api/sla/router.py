from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.api.deps import get_db, require_admin, get_current_active_user
from app.models import SLARule, Category, Priority, User
from app.schemas import SLARuleResponse, SLARuleCreate, SLARuleUpdate, PaginatedResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_sla_rules(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = select(SLARule).where(SLARule.is_active == True)
    
    total_result = await db.execute(select(func.count(SLARule.id)).where(SLARule.is_active == True))
    total = total_result.scalar()
    
    result = await db.execute(
        query.offset((page - 1) * page_size).limit(page_size).order_by(SLARule.id)
    )
    sla_rules = result.scalars().all()
    
    return PaginatedResponse(
        items=[SLARuleResponse.model_validate(s) for s in sla_rules],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.post("", response_model=SLARuleResponse, status_code=status.HTTP_201_CREATED)
async def create_sla_rule(
    sla_data: SLARuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    if sla_data.category_id:
        result = await db.execute(select(Category).where(Category.id == sla_data.category_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Category not found")
    
    result = await db.execute(select(Priority).where(Priority.id == sla_data.priority_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Priority not found")

    sla_rule = SLARule(
        category_id=sla_data.category_id,
        priority_id=sla_data.priority_id,
        response_time_hours=sla_data.response_time_hours,
        resolution_time_hours=sla_data.resolution_time_hours
    )
    db.add(sla_rule)
    await db.commit()
    await db.refresh(sla_rule)
    return sla_rule


@router.get("/{sla_id}", response_model=SLARuleResponse)
async def get_sla_rule(
    sla_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(select(SLARule).where(SLARule.id == sla_id))
    sla_rule = result.scalar_one_or_none()
    if not sla_rule:
        raise HTTPException(status_code=404, detail="SLA rule not found")
    return sla_rule


@router.put("/{sla_id}", response_model=SLARuleResponse)
async def update_sla_rule(
    sla_id: int,
    sla_update: SLARuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    result = await db.execute(select(SLARule).where(SLARule.id == sla_id))
    sla_rule = result.scalar_one_or_none()
    if not sla_rule:
        raise HTTPException(status_code=404, detail="SLA rule not found")

    update_data = sla_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(sla_rule, field, value)
    await db.commit()
    await db.refresh(sla_rule)
    return sla_rule


@router.delete("/{sla_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sla_rule(
    sla_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    result = await db.execute(select(SLARule).where(SLARule.id == sla_id))
    sla_rule = result.scalar_one_or_none()
    if not sla_rule:
        raise HTTPException(status_code=404, detail="SLA rule not found")
    await db.delete(sla_rule)
    await db.commit()