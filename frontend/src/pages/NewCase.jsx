import { useState } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { submitNewCase } from "../api/endpoints";

export default function NewCase() {
  const navigate = useNavigate();
  const location = useLocation();
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(location.state?.preview || null);
  const [form, setForm] = useState({
    lab_confirmed_label: "",
    patient_age: "",
    patient_sex: "",
    lesion_site: "",
    clinical_notes: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleFile = (f) => {
    setFile(f);
    setPreview(URL.createObjectURL(f));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const fd = new FormData();
      if (file) fd.append("file", file);
      fd.append("lab_confirmed_label", form.lab_confirmed_label);
      if (form.patient_age) fd.append("patient_age", form.patient_age);
      if (form.patient_sex) fd.append("patient_sex", form.patient_sex);
      if (form.lesion_site) fd.append("lesion_site", form.lesion_site);
      if (form.clinical_notes) fd.append("clinical_notes", form.clinical_notes);

      await submitNewCase(fd);
      alert("New case submitted. Pending admin approval.");
      navigate("/predict");
    } catch (err) {
      setError(err.response?.data?.detail || "Submission failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card wide">
        <h1>New Case Submission</h1>
        <p className="subtitle">
          For lesions the model could not classify. Requires lab confirmation.
        </p>

        {error && <div className="error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <label>
            Image (if not already attached)
            <input
              type="file"
              accept="image/*"
              onChange={(e) => handleFile(e.target.files[0])}
            />
          </label>
          {preview && <img src={preview} alt="preview" className="preview" />}

          <label>
            Lab-Confirmed Label *
            <input
              type="text"
              value={form.lab_confirmed_label}
              onChange={(e) => setForm({ ...form, lab_confirmed_label: e.target.value })}
              required
            />
          </label>
          <label>
            Patient Age
            <input
              type="number"
              value={form.patient_age}
              onChange={(e) => setForm({ ...form, patient_age: e.target.value })}
            />
          </label>
          <label>
            Patient Sex
            <select
              value={form.patient_sex}
              onChange={(e) => setForm({ ...form, patient_sex: e.target.value })}
            >
              <option value="">—</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
            </select>
          </label>
          <label>
            Lesion Site
            <input
              type="text"
              value={form.lesion_site}
              onChange={(e) => setForm({ ...form, lesion_site: e.target.value })}
            />
          </label>
          <label>
            Clinical Notes
            <textarea
              value={form.clinical_notes}
              onChange={(e) => setForm({ ...form, clinical_notes: e.target.value })}
              rows={4}
            />
          </label>
          <button type="submit" disabled={loading}>
            {loading ? "Submitting..." : "Submit Case"}
          </button>
        </form>

        <p className="footer">
          <Link to="/predict">Back to Predict</Link>
        </p>
      </div>
    </div>
  );
}