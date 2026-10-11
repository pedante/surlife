"""M1.3 trusted feasible-action menu: enumerate costs, never action rewards.

This interface changes the organism's observation, not the referee's
settlement. Actions are still model-generated. Nothing is auto-repaired.
"""
from __future__ import annotations

import json

from .core import Observation, Task


def legal_masks(task: Task) -> list[int]:
    if not 1 <= len(task.items) <= 8:
        raise ValueError("action menu supports tasks of one through eight items")
    return [mask for mask in range(1 << len(task.items)) if task.score(mask) >= 0]


def menu_messages(messages: list[dict], obs: Observation) -> tuple[list[dict], list[int]]:
    """Return fresh messages and admissible masks; never expose reward totals or optimum."""
    allowed = legal_masks(obs.task)
    options = [{
        "mask": mask,
        "selected_cost": sum(cost for i, (cost, _) in enumerate(obs.task.items) if mask & (1 << i)),
    } for mask in allowed]
    revised = [dict(message) for message in messages]
    revised[0]["content"] += (
        "\nM1.3 action contract: the referee has listed all cost-feasible masks. "
        "Select EXACTLY one mask from allowed_masks. The masks were filtered "
        "for capacity only, not ranked by reward. Compare item rewards to choose "
        "your preferred feasible action. Do not output a new mask, and set "
        "soul_update to the empty string. Do not wait."
    )
    data = json.loads(revised[-1]["content"])
    if not isinstance(data, dict) or data.get("task") != obs.task.as_dict():
        raise ValueError("action observation and menu task disagree")
    data["allowed_masks"] = options
    revised[-1]["content"] = json.dumps(data, sort_keys=True)
    return revised, allowed
