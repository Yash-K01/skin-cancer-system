import { useState, useRef, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { Link } from "react-router-dom";
import { predict7Class, predictBinary, submitFeedback } from "../api/endpoints";
import ProbabilityChart from "../components/ProbabilityChart";
import Logo from "../components/Logo";

/* ---- Error formatter: turn backend error codes into descriptive text ---- */
function describeError(raw) {
  if (!raw) return { title: "Something went wrong", detail: "Please try again." };

  const msg = String(raw);

  if (msg.includes("quality")) {
    if (msg.includes("blurry")) {
      const m = msg.match(/sharpness=([\d.]+)/);
      return {
        title: "Image is too blurry",
        detail: `Sharpness value ${m ? m[1] : "N/A"} is below the minimum required. Please capture a sharper dermoscopy image.`,
      };
    }
    if (msg.includes("dark"))
      return {
        title: "Image is too dark",
        detail: "The lighting is insufficient. Please upload a well-lit dermoscopy image.",
      };
    if (msg.includes("bright"))
      return {
        title: "Image is too bright",
        detail: "The image is overexposed. Please reduce glare or lighting.",
      };
    if (msg.includes("small"))
      return {
        title: "Image resolution is too low",
        detail: "The image dimensions are below the minimum. Use a higher-resolution image.",
      };
    if (msg.includes("Cannot read"))
      return {
        title: "Cannot read the image",
        detail: "The file appears corrupted or unsupported. Please try a JPG or PNG.",
      };
  }

  if (msg.includes("not_skin")) {
    return {
      title: "Not a skin image",
      detail:
        "The image does not contain enough skin-coloured regions. Please upload a close-up dermoscopy image of a single lesion.",
    };
  }

  if (msg.includes("out_of_distribution")) {
    const m = msg.match(/score=([\d.]+)/);
    return {
      title: "Image is not a dermoscopy image",
      detail: `This image doesn't resemble the training data (score ${m ? m[1] : "N/A"}). Upload a magnified dermoscopy image captured with a specialist device.`,
    };
  }

  return { title: "Image rejected", detail: msg };
}

export default function Predict() {
  const { user, logout } = useAuth();
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [binaryResult, setBinaryResult] = useState(null);
  const [error, setError] = useState(null);
  const [prescription, setPrescription] = useState("");

  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);

  // Auto-dismiss the error after 8 seconds
  useEffect(() => {
    if (!error) return;
    const t = setTimeout(() => setError(null), 8000);
    return () => clearTimeout(t);
  }, [error]);

  const handleFile = (f) => {
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
    setBinaryResult(null);
    setError(null);
    setPrescription("");
  };

  const handlePredict = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const [r7, rBin] = await Promise.all([
        predict7Class(file),
        predictBinary(file),
      ]);
      setResult(r7.data);
      setBinaryResult(rBin.data);
    } catch (err) {
      const raw = err.response?.data?.detail || "Prediction failed";
      setError(describeError(raw));
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
    <div className="page page-clinical">
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
        {/* LEFT: UPLOAD */}
        <section className="upload-panel card-3d">
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

        {/* RIGHT: RESULTS */}
        <section className="result-panel">
          {error && (
            <div className="error-toast" role="alert">
              <div className="error-icon">!</div>
              <div className="error-body">
                <strong>{error.title}</strong>
                <span>{error.detail}</span>
              </div>
              <button
                className="error-close"
                onClick={() => setError(null)}
                aria-label="Dismiss"
              >
                ×
              </button>
            </div>
          )}

          {!result && !binaryResult && !error && (
            <div className="card card-3d empty-state">
              <Logo size={52} />
              <p>Upload a dermoscopy image to begin clinical triage.</p>
            </div>
          )}

          {binaryResult && (
            <div className="card card-3d">
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
              <div className="card card-3d">
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

              <div className="card card-3d prescription-card">
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