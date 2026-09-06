from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import joblib
from dotenv import load_dotenv
from groq import Groq
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","https://food-guard-smoky.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = joblib.load(BASE_DIR / "food_model.pkl")
food_encoder = joblib.load(BASE_DIR / "food_encoder.pkl")
packaging_encoder = joblib.load(BASE_DIR / "packaging_encoder.pkl")
risk_encoder = joblib.load(BASE_DIR / "risk_encoder.pkl")

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class FoodInput(BaseModel):
    food: str
    temperature: float
    humidity: float
    days_stored: float
    packaging: str


@app.get("/")
def home():
    return {"message": "FoodGuard API is running"}


@app.post("/predict")
def predict(data: FoodInput):

    food_values = {value.casefold(): value for value in food_encoder.classes_}
    packaging_values = {value.casefold(): value for value in packaging_encoder.classes_}
    food = food_values.get(data.food.strip().casefold())
    packaging = packaging_values.get(data.packaging.strip().casefold())

    if food is None:
        supported_foods = ", ".join(food_encoder.classes_)
        raise HTTPException(
            status_code=400,
            detail=f"Food not supported. Choose: {supported_foods}."
        )

    if packaging is None:
        raise HTTPException(
            status_code=400,
            detail=f"Packaging not supported. Choose: {', '.join(packaging_encoder.classes_)}."
        )

    food_encoded = food_encoder.transform([food])[0]
    packaging_encoded = packaging_encoder.transform([packaging])[0]

    input_data = pd.DataFrame([[
        food_encoded,
        data.temperature,
        data.humidity,
        data.days_stored,
        packaging_encoded
    ]], columns=[
        "food_type",
        "temperature",
        "humidity",
        "days_stored",
        "packaging"
    ])

    prediction = model.predict(input_data)

    risk = risk_encoder.inverse_transform(prediction)[0]

    prompt = f"""
You are a food storage assistant.

Food: {food}
Temperature: {data.temperature}°C
Humidity: {data.humidity}%
Days stored: {data.days_stored}
Packaging: {packaging}
ML predicted risk: {risk}

Explain briefly why the risk may be {risk} and give one practical
storage recommendation.

Do not claim that this prediction guarantees that food is safe or unsafe.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",   
                  messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3
    )

    explanation = response.choices[0].message.content

    return {
        "food": food,
        "risk": risk,
        "explanation": explanation
    }

