from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import Platform, LibraryStrategy, LibrarySource, LibraryLayout


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(primary_key=True)
    internal_accession: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    ena_accession: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    platform: Mapped[Platform] = mapped_column(SAEnum(Platform))
    instrument_model: Mapped[str] = mapped_column(String(255))
    library_strategy: Mapped[LibraryStrategy] = mapped_column(SAEnum(LibraryStrategy))
    library_source: Mapped[LibrarySource] = mapped_column(SAEnum(LibrarySource))
    library_layout: Mapped[LibraryLayout] = mapped_column(SAEnum(LibraryLayout))
    insert_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sample_id: Mapped[int] = mapped_column(ForeignKey("samples.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    sample = relationship("Sample", back_populates="experiments")
    runs = relationship("Run", back_populates="experiment")
