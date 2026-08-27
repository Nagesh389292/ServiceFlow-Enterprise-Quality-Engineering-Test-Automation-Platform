from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth.router import router as auth_router
from app.api.users.router import router as users_router
from app.api.tickets.router import router as tickets_router
from app.api.categories.router import router as categories_router
from app.api.priorities.router import router as priorities_router
from app.api.sla.router import router as sla_router
from app.api.notifications.router import router as notifications_router
from app.db.session import init_db
from app.core.config import settings

app = FastAPI(
    title="Enterprise Quality Engineering Platform API",
    description="REST API for Enterprise Service Management Portal",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/api/users", tags=["Users"])
app.include_router(tickets_router, prefix="/api/tickets", tags=["Tickets"])
app.include_router(categories_router, prefix="/api/categories", tags=["Categories"])
app.include_router(priorities_router, prefix="/api/priorities", tags=["Priorities"])
app.include_router(sla_router, prefix="/api/sla", tags=["SLA"])
app.include_router(notifications_router, prefix="/api/notifications", tags=["Notifications"])


@app.on_event("startup")
async def startup():
    await init_db()


@app.get("/health")
async def health_check():
    return {"status": "healthy", "environment": settings.ENVIRONMENT}


@app.get("/")
async def root():
    return {"message": "Enterprise QE Platform API", "docs": "/docs"}