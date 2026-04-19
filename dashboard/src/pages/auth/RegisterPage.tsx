import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await register(email, password, fullName);
      navigate("/dashboard");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Registration failed");
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "#1a1a2e",
      }}
    >
      <form
        onSubmit={handleSubmit}
        style={{
          background: "#fff",
          padding: 32,
          borderRadius: 8,
          width: 360,
        }}
      >
        <h1 style={{ fontSize: 28, margin: "0 0 4px", fontWeight: 700 }}>
          Rally
        </h1>
        <p style={{ color: "#666", margin: "0 0 24px", fontSize: 14 }}>
          Create your account
        </p>

        {error && (
          <div
            style={{
              background: "#fee",
              color: "#c00",
              padding: "8px 12px",
              borderRadius: 4,
              marginBottom: 16,
              fontSize: 13,
            }}
          >
            {error}
          </div>
        )}

        <div style={{ marginBottom: 16 }}>
          <label style={{ display: "block", fontSize: 13, marginBottom: 4 }}>
            Full name
          </label>
          <input
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
            style={{
              width: "100%",
              padding: "8px 10px",
              border: "1px solid #ddd",
              borderRadius: 4,
              fontSize: 14,
              boxSizing: "border-box",
            }}
          />
        </div>

        <div style={{ marginBottom: 16 }}>
          <label style={{ display: "block", fontSize: 13, marginBottom: 4 }}>
            Email
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={{
              width: "100%",
              padding: "8px 10px",
              border: "1px solid #ddd",
              borderRadius: 4,
              fontSize: 14,
              boxSizing: "border-box",
            }}
          />
        </div>

        <div style={{ marginBottom: 20 }}>
          <label style={{ display: "block", fontSize: 13, marginBottom: 4 }}>
            Password
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            style={{
              width: "100%",
              padding: "8px 10px",
              border: "1px solid #ddd",
              borderRadius: 4,
              fontSize: 14,
              boxSizing: "border-box",
            }}
          />
        </div>

        <button
          type="submit"
          style={{
            width: "100%",
            padding: "10px 0",
            background: "#4361ee",
            color: "#fff",
            border: "none",
            borderRadius: 4,
            fontSize: 14,
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          Create account
        </button>

        <p style={{ marginTop: 16, fontSize: 13, textAlign: "center" }}>
          Already have an account?{" "}
          <Link to="/login" style={{ color: "#4361ee" }}>
            Sign in
          </Link>
        </p>
      </form>
    </div>
  );
}
