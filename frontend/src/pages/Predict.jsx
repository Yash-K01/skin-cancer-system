import { useState, useRef } from "react";
import { useAuth } from "../context/AuthContext";
import { Link } from "react-router-dom";
import { predict7Class, predictBinary, submitFeedback } from "../api/endpoints";
import ProbabilityChart from "../components/ProbabilityChart";
import Logo from "../components/Logo";

export default function Predict() {
  const { user, logout } = useAuth();
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [binaryResult, setBinaryResult] = useState(null);
  const [error, setError] = useState("");
  const [prescription, setPrescription] = useState("");

  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);

  const handleFile = (f) => {
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
    setBinaryResult(null);
    setError("");
    setPrescription("");
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

      // Placeholder for NVIDIA AI prescription generation
      // const rx = await generatePrescription({ prediction: r7.data, binary: rBin.data });
      // setPrescription(rx);
    } catch (err) {
      setError(err.response?.data?.detail || "Prediction failed");
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
        <h1 className="brand">
          <Logo size={34} />
          <span>DermaScan — Clinical Triage</span>
        </h1>
        <div>
          <span className="user-chip">{user?.email}</span>
          {user?.role === "admin" && (
            <Link to="/admin" className="link-btn">Admin</Link>
          )}
          <button onClick={logout} className="logout-btn">Logout</button>
        </div>
      </header>

      <main className="predict-layout">
        {/* ---------- LEFT: UPLOAD ---------- */}
        <section className="upload-panel">
          <div className="panel-head">
            <h2>Patient Image</h2>
            <p className="panel-sub">Dermoscopy · 224×224 recommended</p>
          </div>

          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={(e) => handleFile(e.target.files[0])}
            style={{ display: "none" }}
          />
          <input
            ref={cameraInputRef}
            type="file"
            accept="image/*"
            capture="environment"
            onChange={(e) => handleFile(e.target.files[0])}
            style={{ display: "none" }}
          />

          <div className="upload-options">
            <button
              type="button"
              className="upload-option"
              onClick={() => cameraInputRef.current?.click()}
            >
              <span className="upload-icon">📷</span>
              <span>Live Photo</span>
            </button>
            <button
              type="button"
              className="upload-option"
              onClick={() => fileInputRef.current?.click()}
            >
              <span className="upload-icon">🖼️</span>
              <span>Select Image</span>
            </button>
          </div>

          {preview ? (
            <div className="preview-wrap">
              <img src={preview} alt="preview" className="preview" />
              <span className="preview-badge">Ready for analysis</span>
            </div>
          ) : (
            <div className="preview-empty">
              <span>No image selected</span>
              <small>Use Live Photo or Select Image above</small>
            </div>
          )}

          <button
            className="analyze-btn"
            onClick={handlePredict}
            disabled={!file || loading}
          >
            {loading ? "Analyzing..." : "Analyze"}
          </button>
        </section>

        {/* ---------- RIGHT: RESULTS ---------- */}
        <section className="result-panel">
          {error && (
            <div className="error-toast">
              <div className="error-icon">!</div>
              <div className="error-body">
                <strong>Image rejected</strong>
                <span>{error}</span>
              </div>
            </div>
          )}

          {!result && !binaryResult && !error && (
            <div className="card empty-state">
              <Logo size={52} />
              <p>Upload a dermoscopy image to begin clinical triage.</p>
            </div>
          )}

          {binaryResult && (
            <div className="card">
              <div className="card-head">
                <h3>Malignant / Benign Triage</h3>
                <span className="card-sub">DenseNet201 · binary</span>
              </div>
              <div className={`verdict ${binaryResult.predicted_class.toLowerCase()}`}>
                {binaryResult.predicted_class}
                <span className="verdict-conf">
                  {(binaryResult.confidence * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          )}

          {result && (
            <>
              <div className="card">
                <div className="card-head">
                  <h3>7-Class Lesion Classification</h3>
                  <span className="card-sub">DenseNet121 · HAM10000</span>
                </div>

                <div className={`verdict ${result.status}`}>
                  {result.predicted_class}
                  <span className="verdict-conf">
                    {(result.confidence * 100).toFixed(1)}%
                  </span>
                </div>

                {isUncertain && (
                  <div className="warning">
                    Low confidence — model is uncertain ({result.reason}).
                    Please review carefully or submit as a new case.
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

              {/* ---------- PRESCRIPTION PANEL (NVIDIA AI placeholder) ---------- */}
              <div className="card prescription-card">
                <div className="card-head">
                  <h3>Suggested Prescription</h3>
                  <span className="card-sub">AI-generated · requires physician review</span>
                </div>

                {prescription ? (
                  <div className="prescription-body">
                    <pre>{prescription}</pre>
                  </div>
                ) : (
                  <div className="prescription-empty">
                    <p>
                      A draft prescription will appear here after analysis using
                      the NVIDIA AI clinical endpoint.
                    </p>
                    <p className="prescription-note">
                      ⚕ For research use only — not a substitute for a licensed physician.
                    </p>
                  </div>
                )}
              </div>
            </>
          )}
        </section>
      </main>
    </div>
  );
}