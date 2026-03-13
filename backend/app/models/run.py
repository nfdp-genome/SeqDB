from datetime import datetime
from typing import Optional
from sqlalchemy import String, BigInteger, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import FileType


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    internal_accession: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    ena_accession: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    ncbi_accession: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    file_type: Mapped[FileType] = mapped_column(SAEnum(FileType))
    file_path: Mapped[str] = mapped_column(String(1000))
    file_size: Mapped[int] = mapped_column(BigInteger)
    checksum_md5: Mapped[str] = mapped_column(String(32))
    checksum_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    experiment = relationship("Experiment", back_populates="runs")
    qc_reports = relationship("QCReport", back_populates="run")
