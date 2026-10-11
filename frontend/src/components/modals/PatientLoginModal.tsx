"use client";

import React from "react";

interface PatientLoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  identifier: string;
  setIdentifier: (val: string) => void;
  password: string;
  setPassword: (val: string) => void;
  error: string;
  isSubmitting: boolean;
  onSubmit: (e: React.FormEvent) => void;
  onOpenSignup: () => void;
}

export const PatientLoginModal: React.FC<PatientLoginModalProps> = ({
  isOpen,
  onClose,
  identifier,
  setIdentifier,
  password,
  setPassword,
  error,
  isSubmitting,
  onSubmit,
  onOpenSignup,
}) => {
  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <h2 style={{ fontSize: "1.2rem", fontWeight: 700, color: "#0f172a" }}>
            👤 Patient Sign In
          </h2>
          <button
            onClick={onClose}
            style={{ background: "transparent", border: "none", color: "#94a3b8", fontSize: "1.2rem", cursor: "pointer" }}
          >
            ✕
          </button>
        </div>

        <p style={{ fontSize: "0.82rem", color: "#64748b", marginBottom: "18px" }}>
          Sign in using your Medical Record Number (MRN) or registered phone number.
        </p>

        {error && (
          <div style={{ background: "#fee2e2", border: "1px solid #fecdd3", color: "#b91c1c", padding: "10px 14px", borderRadius: "10px", fontSize: "0.82rem", marginBottom: "14px" }}>
            {error}
          </div>
        )}

        <form onSubmit={onSubmit} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
          <div>
            <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: "#334155", marginBottom: "4px" }}>
              MRN or Phone Number
            </label>
            <input
              type="text"
              required
              className="form-input"
              placeholder="e.g. MRN-1001 or 03001234567"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
            />
          </div>

          <div>
            <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: "#334155", marginBottom: "4px" }}>
              Password
            </label>
            <input
              type="password"
              required
              className="form-input"
              placeholder="Enter your account password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <button type="submit" className="btn-primary" disabled={isSubmitting} style={{ marginTop: "6px" }}>
            {isSubmitting ? "Signing in..." : "Sign In to Clinic"}
          </button>
        </form>

        <div style={{ textAlign: "center", marginTop: "16px", fontSize: "0.8rem", color: "#64748b" }}>
          New patient?{" "}
          <span
            style={{ color: "#0f766e", fontWeight: 700, cursor: "pointer" }}
            onClick={() => {
              onClose();
              onOpenSignup();
            }}
          >
            Create an Account
          </span>
        </div>
      </div>
    </div>
  );
};
