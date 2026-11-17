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


def test_parent_trash_stays_visible_after_last_active_board_moves_to_trash():
    """A parent may have zero active boards while retaining recoverable boards."""
    source = SOURCE.read_text(encoding="utf-8")
    refresh = source.split("async function refreshBoardList() {", 1)[1].split(
        "async function createNewBoard(", 1
    )[0]
    assert 'api<Board[]>("/together/boards/trash")' in refresh
    assert 'active.some(' not in refresh
    assert 'err.status === 403' in refresh
    assert 'setTrashedBoards(trash)' in refresh
    assert 'setTrashedBoards([])' in refresh
    assert "await refreshBoardList()" in source
    assert "Permanently delete…" in source
    assert "Restore board" in source
