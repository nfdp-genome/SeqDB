from datetime import datetime
from typing import Optional
from sqlalchemy import String, ForeignKey, Enum as SAEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import QCStatus


class QCReport(Base):
    __tablename__ = "qc_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"))
    status: Mapped[QCStatus] = mapped_column(SAEnum(QCStatus), default=QCStatus.PENDING)
    tool: Mapped[str] = mapped_column(String(100))
    summary: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    report_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    run = relationship("Run", back_populates="qc_reports")
