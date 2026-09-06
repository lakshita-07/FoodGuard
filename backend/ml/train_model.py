import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
df = pd.read_csv(BASE_DIR / "intelligent_packaging_iot_sensor_data.csv")

df = df[[
    "Food_Category",
    "Temperature_C",
    "Humidity_Percent",
    "Package_Age_Hours",
    "Packaging_Material",
    "Food_Safety_Risk_Level",
]].dropna()
df = df.rename(columns={
    "Food_Category": "food_type",
    "Temperature_C": "temperature",
    "Humidity_Percent": "humidity",
    "Package_Age_Hours": "days_stored",
    "Packaging_Material": "packaging",
    "Food_Safety_Risk_Level": "risk",
})
df["days_stored"] = df["days_stored"] / 24

# Use ready-meal storage records as a temporary profile for Indian food.
indian_food = df[df["food_type"] == "Ready Meal"].copy()
indian_food["food_type"] = "Indian Food"
df = pd.concat([df, indian_food], ignore_index=True)

food_encoder = LabelEncoder()
packaging_encoder = LabelEncoder()
risk_encoder = LabelEncoder()

df["food_type"] = food_encoder.fit_transform(df["food_type"])
df["packaging"] = packaging_encoder.fit_transform(df["packaging"])
df["risk"] = risk_encoder.fit_transform(df["risk"])

X = df.drop("risk", axis=1)
y = df["risk"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

model.fit(X_train, y_train)

predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)

print("Model trained successfully!")
print("Accuracy:", accuracy)

joblib.dump(model, BASE_DIR.parent / "food_model.pkl")
joblib.dump(food_encoder, BASE_DIR.parent / "food_encoder.pkl")
joblib.dump(packaging_encoder, BASE_DIR.parent / "packaging_encoder.pkl")
joblib.dump(risk_encoder, BASE_DIR.parent / "risk_encoder.pkl")

print("Model saved successfully!")