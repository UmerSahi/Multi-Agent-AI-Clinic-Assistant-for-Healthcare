"use client";

import React from "react";

interface ViewRxModalProps {
  isOpen: boolean;
  onClose: () => void;
  appointment: any;
}

export const ViewRxModal: React.FC<ViewRxModalProps> = ({
  isOpen,
  onClose,
  appointment,
}) => {
  if (!isOpen || !appointment) return null;

  const rx = appointment.prescription || {};
  const medicines = rx.medicines || rx.medications || [];

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" style={{ maxWidth: "680px", padding: "32px" }} onClick={(e) => e.stopPropagation()}>
        {/* Clinic Header / Letterhead */}
        <div style={{ borderBottom: "2px solid #0f766e", paddingBottom: "16px", marginBottom: "20px", display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ fontSize: "1.4rem" }}>🏥</span>
              <h2 style={{ fontSize: "1.25rem", fontWeight: 800, color: "#0f766e", letterSpacing: "0.05em" }}>
                CITY CARE CLINICS
              </h2>
            </div>
            <div style={{ fontSize: "0.76rem", color: "#64748b", marginTop: "2px" }}>
              Multi-Specialty Outpatient Healthcare Center
            </div>
          </div>

          <div style={{ textAlign: "right", fontSize: "0.78rem", color: "#334155" }}>
            <div style={{ fontWeight: 700, color: "#0f172a" }}>Dr. {appointment.doctor_name || rx.doctor_name || "Consultant"}</div>
            <div>{appointment.specialty || rx.specialty || "Physician"}</div>
            <div style={{ fontSize: "0.72rem", color: "#64748b" }}>Date: {rx.issued_at || appointment.date}</div>
          </div>
        </div>

        {/* Patient Info Row */}
        <div style={{ background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "12px", padding: "12px 16px", marginBottom: "20px", display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: "10px", fontSize: "0.82rem" }}>
          <div>
            Patient: <strong>{appointment.patient_name || rx.patient_name}</strong>
          </div>
          <div>
            MRN: <strong>{appointment.mrn || rx.patient_id || "P001"}</strong>
          </div>
          <div>
            Phone: <strong>{appointment.phone || rx.phone}</strong>
          </div>
        </div>

        {/* Diagnosis */}
        <div style={{ marginBottom: "18px" }}>
          <div style={{ fontSize: "0.78rem", fontWeight: 700, color: "#0f766e", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Diagnosis / Assessment
          </div>
          <div style={{ fontSize: "0.95rem", fontWeight: 600, color: "#0f172a", marginTop: "3px" }}>
            {rx.diagnosis || "Clinical Outpatient Consultation"}
          </div>
        </div>

        {/* Medications Table */}
        <div style={{ marginBottom: "20px" }}>
          <div style={{ fontSize: "1.2rem", fontWeight: 800, color: "#0f766e", marginBottom: "8px", fontFamily: "serif" }}>
            ℞
          </div>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.84rem" }}>
            <thead>
              <tr style={{ background: "#f1f5f9", borderBottom: "1px solid #cbd5e1", textAlign: "left", color: "#334155" }}>
                <th style={{ padding: "8px 10px" }}>Medicine</th>
                <th style={{ padding: "8px 10px" }}>Dosage</th>
                <th style={{ padding: "8px 10px" }}>Frequency</th>
                <th style={{ padding: "8px 10px" }}>Duration</th>
                <th style={{ padding: "8px 10px" }}>Instructions</th>
              </tr>
            </thead>
            <tbody>
              {medicines.map((m: any, idx: number) => (
                <tr key={idx} style={{ borderBottom: "1px solid #f1f5f9" }}>
                  <td style={{ padding: "8px 10px", fontWeight: 700, color: "#0f172a" }}>{m.medicine_name}</td>
                  <td style={{ padding: "8px 10px", color: "#475569" }}>{m.dosage}</td>
                  <td style={{ padding: "8px 10px", color: "#475569" }}>{m.frequency}</td>
                  <td style={{ padding: "8px 10px", color: "#475569" }}>{m.duration}</td>
                  <td style={{ padding: "8px 10px", color: "#64748b" }}>{m.instructions || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Doctor Advice */}
        {rx.advice && (
          <div style={{ background: "#f0fdf9", border: "1px solid #ccfbf1", borderRadius: "10px", padding: "12px", marginBottom: "20px", fontSize: "0.8rem", color: "#065f46" }}>
            <strong>Special Clinical Instructions:</strong> {rx.advice}
          </div>
        )}

        {/* Signature & Print */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", borderTop: "1px solid #e2e8f0", paddingTop: "18px" }}>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontFamily: "cursive", fontSize: "1.1rem", color: "#0f766e" }}>Dr. Verified</div>
            <div style={{ fontSize: "0.72rem", color: "#94a3b8", borderTop: "1px dashed #cbd5e1", paddingTop: "4px" }}>
              Authorized Electronic Signature
            </div>
          </div>

          <div style={{ display: "flex", gap: "10px", alignItems: "center", flexWrap: "wrap" }}>
            <button
              className="btn-secondary"
              onClick={() => window.print()}
              style={{ fontSize: "0.82rem" }}
            >
              🖨️ Print Rx
            </button>
            <a
              href={`http://127.0.0.1:8000/api/prescriptions/${(appointment.booking_reference || appointment.booking_ref || rx.booking_reference || "").replace("#", "").trim()}/pdf`}
              target="_blank"
              rel="noreferrer"
              className="btn-primary"
              style={{
                fontSize: "0.82rem",
                textDecoration: "none",
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                background: "#0f766e",
                color: "#ffffff",
                padding: "8px 14px",
                borderRadius: "10px"
              }}
            >
              <span>📥</span>
              <span>Download Official PDF</span>
            </a>
            <button
              className="btn-secondary"
              onClick={onClose}
              style={{ fontSize: "0.82rem" }}
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
