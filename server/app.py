from fastapi import FastAPI
from app.env import ReviewSentimentEnv
from app.models import Action

app = FastAPI()

env = ReviewSentimentEnv()

@app.post("/reset")
async def reset(task: str = "easy"):
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