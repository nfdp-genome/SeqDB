from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DomainSchema(Base):
    __tablename__ = "domain_schemas"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(255))
    ena_checklist: Mapped[str] = mapped_column(String(20))
    ncbi_package: Mapped[str] = mapped_column(String(100))
