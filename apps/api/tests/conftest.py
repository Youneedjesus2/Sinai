import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

DB_PATH = Path('tests/test.db')
os.environ['APP_ENV'] = 'test'
os.environ['DATABASE_URL'] = f'sqlite:///{DB_PATH}'
os.environ['OPENAI_API_KEY'] = 'test-key'
os.environ['RINGCENTRAL_WEBHOOK_VERIFICATION_TOKEN'] = 'test-verification-token'

from src.main import app  # noqa: E402
from src.core.db import Base, engine  # noqa: E402


@pytest.fixture(autouse=True)
def reset_db():
    if DB_PATH.exists():
        DB_PATH.unlink()
    engine.dispose()
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if DB_PATH.exists():
        DB_PATH.unlink()


@pytest.fixture
def client():
    return TestClient(app)
