import Logo from "./Logo";

export default function AuthBrand() {
  return (
    <aside className="auth-brand">
      <Logo size={64} />
      <h2>DermaScan</h2>
      <p className="brand-tagline">
        AI-assisted dermoscopy analysis built for clinicians.
      </p>
      <ul className="brand-points">
        <li>7-class lesion prediction</li>
        <li>Malignant / benign triage</li>
        <li>Explainable saliency maps</li>
      </ul>
    </aside>
  );
}
