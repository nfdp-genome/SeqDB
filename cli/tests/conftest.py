import pytest
from seqdb_cli.config import SeqDBConfig


@pytest.fixture
def mock_config(tmp_path):
    return SeqDBConfig(
        server_url="https://api.seqdb.test",
        access_token="test-token-123",
        refresh_token="refresh-456",
    )
