import { useState } from "react";
import "./App.css";

function App() {
  const [food, setFood] = useState("");
  const [temperature, setTemperature] = useState("");
  const [humidity, setHumidity] = useState("");
  const [daysStored, setDaysStored] = useState("");
  const [packaging, setPackaging] = useState("Sealed");

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  async function analyzeFood() {
    setLoading(true);
    setResult(null);

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/predict`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          food: food,
          temperature: Number(temperature),
          humidity: Number(humidity),
          days_stored: Number(daysStored),
          packaging: packaging
        })
      });

      const data = await response.json();
      setResult(data);

    } catch (error) {
      setResult({
        error: "Could not connect to the backend."
      });
    }

    setLoading(false);
  }

  return (
    <div className="page">

      <header>
        <h1>FoodGuard</h1>
        <p>AI-powered food storage risk analyzer</p>
      </header>

      <main>

        <section className="card">

          <h2>Analyze Your Food</h2>

          <div className="form">

            <div className="field">
              <label>Food</label>
              <input
                value={food}
                onChange={(e) => setFood(e.target.value)}
                placeholder="Example: Chicken"
              />
            </div>

            <div className="field">
              <label>Temperature (°C)</label>
              <input
                type="number"
                value={temperature}
                onChange={(e) => setTemperature(e.target.value)}
                placeholder="8"
              />
            </div>

            <div className="field">
              <label>Humidity (%)</label>
              <input
                type="number"
                value={humidity}
                onChange={(e) => setHumidity(e.target.value)}
                placeholder="75"
              />
            </div>

            <div className="field">
              <label>Days Stored</label>
              <input
                type="number"
                value={daysStored}
                onChange={(e) => setDaysStored(e.target.value)}
                placeholder="4"
              />
            </div>

            <div className="field">
              <label>Packaging</label>
              <select
                value={packaging}
                onChange={(e) => setPackaging(e.target.value)}
              >
                <option value="Sealed">Sealed</option>
                <option value="Open">Open</option>
              </select>
            </div>

          </div>

          <button onClick={analyzeFood}>
            {loading ? "Analyzing..." : "Analyze Food"}
          </button>

        </section>

        {result && !result.error && (
          <section className="result">

            <h2>Analysis Result</h2>

            <div className="risk">
              Risk Level: <strong>{result.risk}</strong>
            </div>

            <div className="explanation">
              <h3>AI Explanation</h3>
              <p>{result.explanation}</p>
            </div>

          </section>
        )}

        {result?.error && (
          <section className="result">
            <p>{result.error}</p>
          </section>
        )}

      </main>

      <footer>
        FoodGuard • ML + FastAPI + Groq + Supabase
      </footer>

    </div>
  );
}

export default App;
