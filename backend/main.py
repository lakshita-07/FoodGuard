from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import joblib
from dotenv import load_dotenv
from groq import Groq
from supabase import create_client
import os

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = joblib.load("food_model.pkl")
food_encoder = joblib.load("food_encoder.pkl")
packaging_encoder = joblib.load("packaging_encoder.pkl")
risk_encoder = joblib.load("risk_encoder.pkl")

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

class FoodInput(BaseModel):
    food: str
    temperature: float
    humidity: float
    days_stored: int
    packaging: str


@app.get("/")
def home():
    return {"message": "FoodGuard API is running"}


@app.post("/predict")
def predict(data: FoodInput):

    food_encoded = food_encoder.transform([data.food])[0]
    packaging_encoded = packaging_encoder.transform([data.packaging])[0]

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

Food: {data.food}
Temperature: {data.temperature}°C
Humidity: {data.humidity}%
Days stored: {data.days_stored}
Packaging: {data.packaging}
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

    supabase.table("predictions").insert({
        "food_type": data.food,
        "temperature": data.temperature,
        "humidity": data.humidity,
        "days_stored": data.days_stored,
        "packaging": data.packaging,
        "risk": risk,
        "explanation": explanation
    }).execute()

    return {
        "food": data.food,
        "risk": risk,
        "explanation": explanation
    }
@app.get("/history")
def get_history():

    response = supabase.table("predictions") \
        .select("*") \
        .order("created_at", desc=True) \
        .execute()

    return response.data

