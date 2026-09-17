import uuid
from datetime import UTC, datetime, timedelta

from app.auth import _digest, create_session, resolve_user_id
from app.auth_models import AuthSession


class FakeDb:
    def __init__(self):
        self.added = None
        self.result = None

    def add(self, value):
        self.added = value

    def flush(self):
        return None

    def scalar(self, _query):
        return self.result


def test_session_token_is_opaque_and_only_hash_is_persisted():
    db = FakeDb()
    user_id = uuid.uuid4()

    token, session = create_session(db, user_id)

    assert token
    assert token != session.token_hash
    assert session.token_hash == _digest(token)
    assert len(session.token_hash) == 64
    assert session.user_id == user_id


def test_expired_session_does_not_resolve_identity():
    db = FakeDb()
    db.result = AuthSession(
        user_id=uuid.uuid4(),
        token_hash="0" * 64,
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )

    assert resolve_user_id(db, "synthetic-test-token") is None
