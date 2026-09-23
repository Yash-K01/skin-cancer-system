import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { Link } from "react-router-dom";
import {
  predict7Class,
  predictBinary,
  explain7Class,
  submitFeedback,
} from "../api/endpoints";
import ProbabilityChart from "../components/ProbabilityChart";

export default function Predict() {
  const { user, logout } = useAuth();
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [binaryResult, setBinaryResult] = useState(null);
  const [saliency, setSaliency] = useState(null);
  const [error, setError] = useState("");

  const handleFile = (f) => {
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
    setBinaryResult(null);
    setSaliency(null);
    setError("");
  };

  const handlePredict = async () => {
    if (!file) return;
    setLoading(true);
    setError("");
    try {
      const [r7, rBin] = await Promise.all([
        predict7Class(file),
        predictBinary(file),
      ]);
      setResult(r7.data);
      setBinaryResult(rBin.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Prediction failed");
    } finally {
      setLoading(false);
    }
  };

  const handleExplain = async () => {
    if (!file) return;
    setLoading(true);
    try {
      const r = await explain7Class(file);
      setSaliency(r.data.saliency_png_b64);
    } catch (err) {
      setError(err.response?.data?.detail || "Explain failed");
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async (agrees) => {
    if (!result) return;
    try {
      await submitFeedback({
        prediction_id: result.prediction_id,
        doctor_label: result.predicted_class,
        agrees,
        notes: agrees ? "" : "Doctor disagrees",
      });
      alert("Feedback recorded");
    } catch (err) {
      alert("Feedback failed");
    }
  };

  const isUncertain = result?.status === "uncertain";

  return (
    <div className="page">
      <header className="topbar">
        <h1>Skin Cancer Detection</h1>
        <div>
          <span>{user?.email}</span>
          {user?.role === "admin" && (
            <Link to="/admin" className="link-btn">Admin</Link>
          )}
          <button onClick={logout} className="logout-btn">Logout</button>
        </div>
      </header>

      <main className="predict-layout">
        <section className="upload-panel">
          <h2>Upload Dermoscopy Image</h2>
          <input
            type="file"
            accept="image/*"
            onChange={(e) => handleFile(e.target.files[0])}
          />
          {preview && (
            <img src={preview} alt="preview" className="preview" />
          )}
          <div className="actions">
            <button onClick={handlePredict} disabled={!file || loading}>
              {loading ? "Analyzing..." : "Analyze"}
            </button>
            <button onClick={handleExplain} disabled={!file || loading} className="secondary">
              Show Saliency
            </button>
          </div>
        </section>

        <section className="result-panel">
          {error && <div className="error">{error}</div>}

          {binaryResult && (
            <div className="card">
              <h3>Binary Triage</h3>
              <div className={`verdict ${binaryResult.predicted_class.toLowerCase()}`}>
                {binaryResult.predicted_class} — {(binaryResult.confidence * 100).toFixed(1)}%
              </div>
            </div>
          )}

          {result && (
            <>
              <div className="card">
                <h3>7-Class Prediction</h3>
                <div className={`verdict ${result.status}`}>
                  {result.predicted_class} — {(result.confidence * 100).toFixed(1)}%
                </div>

                {isUncertain && (
                  <div className="warning">
                    Model is uncertain ({result.reason}).
                    Please review carefully or submit as new case.
                  </div>
                )}

                <ProbabilityChart
                  probabilities={result.probabilities}
                  predicted={result.predicted_class}
                />

                <div className="feedback-row">
                  <button onClick={() => handleFeedback(true)}>✓ Agree</button>
                  <button onClick={() => handleFeedback(false)} className="secondary">
                    ✗ Disagree
                  </button>
                  {isUncertain && (
                    <Link to="/new-case" state={{ preview }} className="link-btn">
                      Submit as New Case
                    </Link>
                  )}
                </div>
              </div>

              {saliency && (
                <div className="card">
                  <h3>Saliency Map (Occlusion Sensitivity)</h3>
                  <img
                    src={`data:image/png;base64,${saliency}`}
                    alt="saliency"
                    className="saliency-img"
                  />
                </div>
              )}
            </>
          )}
        </section>
      </main>
    </div>
  );
}