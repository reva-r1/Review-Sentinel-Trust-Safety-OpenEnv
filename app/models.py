from pydantic import BaseModel
from typing import Optional, List, Literal


class Observation(BaseModel):
    """What the agent sees at each step."""
    review: str


class Action(BaseModel):
    """What the agent must return at each step."""
    sentiment: Literal["positive", "negative", "neutral"]
    decision: Literal["allow", "flag"]


class Reward(BaseModel):
    """Reward breakdown for a single step."""
    sentiment_reward: float
    decision_reward: float
    total: float


class HistoryEntry(BaseModel):
    """A single step's record."""
    step: int
    review: str
    predicted_sentiment: str
    predicted_decision: str
    true_sentiment: str
    true_decision: str
    reward: float


class EnvState(BaseModel):
    """Full internal state of the environment."""
    task: str
    current_index: int
    total_reviews: int
    history: List[HistoryEntry]
    cumulative_reward: float
    done: bool

 
class StepResult(BaseModel):
    observation: Observation
    reward: float
    done: bool
    info: dict