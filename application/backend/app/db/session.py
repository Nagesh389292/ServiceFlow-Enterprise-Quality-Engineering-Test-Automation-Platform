from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=settings.ENVIRONMENT == "development")
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


from sqlalchemy import select

async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        yield session


async def init_db() -> None:
    import app.models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        from app.models import User, Priority, Category, UserRole
        from app.core.security import get_password_hash


        res = await session.execute(select(User))
        if not res.scalars().first():
            priorities = [
                Priority(name="P1", display_name="Critical - Immediate", sla_hours=1, color="#DC2626"),
                Priority(name="P2", display_name="High - Urgent", sla_hours=4, color="#EA580C"),
                Priority(name="P3", display_name="Medium - Normal", sla_hours=8, color="#CA8A04"),
                Priority(name="P4", display_name="Low - Low Priority", sla_hours=24, color="#16A34A"),
            ]
            session.add_all(priorities)

            categories = [
                Category(name="Hardware", description="Hardware related issues"),
                Category(name="Software", description="Software installation and licensing"),
                Category(name="Network", description="Network and WiFi connectivity"),
                Category(name="Access", description="Account access and permissions"),
                Category(name="Security", description="Security incidents and phishing"),
            ]
            session.add_all(categories)

            users = [
                User(
                    email="admin@eqe.com",
                    username="admin",
                    full_name="System Administrator",
                    hashed_password=get_password_hash("Admin@123"),
                    role=UserRole.ADMIN,
                    is_active=True
                ),
                User(
                    email="agent@eqe.com",
                    username="agent",
                    full_name="Support Agent",
                    hashed_password=get_password_hash("Agent@123"),
                    role=UserRole.AGENT,
                    is_active=True
                ),
                User(
                    email="employee@eqe.com",
                    username="employee",
                    full_name="John Employee",
                    hashed_password=get_password_hash("Employee@123"),
                    role=UserRole.EMPLOYEE,
                    is_active=True
                ),
            ]
            session.add_all(users)
            await session.commit()