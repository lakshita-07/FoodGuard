import pandas as pd
import joblib

model = joblib.load("food_model.pkl")
food_encoder = joblib.load("food_encoder.pkl")
packaging_encoder = joblib.load("packaging_encoder.pkl")
risk_encoder = joblib.load("risk_encoder.pkl")

food = "Chicken"
temperature = 8
humidity = 75
days_stored = 4
packaging = "Sealed"

food_encoded = food_encoder.transform([food])[0]
packaging_encoded = packaging_encoder.transform([packaging])[0]

data = pd.DataFrame([[
    food_encoded,
    temperature,
    humidity,
    days_stored,
    packaging_encoded
]], columns=[
    "food_type",
    "temperature",
    "humidity",
    "days_stored",
    "packaging"
])

prediction = model.predict(data)

risk = risk_encoder.inverse_transform(prediction)[0]

print("Food:", food)
print("Risk:", risk)