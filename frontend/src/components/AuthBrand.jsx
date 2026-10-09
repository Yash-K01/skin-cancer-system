import Logo from "./Logo";

export default function AuthBrand({
  tagline = "AI-assisted dermoscopy analysis built for clinicians.",
  points = [
    "7-class lesion prediction",
    "Malignant / benign triage",
    "Explainable saliency maps",
  ],
}) {
  return (
    <aside className="auth-brand">
      <div className="auth-brand-overlay" />

      <div className="auth-brand-content">
        <div className="auth-brand-top">
          <Logo size={64} />
          <h2>DermaScan</h2>
        </div>

        <div className="auth-brand-middle">
          <p className="brand-tagline">{tagline}</p>
          <ul className="brand-points">
            {points.map((p) => (
              <li key={p}>{p}</li>
            ))}
          </ul>
        </div>

        <div className="auth-brand-bottom">
          <p className="brand-quote">
            “Early detection saves lives — every second counts.”
          </p>
          <p className="brand-credit">Powered by DenseNet · Explainable AI</p>
        </div>
      </div>
    </aside>
  );
}