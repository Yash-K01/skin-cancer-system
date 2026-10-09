import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { registerUser } from "../api/endpoints";
import Logo from "../components/Logo";
import AuthBrand from "../components/AuthBrand";

export default function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await registerUser({
        email,
        password,
        full_name: fullName,
        role: "doctor",
      });
      navigate("/login");
    } catch (err) {
      setError(err.response?.data?.detail || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-split">
      <AuthBrand
        tagline="Join the clinical network improving early skin cancer outcomes"
        points={[
          "Free for verified dermatologists",
          "Secure HIPAA-aligned storage",
          "Human-in-the-loop case review",
          "Publishable research dashboard",
        ]}
      />

      <div className="auth-container">
        <div className="auth-card">
          <div className="auth-logo-mobile">
            <Logo size={48} />
          </div>
          <h1>Create Account</h1>
          <p className="subtitle">Doctor Registration</p>

          {error && <div className="error">{error}</div>}

          <form onSubmit={handleSubmit}>
            <label>
              Full Name
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Dr. Jane Doe"
                required
              />
            </label>
            <label>
              Email
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="doctor@hospital.com"
                required
              />
            </label>
            <label>
              Password
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Minimum 6 characters"
                required
                minLength={6}
              />
            </label>
            <button type="submit" disabled={loading}>
              {loading ? "Creating..." : "Register"}
            </button>
          </form>

          <p className="footer">
            Already have an account? <Link to="/login">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}