from datetime import datetime, timedelta

from sqlalchemy import Integer, String, BigInteger, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import UploadMethod, StagedFileStatus


class StagedFile(Base):
    __tablename__ = "staged_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    filename: Mapped[str] = mapped_column(String(500))
    file_size: Mapped[int] = mapped_column(BigInteger)
    checksum_md5: Mapped[str] = mapped_column(String(32))
    upload_method: Mapped[UploadMethod] = mapped_column(SAEnum(UploadMethod))
    staging_path: Mapped[str] = mapped_column(String(1000))
    status: Mapped[StagedFileStatus] = mapped_column(
        SAEnum(StagedFileStatus), default=StagedFileStatus.PENDING
    )
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.utcnow() + timedelta(days=7)
    )

    user = relationship("User")
