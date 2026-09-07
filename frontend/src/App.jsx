import { useState } from "react";
import "./App.css";

function App() {
  const [food, setFood] = useState("");
  const [temperature, setTemperature] = useState("");
  const [humidity, setHumidity] = useState("");
  const [daysStored, setDaysStored] = useState("");
  const [packaging, setPackaging] = useState("Glass Container");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  async function analyzeFood() {
    setLoading(true);
    setResult(null);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ food, temperature: Number(temperature), humidity: Number(humidity), days_stored: Number(daysStored), packaging })
      });
      const data = await response.json();
      setResult(response.ok ? data : { error: data.detail || "The backend rejected this request." });
    } catch {
      setResult({ error: "Could not connect to the backend." });
    }
    setLoading(false);
  }

  const foodTypes = ["Bakery", "Beverage", "Canned Food", "Dairy", "Fresh Produce", "Frozen Food", "Indian Food", "Meat Product", "Ready Meal", "Seafood", "Snack Food"];
  const packagingTypes = ["Glass Container", "Aluminum Laminate", "Biodegradable Film", "Composite Film", "PET Plastic", "Paperboard", "Vacuum Pouch"];

  return (
    <div className="page">
      <header className="topbar"><a className="brand" href="/"><span className="brand-mark">🍽</span><span>FoodGuard</span></a><span className="status"><span /> Live safety model</span></header>
      <main className="workspace">
        <aside className="sidebar">
          <div className="eyebrow">Storage check</div>
          <h1>Know before<br /><em>you serve.</em></h1>
          <p className="intro">A quick, evidence-informed read on the conditions your food has been kept in.</p>
          <section className="form-panel">
            <div className="panel-heading"><span className="step">01</span><h2>Food details</h2></div>
            <div className="form">
              <div className="field"><label htmlFor="food">Food category</label><input id="food" value={food} onChange={(e) => setFood(e.target.value)} list="food-types" placeholder="Select a food category" /><datalist id="food-types">{foodTypes.map((type) => <option value={type} key={type} />)}</datalist></div>
              <div className="field"><label htmlFor="temperature">Temperature (C)</label><input id="temperature" type="number" value={temperature} onChange={(e) => setTemperature(e.target.value)} placeholder="e.g. 4" /></div>
              <div className="field"><label htmlFor="humidity">Humidity (%)</label><input id="humidity" type="number" value={humidity} onChange={(e) => setHumidity(e.target.value)} placeholder="e.g. 60" /></div>
              <div className="field"><label htmlFor="daysStored">Days stored</label><input id="daysStored" type="number" value={daysStored} onChange={(e) => setDaysStored(e.target.value)} placeholder="e.g. 2" /></div>
              <div className="field"><label htmlFor="packaging">Packaging material</label><select id="packaging" value={packaging} onChange={(e) => setPackaging(e.target.value)}>{packagingTypes.map((type) => <option value={type} key={type}>{type}</option>)}</select></div>
            </div>
            <button className="analyze-button" onClick={analyzeFood}><span>{loading ? "Reading conditions..." : "Analyze food"}</span><span aria-hidden="true">→</span></button>
          </section>
          <p className="privacy-note">Your inputs stay private and are used only for this assessment.</p>
        </aside>
        <section className="results-area">
          <div className="results-header"><div><div className="eyebrow">Assessment</div><h2>Your food safety read</h2></div><span className="result-count">{result ? "01 / 01" : "Awaiting input"}</span></div>
          {!result && <div className="empty-state"><span className="empty-icon">✦</span><h3>Your result will appear here.</h3><p>Fill in the conditions on the left to get a clear, practical recommendation.</p></div>}
          {result && !result.error && <div className="result-content"><div className={`risk-banner ${result.risk?.toLowerCase().replace(" ", "-")}`}><span className="risk-dot" /><div><span className="risk-label">Predicted safety level</span><strong>{result.risk}</strong></div><span className="risk-arrow">↗</span></div><div className="summary-grid"><div><span>Food category</span><strong>{result.food}</strong></div><div><span>Model status</span><strong>Analyzed</strong></div></div><div className="explanation"><div className="eyebrow">AI explanation</div><p>{result.explanation}</p></div></div>}
          {result?.error && <div className="error-state"><span>!</span><div><strong>Assessment unavailable</strong><p>{result.error}</p></div></div>}
        </section>
      </main>
      <footer><span>FoodGuard</span><span>ML-assisted food storage guidance</span><span>v1.0</span></footer>
    </div>
  );
}

export default App;
