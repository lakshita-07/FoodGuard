# FoodGuard

FoodGuard is an AI-assisted food storage safety analyzer. It combines a scikit-learn risk model with a Groq-generated explanation based on the food category and storage conditions.

## Features

- Food safety risk prediction
- Temperature, humidity, storage time, and packaging inputs
- AI explanation and storage recommendation
- Support for multiple food categories and packaging materials
- Responsive React interface
- FastAPI backend

## Project Structure

```text
foodguard/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── ml/
│       ├── food_data.csv
│       ├── intelligent_packaging_iot_sensor_data.csv
│       └── train_model.py
└── frontend/
    ├── src/
    └── package.json
```

## Requirements

- Python 3.9 or newer
- Node.js and npm
- A Groq API key

## Backend Setup

Open a terminal and run:

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Create `backend/.env`:

```env
GROQ_API_KEY=your_groq_api_key
```

Start the API:

```bash
.venv/bin/uvicorn main:app --reload --port 8000
```

The API runs at `http://127.0.0.1:8000`.

Test it by opening:

```text
http://127.0.0.1:8000/
```

## Frontend Setup

In a second terminal:

```bash
cd frontend
npm install
```

Create `frontend/.env`:

```env
VITE_API_URL=http://127.0.0.1:8000
```

Start the frontend:

```bash
npm run dev
```

Open the local URL shown by Vite, usually `http://localhost:5173`.

## Supported Inputs

Food categories currently supported:

- Bakery
- Beverage
- Canned Food
- Dairy
- Fresh Produce
- Frozen Food
- Indian Food
- Meat Product
- Ready Meal
- Seafood
- Snack Food

Packaging materials currently supported:

- Glass Container
- Aluminum Laminate
- Biodegradable Film
- Composite Film
- PET Plastic
- Paperboard
- Vacuum Pouch

## Retraining the Model

The current model is trained from the intelligent packaging dataset. To retrain it after changing the data:

```bash
cd backend/ml
../.venv/bin/python train_model.py
```

The script writes the model and encoder files into `backend/`.

`Indian Food` currently uses the dataset's `Ready Meal` records as a temporary storage profile. It should eventually be replaced with Indian-food-specific training data.

## Database Status

Supabase database saving is currently disabled. Predictions are processed and displayed, but they are not persisted after the request finishes.

## Validation

Build the frontend with:

```bash
cd frontend
npm run build
```

Run the backend syntax check with:

```bash
cd backend
.venv/bin/python -m py_compile main.py
```

## Important Note

FoodGuard provides an estimate based on its training data and should not be treated as a guarantee that food is safe or unsafe. Use official food-safety guidance for final decisions.
