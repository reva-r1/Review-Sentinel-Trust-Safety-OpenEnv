"""
ReviewSentimentEnv — the core OpenEnv environment.

Simulates a Trust & Safety review moderation task where an AI agent must:
1. Classify the sentiment of each customer review (positive / negative / neutral)
2. Decide whether the review should be allowed or flagged (spam, toxicity, etc.)
"""
from typing import Optional
from app.models import Observation, Action, EnvState, HistoryEntry, StepResult
from app.tasks import load_task


class ReviewSentimentEnv:
    def __init__(self):
        self._task_name: str = "easy"
        self._reviews: list = []
        self._current_index: int = 0
        self._history: list = []
        self._cumulative_reward: float = 0.0
        self._done: bool = False

    async def reset(self, task: str = "easy") -> StepResult:
        """
        Reset the environment and load a task.

        Args:
            task: "easy", "medium", or "hard"

        Returns:
            StepResult with the first review as observation.
        """
        self._task_name = task
        self._reviews = load_task(task)
        self._current_index = 0
        self._history = []
        self._cumulative_reward = 0.0
        self._done = False

        first_review = self._reviews[0]["review"]
        return StepResult(
            observation=Observation(review=first_review),
            reward=0.0,
            done=False,
            info={"task": task, "total_reviews": len(self._reviews)},
        )

    async def step(self, action: Action) -> StepResult:
        """
        Process one agent action.

        Args:
            action: Action with sentiment and decision fields.

        Returns:
            StepResult with next observation, reward, done flag, and info.
        """
        if self._done:
            return StepResult(
                observation=Observation(review="[EPISODE ENDED]"),
                reward=0.0,
                done=True,
                info={"error": "Episode already finished. Call reset()."},
            )

        current = self._reviews[self._current_index]
        true_sentiment = current["sentiment"]
        true_decision = current["decision"]

        # --- Sentiment reward (0.0 to 0.5) ---
        if action.sentiment == true_sentiment:
            sentiment_reward = 0.5
        elif action.sentiment == "neutral" and true_sentiment in ("positive", "negative"):
            sentiment_reward = 0.3
        elif true_sentiment == "neutral" and action.sentiment in ("positive", "negative"):
            sentiment_reward = 0.3
        else:
            # completely wrong: predicted positive when negative, or vice versa
            sentiment_reward = 0.1

        # --- Decision reward (0.0 to 0.5) ---
        if action.decision == true_decision:
            decision_reward = 0.5
        else:
            decision_reward = 0.1

        total_reward = round(sentiment_reward + decision_reward, 2)
        self._cumulative_reward += total_reward

        # Record history
        entry = HistoryEntry(
            step=self._current_index + 1,
            review=current["review"],
            predicted_sentiment=action.sentiment,
            predicted_decision=action.decision,
            true_sentiment=true_sentiment,
            true_decision=true_decision,
            reward=total_reward,
        )
        self._history.append(entry)

        # Advance to next review
        self._current_index += 1

        if self._current_index >= len(self._reviews):
            self._done = True
            return StepResult(
                observation=Observation(review="[ALL REVIEWS PROCESSED]"),
                reward=total_reward,
                done=True,
                info={
                    "step": self._current_index,
                    "sentiment_reward": sentiment_reward,
                    "decision_reward": decision_reward,
                },
            )

        next_review = self._reviews[self._current_index]["review"]
        return StepResult(
            observation=Observation(review=next_review),
            reward=total_reward,
            done=False,
            info={
                "step": self._current_index,
                "sentiment_reward": sentiment_reward,
                "decision_reward": decision_reward,
            },
        )

    def state(self) -> EnvState:
        """Return the full internal state of the environment."""
        return EnvState(
            task=self._task_name,
            current_index=self._current_index,
            total_reviews=len(self._reviews),
            history=self._history,
            cumulative_reward=round(self._cumulative_reward, 4),
            done=self._done,
        )

    async def close(self):
        """Cleanup (no-op for this environment)."""
        pass
