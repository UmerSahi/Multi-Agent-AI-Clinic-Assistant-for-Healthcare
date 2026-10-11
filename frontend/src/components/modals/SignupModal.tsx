"use client";

import React from "react";

interface SignupModalProps {
  isOpen: boolean;
  onClose: () => void;
  form: {
    full_name: string;
    phone: string;
    age: string;
    gender: string;
    email: string;
    password: string;
    address: string;
    blood_group: string;
  };
  setForm: React.Dispatch<React.SetStateAction<any>>;
  isSubmitting: boolean;
  onSubmit: (e: React.FormEvent) => void;
}

export const SignupModal: React.FC<SignupModalProps> = ({
  isOpen,
  onClose,
  form,
  setForm,
  isSubmitting,
  onSubmit,
}) => {
  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <h2 style={{ fontSize: "1.2rem", fontWeight: 700, color: "#0f172a" }}>
            👤 New Patient Registration
          </h2>
          <button
            onClick={onClose}
            style={{ background: "transparent", border: "none", color: "#94a3b8", fontSize: "1.2rem", cursor: "pointer" }}
          >
            ✕
          </button>
        </div>

        <p style={{ fontSize: "0.82rem", color: "#64748b", marginBottom: "18px" }}>
          Register a new patient to generate their Medical Record Number (MRN) and start a clinical session.
        </p>

        <form onSubmit={onSubmit} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          <div>
            <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: "#334155", marginBottom: "4px" }}>
              Full Name *
            </label>
            <input
              type="text"
              required
              className="form-input"
              placeholder="e.g. Umer Sahi"
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
            />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: "10px" }}>
            <div>
              <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: "#334155", marginBottom: "4px" }}>
                Phone Number *
              </label>
              <input
                type="text"
                required
                className="form-input"
                placeholder="03001234567"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
              />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: "#334155", marginBottom: "4px" }}>
                Age *
              </label>
              <input
                type="number"
                required
                className="form-input"
                placeholder="28"
                value={form.age}
                onChange={(e) => setForm({ ...form, age: e.target.value })}
              />
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
            <div>
              <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: "#334155", marginBottom: "4px" }}>
                Gender
              </label>
              <select
                className="form-input"
                value={form.gender}
                onChange={(e) => setForm({ ...form, gender: e.target.value })}
              >
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: "#334155", marginBottom: "4px" }}>
                Blood Group
              </label>
              <input
                type="text"
                className="form-input"
                placeholder="B+ or O+"
                value={form.blood_group}
                onChange={(e) => setForm({ ...form, blood_group: e.target.value })}
              />
            </div>
          </div>

          <div>
            <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: "#334155", marginBottom: "4px" }}>
              Account Password *
            </label>
            <input
              type="password"
              required
              className="form-input"
              placeholder="Create a secure password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
            />
          </div>

          <button type="submit" className="btn-primary" disabled={isSubmitting} style={{ marginTop: "8px" }}>
            {isSubmitting ? "Generating MRN & Registering..." : "Complete Registration"}
          </button>
        </form>
      </div>
    </div>
  );
};
