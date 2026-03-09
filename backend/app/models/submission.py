from datetime import datetime
from typing import Optional
from sqlalchemy import String, ForeignKey, Enum as SAEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import SubmissionStatus


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    internal_accession: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(500))
    status: Mapped[SubmissionStatus] = mapped_column(
        SAEnum(SubmissionStatus), default=SubmissionStatus.DRAFT
    )
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    run_accessions: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    validation_report: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
