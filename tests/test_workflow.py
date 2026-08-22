import pytest

from gateway.errors import InvalidInputError, WorkflowValidationError
from gateway.workflow import Binding, patch_workflow


def sample_workflow():
    return {
        "12": {"class_type": "LoadVideo", "inputs": {"video": "old.mp4"}},
        "25": {"class_type": "LoadImage", "inputs": {"image": "old.png"}},
    }


def test_patch_only_declared_inputs():
    original = sample_workflow()
    bindings = {
        "video": Binding(node="12", field="video"),
        "face": Binding(node="25", field="image"),
    }

    patched = patch_workflow(
        original,
        bindings,
        {"video": "agent-skills/source.mp4", "face": "agent-skills/face.jpg"},
    )

    assert patched["12"]["inputs"]["video"] == "agent-skills/source.mp4"
    assert patched["25"]["inputs"]["image"] == "agent-skills/face.jpg"
    assert original["12"]["inputs"]["video"] == "old.mp4"


def test_rejects_undeclared_patch():
    with pytest.raises(InvalidInputError) as exc:
        patch_workflow(
            sample_workflow(),
            {"video": Binding(node="12", field="video")},
            {"sampler": "malicious-change"},
        )
    assert exc.value.code == "INVALID_INPUT"


def test_rejects_missing_bound_field():
    with pytest.raises(WorkflowValidationError):
        patch_workflow(
            sample_workflow(),
            {"video": Binding(node="12", field="missing")},
            {"video": "source.mp4"},
        )
