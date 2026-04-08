import os
import json
import asyncio
from typing import AsyncGenerator
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openai import OpenAI

from app.env import ReviewSentimentEnv
from app.models import Action
from app.graders import grade_easy, grade_medium, grade_hard
from app.tasks import load_task

app = FastAPI(title="Review Sentinel Dashboard")

# --- OpenEnv Required Endpoints ---

env = ReviewSentimentEnv()

@app.post("/reset")
async def reset(task: str = Query("easy")):
    result = await env.reset(task=task)
    return {
        "observation": {
            "review": result.observation.review
        },
        "reward": 0.0,
        "done": False,
        "info": result.info or {}
    }

@app.post("/step")
async def step(action: Action):
    result = await env.step(action)
    return {
        "observation": {
            "review": result.observation.review
        },
        "reward": float(result.reward),
        "done": result.done,
        "info": result.info or {}
    }

@app.get("/state")
async def state():
    return env.state().model_dump()

# Mount the static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    from fastapi.responses import FileResponse
    return FileResponse('static/index.html')

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
- Promotional or paid content
- Abusive language

IMPORTANT: Return ONLY the raw JSON object. Do not explain your choice.
Example: {"sentiment": "positive", "decision": "allow"}"""

async def get_agent_action(client: OpenAI, review_text: str, model_name: str) -> Action:
    """Ask AI to classify the review."""
    try:
        # We run this in a thread because OpenAI client is synchronous
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Review: {review_text}"}
            ],
            temperature=0.0,
        ))

        raw = response.choices[0].message.content.strip()
        
        # Robust JSON extraction
        start_idx = raw.find("{")
        end_idx = raw.rfind("}")
        
        if start_idx != -1 and end_idx != -1:
            json_str = raw[start_idx : end_idx + 1]
            data = json.loads(json_str)
        else:
            raise ValueError("No JSON found")
            
        return Action(
            sentiment=data.get("sentiment", "neutral").lower().strip(),
            decision=data.get("decision", "allow").lower().strip()
        )
    except Exception as e:
        # Instead of failing silently, raise the error so the UI can catch it!
        raise RuntimeError(f"Agent Error: {str(e)}")

@app.get("/run-task")
async def run_task_stream(task: str, api_key: str, provider: str = "openai"):
    if not api_key:
        raise HTTPException(status_code=400, detail="API Key required")
    
    if task not in GRADERS:
        raise HTTPException(status_code=400, detail="Invalid task")

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            if provider == "groq":
                client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
                model_name = "llama-3.3-70b-versatile"
            else:
                client = OpenAI(api_key=api_key)
                model_name = "gpt-4o-mini"
                
            env = ReviewSentimentEnv()
            
            # Reset the environment
            result = await env.reset(task=task)
            reviews = load_task(task)
            total_steps = len(reviews)

            yield f"data: {json.dumps({'type': 'start', 'task': task, 'total_steps': total_steps})}\n\n"
            
            for step_idx in range(1, total_steps + 1):
                if result.done:
                    break
                
                review_text = result.observation.review
                action = await get_agent_action(client, review_text, model_name)
                
                result = await env.step(action)
                
                payload = {
                    "type": "step",
                    "step": step_idx,
                    "review": review_text,
                    "action": action.model_dump(),
                    "reward": result.reward,
                    "total_steps": total_steps
                }
                yield f"data: {json.dumps(payload)}\n\n"
                
                # Small delay to make the UI look more "live"
                await asyncio.sleep(0.5)

            # Final Grader
            state = env.state()
            score = GRADERS[task](state.history)
            
            yield f"data: {json.dumps({'type': 'end', 'score': score})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


class CustomReviewRequest(BaseModel):
    api_key: str
    provider: str = "openai"
    review: str
    expected_sentiment: str | None = None
    expected_decision: str | None = None

@app.post("/analyze-custom-review")
async def analyze_custom_review(req: CustomReviewRequest):
    if not req.api_key:
        raise HTTPException(status_code=400, detail="API Key required")
    try:
        if req.provider == "groq":
            client = OpenAI(api_key=req.api_key, base_url="https://api.groq.com/openai/v1")
            model_name = "llama-3.3-70b-versatile"
        else:
            client = OpenAI(api_key=req.api_key)
            model_name = "gpt-4o-mini"
            
        action = await get_agent_action(client, req.review, model_name)
        
        reward = 0.0
        if req.expected_sentiment and req.expected_decision:
            action_sent = action.sentiment.lower()
            exp_sent = req.expected_sentiment.lower()
            if action_sent == exp_sent:
                sentiment_reward = 0.5
            elif action_sent == "neutral" or exp_sent == "neutral":
                sentiment_reward = 0.3
            else:
                sentiment_reward = 0.1
                
            action_dec = action.decision.lower()
            exp_dec = req.expected_decision.lower()
            if action_dec == exp_dec:
                decision_reward = 0.5
            else:
                decision_reward = 0.1
                
            reward = round(sentiment_reward + decision_reward, 2)
            
        result = action.model_dump()
        result["reward"] = reward
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def main():
    import uvicorn
    port = int(os.getenv("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
