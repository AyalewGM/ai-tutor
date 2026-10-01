import uuid

from fastapi.testclient import TestClient

from app.multimodal_api import MultimodalStepIn


def test_multimodal_payload_rejects_non_png() -> None:
    try:
        MultimodalStepIn(
            session_id=uuid.uuid4(),
            prompt="help",
            canvas={"version": 1, "strokes": []},
            snapshot_data_url="data:image/jpeg;base64,abc",
        )
    except ValueError:
        return
    raise AssertionError("non-PNG scratchpad payload must be rejected")


def test_multimodal_payload_bounds_prompt() -> None:
    try:
        MultimodalStepIn(
            session_id=uuid.uuid4(),
            prompt="x" * 501,
            canvas={"version": 1, "strokes": []},
            snapshot_data_url="data:image/png;base64,abc",
        )
    except ValueError:
        return
    raise AssertionError("oversized prompt must be rejected")
