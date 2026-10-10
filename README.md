# FoodGuard

FoodGuard checks food storage conditions using USDA time-and-temperature
guidance and product-specific storage times from the USDA FSIS FoodKeeper data.
The risk assessment is deterministic and does not depend on a trained ML model
or an AI API.

## What the assessment does

- Applies the USDA danger zone of 40–140°F (4.4–60°C), with a maximum of 2
  unrefrigerated hours, or 1 hour above 90°F (32.2°C).
- Uses the selected FoodKeeper product's refrigerator, pantry, and freezer
quality guidance when available.
- Reports its rule basis, a qualitative confidence level, and an explicit
warning when the request falls outside its documented assessment range.
- Optionally uses Groq to rephrase the already-computed explanation. If Groq is
  missing, times out, or returns an API error, the deterministic assessment is
  still returned.

This is consumer guidance, not a guarantee that food is safe. Risk categories
are not probabilities. The check cannot determine whether a product is open,
damaged, contaminated, or has been handled correctly at every point.

## FoodKeeper data

`backend/data/foodkeeper.json` contains the USDA FSIS FoodKeeper public-domain
data snapshot (data version 128; source file last modified in 2018). The
`/options` endpoint returns the categories and specific products from this
snapshot. Product shelf-life data may vary with preparation and package state;
follow the product label and check the current USDA FoodKeeper entry.

Sources:

- [USDA FSIS FoodKeeper data](https://www.fsis.usda.gov/shared/data/EN/foodkeeper.json)
- [USDA FSIS danger zone guidance](https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/danger-zone-40f-140f)
- [FoodSafety.gov cold food storage charts](https://www.foodsafety.gov/food-safety-charts/cold-food-storage-charts)
- [FoodSafety.gov FoodKeeper app](https://www.foodsafety.gov/keep-food-safe/foodkeeper-app)

## Requirements

- Python 3.9 or newer
- Node.js 20.19+ or 22.12+
- A Groq API key is optional

## Backend setup

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
.venv/bin/uvicorn main:app --reload --port 8000
```

The API is available at `http://127.0.0.1:8000`. `GET /health` reports service
and optional AI status; `GET /options` supplies FoodKeeper categories, food
items, and packaging options.

To enable optional explanation rephrasing, set `GROQ_API_KEY` in `backend/.env`.
Do not commit credentials. When enabled, FoodGuard sends the selected item and
rule-derived result to Groq only to rephrase the explanation; Groq never
determines or changes the risk result.

## Frontend setup

```bash
cd frontend
npm ci
cp .env.example .env
npm run dev
```

The frontend defaults to `http://127.0.0.1:8000` when `VITE_API_URL` is unset.
Set `VITE_API_URL` to the deployed backend URL for production.

## Configuration

Backend configuration is documented in [`backend/.env.example`](backend/.env.example):

- `GROQ_API_KEY`: optional; omit to disable AI wording.
- `GROQ_MODEL`: optional model name.
- `GROQ_TIMEOUT_SECONDS`: AI timeout; defaults to 4 seconds.
- `CORS_ORIGINS`: comma-separated browser origins.
- `PREDICT_RATE_LIMIT_PER_MINUTE`: per-client in-memory limit; defaults to 30.

The in-memory rate limit is per process. Deployments with multiple workers or
instances should also enforce a shared limit at their gateway.

## Tests and checks

```bash
cd backend
.venv/bin/python -m unittest discover -s tests -v
cd ../frontend
npm run lint
npm run build
```

GitHub Actions runs these backend and frontend checks on pushes and pull
requests.

## Project layout

```text
foodguard/
├── backend/
│   ├── data/foodkeeper.json
│   ├── foodkeeper.py
│   ├── main.py
│   ├── safety_rules.py
│   ├── requirements.txt
│   └── tests/
└── frontend/
    ├── src/
    └── package.json
```

The repository does not currently declare a license for its application code.
The USDA FoodKeeper data is public domain as U.S. government work.
