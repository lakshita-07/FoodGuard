from __future__ import annotations

import logging
import os
import threading
import time
from collections import deque
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from groq import APIError, Groq
from pydantic import BaseModel, ConfigDict, Field

from foodkeeper import PRODUCTS, get_options
from safety_rules import assess_food

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
logger = logging.getLogger(__name__)

cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]
app = FastAPI(title="FoodGuard API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

groq_api_key = os.getenv("GROQ_API_KEY")
client = (
    Groq(
        api_key=groq_api_key,
        timeout=float(os.getenv("GROQ_TIMEOUT_SECONDS", "4")),
        max_retries=0,
    )
    if groq_api_key
    else None
)
ai_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
rate_limit = int(os.getenv("PREDICT_RATE_LIMIT_PER_MINUTE", "30"))
rate_windows: dict[str, deque[float]] = {}
rate_windows_lock = threading.Lock()


class FoodInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    food_id: int = Field(gt=0)
    temperature: float = Field(ge=-100, le=100, allow_inf_nan=False)
    days_stored: float = Field(ge=0, le=36500, allow_inf_nan=False)


def check_rate_limit(client_ip: str, now: float | None = None) -> None:
    current_time = time.monotonic() if now is None else now
    cutoff = current_time - 60
    with rate_windows_lock:
        if client_ip not in rate_windows and len(rate_windows) >= 10000:
            expired = [
                ip
                for ip, window in rate_windows.items()
                if not window or window[-1] <= cutoff
            ]
            for ip in expired:
                rate_windows.pop(ip, None)
            if len(rate_windows) >= 10000:
                raise HTTPException(
                    status_code=503,
                    detail="The assessment service is temporarily at capacity.",
                    headers={"Retry-After": "60"},
                )

        requests = rate_windows.setdefault(client_ip, deque())
        while requests and requests[0] <= cutoff:
            requests.popleft()
        if len(requests) >= rate_limit:
            retry_after = max(1, int(requests[0] + 60 - current_time))
            raise HTTPException(
                status_code=429,
                detail="Too many assessments. Please wait before trying again.",
                headers={"Retry-After": str(retry_after)},
            )
        requests.append(current_time)


def create_explanation(product: dict, assessment: dict) -> tuple[str, str]:
    fallback = f"{assessment['basis']}\n{assessment['recommendation']}"
    if client is None:
        return fallback, "disabled"

    prompt = (
        "Rewrite the following fixed food-safety rule result as one concise, "
        "plain-language explanation and recommendation. Keep its meaning and "
        "risk level unchanged. Do not infer facts, override the rule, or claim "
        "that food is safe.\n"
        f"Food item: {product['display_name']}\n"
        f"Rule result: {assessment['risk']}\n"
        f"Rule basis: {assessment['basis']}\n"
        f"Recommendation: {assessment['recommendation']}"
    )
    try:
        response = client.chat.completions.create(
            model=ai_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        explanation = response.choices[0].message.content
        if explanation:
            return explanation, "available"
        logger.warning("Groq returned an empty explanation; using the rule explanation.")
    except APIError:
        logger.exception("Groq explanation request failed; returning the rule result.")
    return fallback, "unavailable"


@app.get("/")
def home():
    return {"message": "FoodGuard API is running"}


@app.get("/health")
def health():
    return {"status": "ok", "ai_explanations": client is not None}


@app.get("/options")
def options():
    return get_options()


@app.post("/predict")
def predict(data: FoodInput, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(client_ip)
    product = PRODUCTS.get(data.food_id)
    if product is None:
        raise HTTPException(status_code=422, detail="Choose a valid food item from /options.")
    assessment = assess_food(product, data.temperature, data.days_stored)
    explanation, explanation_status = create_explanation(product, assessment)
    return {
        "food": product["display_name"],
        "category": product["category"],
        **assessment,
        "explanation": explanation,
        "explanation_status": explanation_status,
    }
