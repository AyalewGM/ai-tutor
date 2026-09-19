import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

from fastapi import HTTPException

from app.privacy_api import (
    CURRENT_NOTICE_VERSION,
    PrivacyNoticeAcknowledgementIn,
    acknowledge_current_notice,
    get_current_notice,
)
from app.privacy_models import PrivacyNoticeAcknowledgement


class FakePrivacyDb:
    def __init__(self, existing=None):
        self.existing = existing
        self.added = []
        self.commits = 0

    def scalar(self, _query):
        return self.existing

    def add(self, value):
        self.added.append(value)
        self.existing = value

    def commit(self):
        self.commits += 1
        for value in self.added:
            if value.acknowledged_at is None:
                value.acknowledged_at = datetime.now(UTC)

    def refresh(self, _value):
        return None


def _parent():
    return SimpleNamespace(id=uuid.uuid4(), role="PARENT")


def test_notice_is_parent_authenticated_and_unacknowledged_initially():
    result = get_current_notice(_parent(), FakePrivacyDb())
    assert result.version == CURRENT_NOTICE_VERSION
    assert result.acknowledged is False
    assert result.acknowledged_at is None
    assert "not represented as verifiable parental consent" in result.summary


def test_acknowledgement_is_idempotent_for_current_version():
    parent = _parent()
    db = FakePrivacyDb()
    payload = PrivacyNoticeAcknowledgementIn(notice_version=CURRENT_NOTICE_VERSION)

    first = acknowledge_current_notice(payload, parent, db)
    second = acknowledge_current_notice(payload, parent, db)

    assert first.acknowledged is True
    assert second.acknowledged is True
    assert len(db.added) == 1
    assert db.commits == 1
    assert db.added[0].user_id == parent.id


def test_stale_notice_version_fails_before_writing():
    db = FakePrivacyDb()
    try:
        acknowledge_current_notice(
            PrivacyNoticeAcknowledgementIn(notice_version="obsolete-version"),
            _parent(),
            db,
        )
    except HTTPException as exc:
        assert exc.status_code == 409
    else:
        raise AssertionError("stale notice acknowledgement must fail")
    assert db.added == []
    assert db.commits == 0


def test_existing_acknowledgement_is_returned_without_duplicate_write():
    parent = _parent()
    existing = PrivacyNoticeAcknowledgement(
        user_id=parent.id,
        notice_version=CURRENT_NOTICE_VERSION,
        acknowledged_at=datetime.now(UTC),
    )
    db = FakePrivacyDb(existing=existing)

    result = acknowledge_current_notice(
        PrivacyNoticeAcknowledgementIn(notice_version=CURRENT_NOTICE_VERSION),
        parent,
        db,
    )

    assert result.acknowledged is True
    assert db.added == []
    assert db.commits == 0
