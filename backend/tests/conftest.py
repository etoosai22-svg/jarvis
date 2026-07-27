"""테스트는 개발용 jarvis.db가 아니라 임시 파일 DB를 쓴다.

app.core.database가 import 시점에 engine을 만들기 때문에, 앱을 import하기 전에
환경변수를 세팅해야 한다.
"""

import os
import tempfile
from pathlib import Path

_TEST_DB = Path(tempfile.mkdtemp(prefix="jarvis-test-")) / "test.db"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TEST_DB}"
os.environ["AUTH_REQUIRED"] = "false"
os.environ.pop("OPENAI_API_KEY", None)  # LLM 호출 없이 fallback 경로를 검증한다.

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
