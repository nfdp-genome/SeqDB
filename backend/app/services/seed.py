import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.enums import UserRole
from app.models.user import User
from app.services.auth import hash_password

logger = logging.getLogger(__name__)


async def seed_root_admin(db: AsyncSession) -> None:
    result = await db.execute(
        select(User).where(User.email == settings.root_admin_email)
    )
    existing = result.scalar_one_or_none()
    if existing:
        logger.info("Root admin already exists")
        return

    user = User(
        email=settings.root_admin_email,
        hashed_password=hash_password(settings.root_admin_password),
        full_name="Root Administrator",
        role=UserRole.ADMIN,
        must_change_password=True,
    )
    db.add(user)
    await db.commit()
    logger.info("Root admin seeded")
