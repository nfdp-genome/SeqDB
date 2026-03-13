from datetime import datetime
from typing import Optional

from sqlalchemy import Enum as SAEnum, JSON, String, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import OntologyType


class OntologyTerm(Base):
    __tablename__ = "ontology_terms"
    __table_args__ = (
        UniqueConstraint("ontology", "term_id", name="uq_ontology_term"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ontology: Mapped[OntologyType] = mapped_column(SAEnum(OntologyType), index=True)
    term_id: Mapped[str] = mapped_column(String(100), index=True)
    label: Mapped[str] = mapped_column(String(500))
    synonyms: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    parent_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_obsolete: Mapped[bool] = mapped_column(Boolean, default=False)
    last_updated: Mapped[datetime] = mapped_column(default=datetime.utcnow)
