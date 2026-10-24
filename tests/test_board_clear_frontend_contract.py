"""Source regression for scoped whiteboard clear UX (runtime E2E is independent Muse's gate)."""

from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[1] / "frontend/src/pages/LearnTogether.tsx")


def test_clear_my_writing_uses_server_durable_events_and_scoped_confirmation():
    source = SOURCE.read_text(encoding="utf-8")
    assert 'Clear My Writing' in source
    assert 'clear-my-writing`' in source
    assert "page_id: pageAtConfirmation" in source
    assert "expected_revision: expectedRevision" in source
    assert "ingest.current(batch)" in source
    assert "Clear {ownVisibleCount} of my marks" in source
    assert 'role="group"' in source
    assert 'aria-modal="true"' not in source
