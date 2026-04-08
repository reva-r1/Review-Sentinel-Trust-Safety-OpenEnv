"""
Task loader for review-sentiment-env.
Returns the list of review entries for a given difficulty level.
"""
from typing import List, Dict, Literal
from app.data import TASKS


def load_task(level: Literal["easy", "medium", "hard"]) -> List[Dict]:
    """
    Load reviews for a given task level.

    Args:
        level: "easy", "medium", or "hard"

    Returns:
        List of review dicts with keys: review, sentiment, decision
    """
    if level not in TASKS:
        raise ValueError(f"Unknown task level '{level}'. Choose from: easy, medium, hard.")
    return TASKS[level]
