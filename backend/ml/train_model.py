import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib

df = pd.read_csv("food_data.csv")

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

joblib.dump(model, "food_model.pkl")
joblib.dump(food_encoder, "food_encoder.pkl")
joblib.dump(packaging_encoder, "packaging_encoder.pkl")
joblib.dump(risk_encoder, "risk_encoder.pkl")

print("Model saved successfully!")