"use client";

import React from "react";
import { DoctorDirectoryItem, Patient } from "@/types";

interface BookingSlotModalProps {
  isOpen: boolean;
  onClose: () => void;
  slot: any;
  doctor: DoctorDirectoryItem | null;
  date: string;
  patientUser: Patient | null;
  reason: string;
  setReason: (val: string) => void;
  isSubmitting: boolean;
  successResult: any | null;
  onConfirm: () => void;
  onDismissSuccess: () => void;
}

export const BookingSlotModal: React.FC<BookingSlotModalProps> = ({
  isOpen,
  onClose,
  slot,
  doctor,
  date,
  patientUser,
  reason,
  setReason,
  isSubmitting,
  successResult,
  onConfirm,
  onDismissSuccess,
}) => {
  if (!isOpen) return null;

  const timeStr = typeof slot === "string" ? slot : slot?.display_time || slot?.time || slot?.slot_id;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        {successResult ? (
          <div style={{ textAlign: "center", padding: "10px 0" }}>
            <div style={{ fontSize: "3rem", marginBottom: "12px" }}>🎉</div>
            <h2 style={{ fontSize: "1.3rem", fontWeight: 700, color: "#059669" }}>
              Appointment Confirmed!
            </h2>
            <p style={{ fontSize: "0.85rem", color: "#64748b", marginTop: "4px" }}>
              Your outpatient consultation has been scheduled in the clinic system.
            </p>

            <div style={{ background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: "14px", padding: "16px", margin: "20px 0" }}>
              <div style={{ fontSize: "0.78rem", color: "#047857", fontWeight: 600 }}>Booking Reference Code:</div>
              <div style={{ fontSize: "1.3rem", fontWeight: 800, color: "#065f46", fontFamily: "var(--font-mono)", marginTop: "4px" }}>
                {successResult.booking_reference || successResult.booking_ref || "APP-SUCCESS"}
              </div>
              <div style={{ fontSize: "0.75rem", color: "#64748b", marginTop: "8px" }}>
                Doctor: <strong>{doctor?.full_name}</strong> • Time: <strong>{timeStr}</strong> ({date})
              </div>
            </div>

            <button className="btn-primary" onClick={onDismissSuccess} style={{ width: "100%" }}>
              Done / Return to Appointments
            </button>
          </div>
        ) : (
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <h2 style={{ fontSize: "1.2rem", fontWeight: 700, color: "#0f172a" }}>
                📅 Confirm Appointment Booking
              </h2>
              <button
                onClick={onClose}
                style={{ background: "transparent", border: "none", color: "#94a3b8", fontSize: "1.2rem", cursor: "pointer" }}
              >
                ✕
              </button>
            </div>

            {/* Doctor & Slot Summary */}
            <div style={{ background: "#f0fdf9", border: "1px solid #ccfbf1", borderRadius: "14px", padding: "14px", marginBottom: "16px" }}>
              <div style={{ fontWeight: 700, color: "#0f172a", fontSize: "0.95rem" }}>
                {doctor?.full_name}
              </div>
              <div style={{ fontSize: "0.8rem", color: "#0f766e", fontWeight: 600 }}>
                {doctor?.specialty} • Consultation Fee: PKR {doctor?.consultation_fee?.toLocaleString()}
              </div>
              <div style={{ fontSize: "0.78rem", color: "#475569", marginTop: "6px" }}>
                📅 Date: <strong>{date}</strong> &nbsp;•&nbsp; ⏰ Time Slot: <strong>{timeStr}</strong>
              </div>
            </div>

            {/* Patient details */}
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <div>
                <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: "#334155", marginBottom: "4px" }}>
                  Patient Name
                </label>
                <input
                  type="text"
                  disabled
                  className="form-input"
                  value={patientUser ? patientUser.patient_name : "Umer Sahi"}
                  style={{ background: "#f8fafc" }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: "#334155", marginBottom: "4px" }}>
                  Reason for Visit / Symptoms
                </label>
                <textarea
                  className="form-input"
                  rows={3}
                  placeholder="Describe your symptoms or consultation reason..."
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                />
              </div>

              <div style={{ display: "flex", gap: "10px", marginTop: "10px" }}>
                <button className="btn-secondary" onClick={onClose} style={{ flex: 1 }}>
                  Cancel
                </button>
                <button
                  className="btn-primary"
                  onClick={onConfirm}
                  disabled={isSubmitting}
                  style={{ flex: 2 }}
                >
                  {isSubmitting ? "Booking Slot..." : "Confirm & Book Slot"}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
