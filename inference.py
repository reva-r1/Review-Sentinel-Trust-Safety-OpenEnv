"""
Baseline inference script for review-sentiment-env.

Uses the OpenAI API client to run an LLM agent against all 3 tasks.
Reads credentials from environment variables.
Logs output strictly in [START], [STEP], [END] format.
"""
import os
import sys
import json
import asyncio
from typing import List

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openai import OpenAI
from app.env import ReviewSentimentEnv
from app.models import Action
from app.graders import grade_easy, grade_medium, grade_hard

# ── Config ────────────────────────────────────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.getenv("HF_TOKEN")

# Optional — if you use from_docker_image():
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")

BENCHMARK = "review-sentiment-env"
MAX_STEPS = 15  # generous upper bound for any task
SUCCESS_SCORE_THRESHOLD = 0.7

GRADERS = {
    "easy": grade_easy,
    "medium": grade_medium,
    "hard": grade_hard,
}

SYSTEM_PROMPT = """You are a Trust & Safety review moderator.

For each customer review you receive, you must return a JSON object with exactly two fields:

1. "sentiment": classify the review as "positive", "negative", or "neutral"
2. "decision": decide whether to "allow" the review or "flag" it for moderation

Flag a review if it contains:
- Spam or suspicious links
- Promotional or paid content disguised as a review
- Abusive language or personal attacks
- Fake or incentivized reviews

Otherwise, allow it — even if the sentiment is negative. Negative opinions are fine; policy violations are not.

IMPORTANT: Return ONLY the raw JSON object. No markdown, no explanation, no code blocks.
Example: {"sentiment": "positive", "decision": "allow"}"""


# ── Logging helpers ───────────────────────────────────────────────────────────
def log_start(task: str, env: str, model: str):
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error=None):
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]):
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}",
        flush=True,
    )


# ── Agent logic ───────────────────────────────────────────────────────────────
def get_agent_action(client: OpenAI, review_text: str, history: List[str]) -> Action:
    """Ask the LLM to classify the review and return a typed Action."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]
    # Add history for context
    for h in history[-5:]:  # keep context window small
        messages.append({"role": "user", "content": h})

    messages.append({"role": "user", "content": f"Review: {review_text}"})

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.0,
        max_tokens=100,
    )

    raw = response.choices[0].message.content.strip()

    # Parse JSON from the response
    try:
        # Handle cases where model wraps in markdown code blocks
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        data = json.loads(raw)
        sentiment = data.get("sentiment", "neutral").lower().strip()
        decision = data.get("decision", "allow").lower().strip()

        # Validate values
        if sentiment not in ("positive", "negative", "neutral"):
            sentiment = "neutral"
        if decision not in ("allow", "flag"):
            decision = "allow"

        return Action(sentiment=sentiment, decision=decision)

    except (json.JSONDecodeError, KeyError, AttributeError):
        # Fallback if LLM gives garbage
        return Action(sentiment="neutral", decision="allow")


# ── Main loop ─────────────────────────────────────────────────────────────────
async def run_task(client: OpenAI, env: ReviewSentimentEnv, task_name: str):
    """Run a single task and return the final score."""
    history: List[str] = []
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    try:
        result = await env.reset(task=task_name)
        review_text = result.observation.review

        for step in range(1, MAX_STEPS + 1):
            if result.done:
                break

            action = get_agent_action(client, review_text, history)
            action_str = json.dumps({"sentiment": action.sentiment, "decision": action.decision})

            result = await env.step(action)

            reward = result.reward or 0.0
            done = result.done
            error = None

            rewards.append(reward)
            steps_taken = step

            log_step(step=step, action=action_str, reward=reward, done=done, error=error)

            history.append(f"Review: {review_text} -> {action_str} (reward: {reward:.2f})")
            review_text = result.observation.review

            if done:
                break

        # Grade using the appropriate grader
        grader = GRADERS[task_name]
        state = env.state()
        score = grader(state.history)
        success = score >= SUCCESS_SCORE_THRESHOLD

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return score


async def main():
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
    env = ReviewSentimentEnv()

    print("=" * 60)
    print("  REVIEW-SENTIMENT-ENV — Baseline Inference")
    print("=" * 60)
    print()

    all_scores = {}
    for task_name in ["easy", "medium", "hard"]:
        print(f"\n--- Running task: {task_name} ---")
        score = await run_task(client, env, task_name)
        all_scores[task_name] = score
        print(f"--- Task {task_name} score: {score:.4f} ---\n")

    print("=" * 60)
    print("  FINAL RESULTS")
    print("=" * 60)
    for task_name, score in all_scores.items():
        print(f"  {task_name:>8}: {score:.4f}")
    avg = sum(all_scores.values()) / len(all_scores)
    print(f"  {'average':>8}: {avg:.4f}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
