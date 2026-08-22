from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gateway.errors import InvalidInputError, WorkflowValidationError


@dataclass(frozen=True, slots=True)
class Binding:
    node: str
    field: str


def load_workflow(path: str | Path) -> dict[str, Any]:
    workflow_path = Path(path)
    if not workflow_path.is_file():
        raise InvalidInputError(f"Workflow file does not exist: {workflow_path}")
    with workflow_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise WorkflowValidationError("API workflow JSON must be an object keyed by node id.")
    return data


def patch_workflow(
    workflow: dict[str, Any],
    bindings: dict[str, Binding],
    values: dict[str, Any],
) -> dict[str, Any]:
    """Patch only explicitly declared node inputs.

    This is the production safety boundary: callers can supply semantic values,
    but cannot mutate arbitrary nodes or graph structure.
    """
    unknown = set(values) - set(bindings)
    if unknown:
        raise InvalidInputError(
            "Request contains undeclared workflow inputs.",
            details={"unknown_inputs": sorted(unknown)},
        )

    patched = copy.deepcopy(workflow)
    for name, value in values.items():
        binding = bindings[name]
        node = patched.get(str(binding.node))
        if not isinstance(node, dict):
            raise WorkflowValidationError(
                f"Bound node {binding.node!r} for {name!r} does not exist."
            )
        inputs = node.get("inputs")
        if not isinstance(inputs, dict):
            raise WorkflowValidationError(
                f"Node {binding.node!r} has no API-format inputs object."
            )
        if binding.field not in inputs:
            raise WorkflowValidationError(
                f"Bound field {binding.field!r} is missing from node {binding.node!r}."
            )
        inputs[binding.field] = value

    return patched
