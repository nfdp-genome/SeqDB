"""Tests for the FTP watcher service."""

import os
import tempfile

from app.services.ftp_watcher import compute_md5, parse_ftp_username


class TestComputeMd5:
    def test_compute_md5(self):
        """Write a temp file, compute MD5, verify it's 32 hex chars."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".fastq") as f:
            f.write(b"@SEQ_ID\nGATCGATCGATCGATC\n+\nFFFFFFFFFFFFFFFF\n")
            f.flush()
            path = f.name

        try:
            md5 = compute_md5(path)
            assert len(md5) == 32
            assert all(c in "0123456789abcdef" for c in md5)
        finally:
            os.unlink(path)

    def test_compute_md5_deterministic(self):
        """Same content should produce the same MD5."""
        content = b"test content for md5"
        with tempfile.NamedTemporaryFile(delete=False) as f1:
            f1.write(content)
            f1.flush()
            path1 = f1.name
        with tempfile.NamedTemporaryFile(delete=False) as f2:
            f2.write(content)
            f2.flush()
            path2 = f2.name

        try:
            assert compute_md5(path1) == compute_md5(path2)
        finally:
            os.unlink(path1)
            os.unlink(path2)


class TestParseFtpUsername:
    def test_valid_username(self):
        assert parse_ftp_username("nfdp_user_5") == 5

    def test_valid_large_id(self):
        assert parse_ftp_username("nfdp_user_12345") == 12345

    def test_invalid_format(self):
        assert parse_ftp_username("invalid") is None

    def test_wrong_prefix(self):
        assert parse_ftp_username("user_5") is None

    def test_no_number(self):
        assert parse_ftp_username("nfdp_user_") is None

    def test_extra_suffix(self):
        assert parse_ftp_username("nfdp_user_5_extra") is None
