"""Illustrative organism-authored decision strategy.

Not an executable arena package. Demonstrates the shape of a pure strategy
function: no provider credentials, host system calls or world state writes.
"""

from typing import Any


def decide(observation: dict[str, Any]) -> dict[str, Any]:
    """Choose one permitted in-world action."""
    energy = int(observation.get("self", {}).get("energy", 0))
    weather = observation.get("weather", "normal")
    opportunities = observation.get("opportunities", [])

    if energy < 20:
        return {"action": "wait"}
    if weather == "drought" and energy < 100:
        return {"action": "wait"}
    if "task-duel" in opportunities and energy >= 60:
        return {"action": "compete", "game_id": "task-duel", "stake": 30}
    return {"action": "wait"}
