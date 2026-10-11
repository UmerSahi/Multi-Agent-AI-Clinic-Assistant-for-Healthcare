"use client";

import React from "react";

interface DoctorLoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  email: string;
  setEmail: (val: string) => void;
  password: string;
  setPassword: (val: string) => void;
  error: string;
  onSubmit: (e: React.FormEvent) => void;
  onQuickLogin?: (email: string, password: string) => void;
}

export const DoctorLoginModal: React.FC<DoctorLoginModalProps> = ({
  isOpen,
  onClose,
  email,
  setEmail,
  password,
  setPassword,
  error,
  onSubmit,
  onQuickLogin,
}) => {
  if (!isOpen) return null;

  const demoDoctors = [
    { name: "Dr. Bilal Saeed", specialty: "General Medicine", email: "dr.bilal.saeed@citycare.com", icon: "🩺" },
    { name: "Dr. Ayesha Tariq", specialty: "Gynaecology", email: "dr.ayesha.tariq@citycare.com", icon: "🌸" },
    { name: "Dr. Omer Latif", specialty: "Cardiology", email: "dr.omer.latif@citycare.com", icon: "🫀" },
    { name: "Dr. Usman Sheikh", specialty: "Paediatrics", email: "dr.usman.sheikh@citycare.com", icon: "🧒" },
    { name: "Dr. Maryam Naveed", specialty: "Medical Director", email: "dr.maryam@citycare.com", icon: "🏥" },
  ];

  const handleSelectDemo = (docEmail: string) => {
    setEmail(docEmail);
    setPassword("Doctor123!");
    if (onQuickLogin) {
      onQuickLogin(docEmail, "Doctor123!");
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" style={{ maxWidth: "520px" }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ fontSize: "1.4rem" }}>🩺</span>
            <h2 style={{ fontSize: "1.2rem", fontWeight: 800, color: "#0f172a" }}>
              Doctor Portal Sign In
            </h2>
          </div>
          <button
            onClick={onClose}
            style={{ background: "transparent", border: "none", color: "#94a3b8", fontSize: "1.2rem", cursor: "pointer" }}
          >
            ✕
          </button>
        </div>

        <p style={{ fontSize: "0.82rem", color: "#64748b", marginBottom: "16px" }}>
          Log in with your official City Care Clinics medical staff credentials to access patient dossiers, review queues, and prescription writing.
        </p>

        {error && (
          <div style={{ background: "#fee2e2", border: "1px solid #fecdd3", color: "#b91c1c", padding: "10px 14px", borderRadius: "10px", fontSize: "0.82rem", marginBottom: "14px" }}>
            {error}
          </div>
        )}

        {/* 1-CLICK DEMO DOCTOR SWITCHER */}
        <div
          style={{
            background: "#f0fdfa",
            border: "1px solid #ccfbf1",
            borderRadius: "14px",
            padding: "12px 14px",
            marginBottom: "16px",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
            <span style={{ fontSize: "0.76rem", fontWeight: 800, color: "#0f766e", textTransform: "uppercase", letterSpacing: "0.04em" }}>
              ⚡ 1-Click Demo Doctor Sign In
            </span>
            <span style={{ fontSize: "0.7rem", color: "#64748b" }}>Click any to sign in</span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            {demoDoctors.map((doc) => (
              <button
                key={doc.email}
                type="button"
                onClick={() => handleSelectDemo(doc.email)}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "7px 10px",
                  borderRadius: "10px",
                  border: "1px solid #99f6e4",
                  background: email === doc.email ? "#ccfbf1" : "#ffffff",
                  cursor: "pointer",
                  textAlign: "left",
                  transition: "all 0.15s ease",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span style={{ fontSize: "1rem" }}>{doc.icon}</span>
                  <div>
                    <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "#0f172a" }}>{doc.name}</div>
                    <div style={{ fontSize: "0.7rem", color: "#64748b" }}>{doc.specialty} • {doc.email}</div>
                  </div>
                </div>
                <span
                  style={{
                    fontSize: "0.72rem",
                    fontWeight: 700,
                    color: "#0f766e",
                    background: "#f0fdfa",
                    padding: "3px 8px",
                    borderRadius: "6px",
                    border: "1px solid #99f6e4",
                  }}
                >
                  Sign In →
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Manual Credentials Form */}
        <form onSubmit={onSubmit} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          <div>
            <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: "#334155", marginBottom: "4px" }}>
              Doctor Email
            </label>
            <input
              type="email"
              required
              className="form-input"
              placeholder="e.g. dr.bilal.saeed@citycare.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
              <label style={{ fontSize: "0.8rem", fontWeight: 600, color: "#334155" }}>
                Password
              </label>
              <span style={{ fontSize: "0.7rem", color: "#64748b" }}>
                Default: <code>Doctor123!</code> or <code>demo123</code>
              </span>
            </div>
            <input
              type="password"
              required
              className="form-input"
              placeholder="Enter password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <button type="submit" className="btn-primary" style={{ marginTop: "6px", padding: "10px" }}>
            Sign In with Email & Password
          </button>
        </form>
      </div>
    </div>
  );
};
