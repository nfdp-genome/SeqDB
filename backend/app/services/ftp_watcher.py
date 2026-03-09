"""FTP watcher service: scan FTP incoming dirs, compute MD5, register staged files."""

import asyncio
import hashlib
import logging
import os
import re
import shutil

from app.models.enums import UploadMethod
from app.services.staging import StagingService

logger = logging.getLogger(__name__)

MD5_BUF_SIZE = 65536  # 64KB read chunks


def compute_md5(filepath: str) -> str:
    """Compute the MD5 hex digest of a file."""
    md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        while True:
            data = f.read(MD5_BUF_SIZE)
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()


def parse_ftp_username(username: str) -> int | None:
    """Extract user_id from FTP username format 'nfdp_user_{id}'.

    Returns the integer user_id, or None if the format doesn't match.
    """
    match = re.match(r"^nfdp_user_(\d+)$", username)
    if match:
        return int(match.group(1))
    return None


class FTPWatcherService:
    """Watch an FTP incoming directory for new files from users."""

    def __init__(self, ftp_base_dir: str):
        self.ftp_base_dir = ftp_base_dir

    async def scan_once(self, db_session_factory) -> int:
        """Scan all user directories under ftp_base_dir.

        For each new file found:
        1. Compute MD5
        2. Register in DB as a staged file
        3. Move the file to the staging area (or mark for MinIO upload)

        Returns the number of files processed.
        """
        processed = 0

        if not os.path.isdir(self.ftp_base_dir):
            logger.warning("FTP base directory does not exist: %s", self.ftp_base_dir)
            return 0

        for entry in os.listdir(self.ftp_base_dir):
            user_dir = os.path.join(self.ftp_base_dir, entry)
            if not os.path.isdir(user_dir):
                continue

            user_id = parse_ftp_username(entry)
            if user_id is None:
                logger.debug("Skipping non-user directory: %s", entry)
                continue

            for filename in os.listdir(user_dir):
                filepath = os.path.join(user_dir, filename)
                if not os.path.isfile(filepath):
                    continue

                try:
                    md5 = compute_md5(filepath)
                    file_size = os.path.getsize(filepath)
                    staging_path = f"staging/{user_id}/ftp/{filename}"

                    async with db_session_factory() as db:
                        svc = StagingService(db)
                        await svc.register_file(
                            user_id=user_id,
                            filename=filename,
                            file_size=file_size,
                            checksum_md5=md5,
                            upload_method=UploadMethod.FTP,
                            staging_path=staging_path,
                        )

                    # Remove the file from the FTP incoming dir after registration
                    os.remove(filepath)
                    processed += 1
                    logger.info(
                        "Registered FTP file: user=%d file=%s md5=%s",
                        user_id, filename, md5,
                    )
                except Exception:
                    logger.exception(
                        "Failed to process FTP file: %s", filepath
                    )

        return processed

    async def run_forever(self, db_session_factory, interval: int = 30) -> None:
        """Poll the FTP directory at the given interval (seconds)."""
        logger.info(
            "FTP watcher started: dir=%s interval=%ds",
            self.ftp_base_dir, interval,
        )
        while True:
            try:
                count = await self.scan_once(db_session_factory)
                if count:
                    logger.info("FTP scan processed %d files", count)
            except Exception:
                logger.exception("FTP scan error")
            await asyncio.sleep(interval)
