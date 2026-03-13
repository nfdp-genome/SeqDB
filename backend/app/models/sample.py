from datetime import datetime, date
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, Date, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Sample(Base):
    __tablename__ = "samples"

    id: Mapped[int] = mapped_column(primary_key=True)
    internal_accession: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    ena_accession: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    ncbi_accession: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    domain_schema_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    organism: Mapped[str] = mapped_column(String(255))
    tax_id: Mapped[int] = mapped_column(Integer)
    breed: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    collection_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    geographic_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    host: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tissue: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    developmental_stage: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sex: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    checklist_id: Mapped[str] = mapped_column(String(20))
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    custom_fields: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="samples")
    experiments = relationship("Experiment", back_populates="sample")
