import { useEffect, useState } from "react";
import "./App.css";

const API_URL = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(
  /\/$/,
  "",
);

async function requestJson(url, options = {}, timeoutMs = 8000) {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    const data = await response.json().catch(() => ({}));
    return { response, data };
  } finally {
    window.clearTimeout(timeout);
  }
}

function describeError(error) {
  if (Array.isArray(error)) {
    return error
      .map((item) => {
        const field = item.loc?.at(-1);
        return field ? `${field}: ${item.msg}` : item.msg;
      })
      .join(" ");
  }
  return typeof error === "string" ? error : "The backend rejected this request.";
}

function App() {
  const [foodCategories, setFoodCategories] = useState([]);
  const [foodItems, setFoodItems] = useState([]);
  const [foodCategory, setFoodCategory] = useState("");
  const [foodId, setFoodId] = useState("");
  const [temperature, setTemperature] = useState("");
  const [daysStored, setDaysStored] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [backendStatus, setBackendStatus] = useState("checking");
  const [aiEnabled, setAiEnabled] = useState(false);

  useEffect(() => {
    let active = true;

    async function loadOptions() {
      try {
        const [{ response: healthResponse, data: health }, optionsResult] =
          await Promise.all([
            requestJson(`${API_URL}/health`, {}, 3000),
            requestJson(`${API_URL}/options`, {}, 3000),
          ]);
        if (!healthResponse.ok || !optionsResult.response.ok) {
          throw new Error("The backend did not return its service options.");
        }
        if (active) {
          setFoodCategories(optionsResult.data.food_categories ?? []);
          setFoodItems(optionsResult.data.food_items ?? []);
          setAiEnabled(Boolean(health.ai_explanations));
          setBackendStatus("online");
        }
      } catch {
        if (active) {
          setBackendStatus("offline");
        }
      }
    }

    loadOptions();
    return () => {
      active = false;
    };
  }, []);

  async function analyzeFood(event) {
    event.preventDefault();
    if (loading) return;

    setLoading(true);
    setResult(null);
    try {
      const { response, data } = await requestJson(
        `${API_URL}/predict`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            food_id: Number(foodId),
            temperature: Number(temperature),
            days_stored: Number(daysStored),
          }),
        },
        8000,
      );
      if (!response.ok) {
        setResult({ error: describeError(data.detail) });
        return;
      }
      setResult(data);
      setBackendStatus("online");
    } catch (error) {
      setBackendStatus("offline");
      setResult({
        error:
          error.name === "AbortError"
            ? "The assessment request timed out. Please try again."
            : "Could not connect to the backend. Check that the API is running.",
      });
    } finally {
      setLoading(false);
    }
  }

  const privacyNote = aiEnabled
    ? "Your assessment is computed by FoodGuard. The selected item and rule details are sent to Groq only to rephrase the explanation."
    : "Your assessment is computed by FoodGuard. No inputs are sent to an AI explanation service.";

  return (
    <div className="page">
      <header className="topbar">
        <a className="brand" href="/" aria-label="FoodGuard home">
          <span className="brand-mark" aria-hidden="true">
            🍽
          </span>
          <span>FoodGuard</span>
        </a>
        <span className={`status status-${backendStatus}`} role="status">
          <span aria-hidden="true" />
          {backendStatus === "checking"
            ? "Checking backend"
            : backendStatus === "online"
              ? "Backend online"
              : "Backend offline"}
        </span>
      </header>

      <main className="workspace">
        <aside className="sidebar">
          <div className="eyebrow">Storage check</div>
          <h1>
            Know before
            <br />
            <em>you serve.</em>
          </h1>
          <p className="intro">
            A practical check based on official time-and-temperature food
            safety guidance.
          </p>

          <section className="form-panel" aria-labelledby="food-details">
            <div className="panel-heading">
              <span className="step">01</span>
              <h2 id="food-details">Food details</h2>
            </div>
            <form className="form" onSubmit={analyzeFood}>
              <div className="field">
                <label htmlFor="food-category">Food category</label>
                <select
                  id="food-category"
                  value={foodCategory}
                  onChange={(event) => {
                    setFoodCategory(event.target.value);
                    setFoodId("");
                  }}
                  required
                  disabled={foodCategories.length === 0}
                >
                  <option value="">Select a food category</option>
                  {foodCategories.map((category) => (
                    <option value={category} key={category}>
                      {category}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label htmlFor="food">Food item</label>
                <select
                  id="food"
                  value={foodId}
                  onChange={(event) => setFoodId(event.target.value)}
                  required
                  disabled={!foodCategory}
                >
                  <option value="">Select a food item</option>
                  {foodItems
                    .filter((item) => item.category === foodCategory)
                    .map((item) => (
                      <option value={item.id} key={item.id}>
                        {item.display_name}
                      </option>
                    ))}
                </select>
              </div>
              <div className="field">
                <label htmlFor="temperature">Storage temperature (°C)</label>
                <input
                  id="temperature"
                  type="number"
                  value={temperature}
                  onChange={(event) => setTemperature(event.target.value)}
                  min="-100"
                  max="100"
                  step="any"
                  placeholder="e.g. 4"
                  required
                />
              </div>
              <div className="field">
                <label htmlFor="daysStored">Time at this temperature (days)</label>
                <input
                  id="daysStored"
                  type="number"
                  value={daysStored}
                  onChange={(event) => setDaysStored(event.target.value)}
                  min="0"
                  max="36500"
                  step="any"
                  placeholder="e.g. 2"
                  required
                />
                <span className="field-hint">
                  Enter the total time continuously held at this temperature.
                </span>
              </div>
              <button
                className="analyze-button"
                type="submit"
                disabled={loading || foodCategories.length === 0 || !foodId}
              >
                <span>
                  {loading
                    ? "Checking conditions..."
                    : foodCategories.length === 0
                      ? "Waiting for backend..."
                      : "Check food"}
                </span>
                <span aria-hidden="true">→</span>
              </button>
            </form>
          </section>
          <p className="privacy-note">{privacyNote}</p>
        </aside>

        <section className="results-area" aria-labelledby="assessment-title">
          <div className="results-header">
            <div>
              <div className="eyebrow">Assessment</div>
              <h2 id="assessment-title">Your food safety read</h2>
            </div>
            <span className="result-count">
              {result ? "01 / 01" : "Awaiting input"}
            </span>
          </div>

          <div className="assessment-result" aria-live="polite" aria-atomic="true">
            {!result && (
              <div className="empty-state">
                <span className="empty-icon" aria-hidden="true">
                  ✦
                </span>
                <h3>Your result will appear here.</h3>
                <p>
                  Enter the food category, temperature, and time to get a
                  time-and-temperature assessment.
                </p>
              </div>
            )}
            {result && !result.error && (
              <div className="result-content">
                <div
                  className={`risk-banner ${result.risk?.toLowerCase()}`}
                  aria-label={`Rule-based risk assessment: ${result.risk}`}
                >
                  <span className="risk-dot" aria-hidden="true" />
                  <div>
                    <span className="risk-label">Rule-based risk level</span>
                    <strong>{result.risk}</strong>
                  </div>
                </div>
                {result.out_of_range && (
                  <p className="range-warning" role="alert">
                    {result.range_warning}
                  </p>
                )}
                <div className="summary-grid">
                  <div>
                    <span>Food category</span>
                    <strong>{result.food}</strong>
                  </div>
                  <div>
                    <span>Rule confidence</span>
                    <strong>{result.confidence}</strong>
                  </div>
                </div>
                <div className="explanation">
                  <div className="eyebrow">Why this result</div>
                  <p>{result.explanation}</p>
                  <p className="confidence-note">{result.confidence_note}</p>
                  <p className="source-note">
                    Guidance source: USDA FSIS / FoodSafety.gov. Category
                    storage times are broad guides; check the specific FoodKeeper
                    entry and product label.
                  </p>
                </div>
              </div>
            )}
            {result?.error && (
              <div className="error-state" role="alert">
                <span aria-hidden="true">!</span>
                <div>
                  <strong>Assessment unavailable</strong>
                  <p>{result.error}</p>
                </div>
              </div>
            )}
          </div>
        </section>
      </main>

      <footer>
        <span>FoodGuard</span>
        <span>Food-safety guidance, not a guarantee of safety</span>
        <span>v1.0</span>
      </footer>
    </div>
  );
}

export default App;
