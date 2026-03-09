from datetime import datetime, date
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, Enum as SAEnum, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import ProjectType


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    internal_accession: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    ena_accession: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)
    project_type: Mapped[ProjectType] = mapped_column(SAEnum(ProjectType))
    release_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    license: Mapped[str] = mapped_column(String(20), default="CC-BY")
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    created_by_user = relationship("User", back_populates="projects")
    samples = relationship("Sample", back_populates="project")
