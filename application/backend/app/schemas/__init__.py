from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from enum import Enum


class UserRole(str, Enum):
    EMPLOYEE = "employee"
    AGENT = "agent"
    ADMIN = "admin"


class TicketStatus(str, Enum):
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"
    RESOLVED = "resolved"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    ESCALATED = "escalated"


class TicketPriority(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[UserRole] = None


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = UserRole.EMPLOYEE


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LoginRequest(BaseModel):
    username: str
    password: str


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class CategoryResponse(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime


class PriorityBase(BaseModel):
    name: TicketPriority
    display_name: str = Field(..., min_length=1, max_length=50)
    sla_hours: int = Field(..., gt=0)
    color: str = Field(..., pattern=r'^#[0-9A-Fa-f]{6}$')


class PriorityCreate(PriorityBase):
    pass


class PriorityResponse(PriorityBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool


class SLARuleBase(BaseModel):
    category_id: Optional[int] = None
    priority_id: int
    response_time_hours: int = Field(..., gt=0)
    resolution_time_hours: int = Field(..., gt=0)


class SLARuleCreate(SLARuleBase):
    pass


class SLARuleUpdate(BaseModel):
    response_time_hours: Optional[int] = Field(None, gt=0)
    resolution_time_hours: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = None


class SLARuleResponse(SLARuleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime


class TicketBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    priority_id: int
    category_id: int


class TicketCreate(TicketBase):
    pass


class TicketUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[TicketStatus] = None
    priority_id: Optional[int] = None
    category_id: Optional[int] = None
    assignee_id: Optional[int] = None


class TicketAssign(BaseModel):
    assignee_id: int


class TicketStatusChange(BaseModel):
    status: TicketStatus


class TicketPriorityChange(BaseModel):
    priority_id: int


class TicketEscalate(BaseModel):
    reason: str = Field(..., min_length=1)


class TicketClose(BaseModel):
    resolution: str = Field(..., min_length=1)


class TicketResponse(TicketBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_number: str
    status: TicketStatus
    creator_id: int
    assignee_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    closed_at: Optional[datetime]
    due_date: Optional[datetime]


class TicketCommentBase(BaseModel):
    content: str = Field(..., min_length=1)
    is_internal: bool = False


class TicketCommentCreate(TicketCommentBase):
    pass


class TicketCommentResponse(TicketCommentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    author_id: int
    created_at: datetime
    updated_at: datetime


class TicketHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    field_name: str
    old_value: Optional[str]
    new_value: Optional[str]
    changed_by: int
    changed_at: datetime


class AttachmentBase(BaseModel):
    filename: str
    file_path: str
    file_size: int
    mime_type: str


class AttachmentResponse(AttachmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    uploaded_by: int
    created_at: datetime


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    message: str
    is_read: bool
    reference_type: Optional[str]
    reference_id: Optional[int]
    created_at: datetime


class PaginatedResponse(BaseModel):
    items: List
    total: int
    page: int
    page_size: int
    total_pages: int