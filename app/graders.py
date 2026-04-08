"""
Deterministic graders for easy, medium, and hard tasks.

Each grader runs the environment with a set of "perfect" answers
and returns a normalized score between 0.0 and 1.0.

For external use: pass the history from env.state() to compute_score().
"""
from typing import List
from app.models import HistoryEntry


def compute_score(history: List[HistoryEntry], max_reward_per_step: float = 1.0) -> float:
    """
    Compute normalized score from episode history.

    Score = average reward across all steps, normalized to [0.0, 1.0].

    Args:
        history: list of HistoryEntry from env.state().history
        max_reward_per_step: the maximum possible reward per step (1.0)

    Returns:
        float between 0.0 and 1.0
    """
    if not history:
        return 0.0
    total = sum(entry.reward for entry in history)
    score = total / (len(history) * max_reward_per_step)
    return round(min(max(score, 0.0), 1.0), 4)


def grade_easy(history: List[HistoryEntry]) -> float:
    """Grade the easy task. Returns 0.0–1.0."""
    return compute_score(history)


def grade_medium(history: List[HistoryEntry]) -> float:
    """Grade the medium task. Returns 0.0–1.0."""
    return compute_score(history)


def grade_hard(history: List[HistoryEntry]) -> float:
    """Grade the hard task. Returns 0.0–1.0."""
    return compute_score(history)
