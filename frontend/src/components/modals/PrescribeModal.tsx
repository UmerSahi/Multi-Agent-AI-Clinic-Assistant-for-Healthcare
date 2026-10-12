"use client";

import React, { useState } from "react";
import { DoctorAccount } from "@/types";

interface PrescribeModalProps {
  isOpen: boolean;
  onClose: () => void;
  appointment: any;
  doctorUser: DoctorAccount | null;
  prescriptionForm: {
    diagnosis: string;
    advice: string;
    medicines: Array<{
      medicine_name: string;
      dosage: string;
      frequency: string;
      duration: string;
      instructions: string;
    }>;
  };
  setPrescriptionForm: React.Dispatch<React.SetStateAction<any>>;
  onAddMedicineRow: () => void;
  onRemoveMedicineRow: (idx: number) => void;
  onMedicineChange: (idx: number, field: string, val: string) => void;
  isSubmitting: boolean;
  errorMessage?: string;
  successMessage?: boolean;
  onSubmit: (e: React.FormEvent) => void;
}

export const PrescribeModal: React.FC<PrescribeModalProps> = ({
  isOpen,
  onClose,
  appointment,
  doctorUser,
  prescriptionForm,
  setPrescriptionForm,
  onAddMedicineRow,
  onRemoveMedicineRow,
  onMedicineChange,
  isSubmitting,
  errorMessage,
  successMessage,
  onSubmit,
}) => {
  const [clientError, setClientError] = useState<string>("");

  if (!isOpen || !appointment) return null;

  // Check whether the logged-in doctor is assigned to this appointment
  const checkIsDoctorAssigned = (): boolean => {
    if (!doctorUser) return false;
    const docId = (doctorUser.doctor_id || doctorUser.id || "").toLowerCase().trim();
    const appDocId = (appointment.doctor_id || appointment.practitioner_id || "").toLowerCase().trim();
    if (docId && appDocId && docId === appDocId) return true;

    const cleanDocName = (doctorUser.doctor_name || (doctorUser as any).name || "")
      .toLowerCase()
      .replace(/^dr\.\s*|^doctor\s*/i, "")
      .replace(/[^a-z0-9]/g, "")
      .trim();
    const cleanAppDocName = (appointment.doctor_name || "")
      .toLowerCase()
      .replace(/^dr\.\s*|^doctor\s*/i, "")
      .replace(/[^a-z0-9]/g, "")
      .trim();

    if (cleanDocName && cleanAppDocName) {
      return (
        cleanDocName === cleanAppDocName ||
        cleanDocName.includes(cleanAppDocName) ||
        cleanAppDocName.includes(cleanDocName)
      );
    }
    return false;
  };

  const isAssigned = checkIsDoctorAssigned();
  const displayedError = clientError || errorMessage;

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setClientError("");

    if (!isAssigned) {
      setClientError(
        `Clinical Restriction: Only ${appointment.doctor_name || "the booked attending physician"} can issue prescriptions for this appointment.`
      );
      return;
    }

    if (!prescriptionForm.diagnosis || !prescriptionForm.diagnosis.trim()) {
      setClientError("Please enter a clinical diagnosis / assessment before issuing the prescription.");
      return;
    }

    if (!prescriptionForm.medicines || prescriptionForm.medicines.length === 0) {
      setClientError("Please include at least one medication in the prescription.");
      return;
    }

    const hasEmptyMed = prescriptionForm.medicines.some((m) => !m.medicine_name || !m.medicine_name.trim());
    if (hasEmptyMed) {
      setClientError("Please fill in medication names for all rows, or delete empty rows.");
      return;
    }

    onSubmit(e);
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" style={{ maxWidth: "740px", maxHeight: "90vh", overflowY: "auto" }} onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <div>
            <h2 style={{ fontSize: "1.25rem", fontWeight: 800, color: "#0f172a", display: "flex", alignItems: "center", gap: "8px" }}>
              <span>💊</span>
              <span>Issue Electronic Prescription (Rx)</span>
            </h2>
            <div style={{ fontSize: "0.8rem", color: "#64748b", marginTop: "2px" }}>
              Booking: <strong style={{ color: "#0f766e" }}>{appointment.booking_reference || appointment.booking_ref || appointment.id}</strong> • Patient: <strong>{appointment.patient_name}</strong> (MRN: {appointment.mrn || appointment.patient_mrn || "P001"})
            </div>
          </div>
          <button
            onClick={onClose}
            style={{ background: "transparent", border: "none", color: "#94a3b8", fontSize: "1.3rem", cursor: "pointer", padding: "4px" }}
            aria-label="Close modal"
          >
            ✕
          </button>
        </div>

        {/* Doctor Authorization Banner */}
        <div style={{ marginBottom: "16px" }}>
          {isAssigned ? (
            <div
              style={{
                background: "#ecfdf5",
                border: "1.5px solid #a7f3d0",
                borderRadius: "12px",
                padding: "10px 14px",
                display: "flex",
                alignItems: "center",
                gap: "10px",
                fontSize: "0.8rem",
                color: "#065f46",
              }}
            >
              <span style={{ fontSize: "1.2rem" }}>✅</span>
              <div>
                <strong>Authorized Attending Physician:</strong> {doctorUser?.doctor_name} ({doctorUser?.specialty || "Specialist"})
                <div style={{ fontSize: "0.72rem", color: "#047857" }}>
                  PMDC Verified: {doctorUser?.pmdc_number || "Active Practitioner"} • Authorized to sign electronic prescription.
                </div>
              </div>
            </div>
          ) : (
            <div
              style={{
                background: "#fff1f2",
                border: "1.5px solid #fecdd3",
                borderRadius: "12px",
                padding: "12px 14px",
                display: "flex",
                alignItems: "flex-start",
                gap: "10px",
                fontSize: "0.8rem",
                color: "#9f1239",
              }}
            >
              <span style={{ fontSize: "1.3rem" }}>🔒</span>
              <div>
                <strong>Prescription Restriction (Clinical Safety):</strong>
                <div>
                  Only <strong>{appointment.doctor_name || "the booked attending doctor"}</strong> can prescribe for this patient.
                  {doctorUser ? (
                    <span> You are logged in as <strong>{doctorUser.doctor_name}</strong>.</span>
                  ) : (
                    <span> You must sign in to the Doctor Workstation to issue prescriptions.</span>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Dynamic Alerts */}
        {displayedError && (
          <div
            style={{
              background: "#fef2f2",
              border: "1.5px solid #f87171",
              borderRadius: "10px",
              padding: "10px 14px",
              color: "#991b1b",
              fontSize: "0.82rem",
              fontWeight: 600,
              marginBottom: "14px",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <span>⚠️</span>
            <span>{displayedError}</span>
          </div>
        )}

        {successMessage && (
          <div
            style={{
              background: "#d1fae5",
              border: "1.5px solid #34d399",
              borderRadius: "10px",
              padding: "10px 14px",
              color: "#065f46",
              fontSize: "0.84rem",
              fontWeight: 700,
              marginBottom: "14px",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <span>🎉</span>
            <span>Electronic Prescription (Rx) successfully signed & issued! Updating clinic records...</span>
          </div>
        )}

        <form onSubmit={handleFormSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {/* Diagnosis */}
          <div>
            <label style={{ display: "block", fontSize: "0.82rem", fontWeight: 700, color: "#334155", marginBottom: "4px" }}>
              Clinical Diagnosis / Assessment <span style={{ color: "#e11d48" }}>*</span>
            </label>
            <input
              type="text"
              className="form-input"
              placeholder="e.g. Acute Upper Respiratory Tract Infection (URTI) with mild fever"
              value={prescriptionForm.diagnosis}
              onChange={(e) => {
                setClientError("");
                setPrescriptionForm({ ...prescriptionForm, diagnosis: e.target.value });
              }}
            />
            <div style={{ fontSize: "0.72rem", color: "#64748b", marginTop: "4px" }}>
              Appointment Complaint: {appointment.reason || appointment.reason_for_visit || "General Consultation"}
            </div>
          </div>

          {/* Medicines Dynamic Table */}
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
              <label style={{ fontSize: "0.82rem", fontWeight: 700, color: "#0f766e" }}>
                Prescribed Medications ({prescriptionForm.medicines.length})
              </label>
              <button
                type="button"
                onClick={onAddMedicineRow}
                style={{
                  background: "#ecfdf5",
                  border: "1px solid #a7f3d0",
                  color: "#047857",
                  borderRadius: "8px",
                  padding: "5px 12px",
                  fontSize: "0.75rem",
                  fontWeight: 700,
                  cursor: "pointer",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "4px",
                }}
              >
                <span>+</span>
                <span>Add Medication</span>
              </button>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {prescriptionForm.medicines.map((med, idx) => (
                <div
                  key={idx}
                  style={{
                    background: "#f8fafc",
                    border: "1px solid #e2e8f0",
                    borderRadius: "10px",
                    padding: "10px",
                    display: "grid",
                    gridTemplateColumns: "1.6fr 1fr 1fr 1fr auto",
                    gap: "8px",
                    alignItems: "center",
                  }}
                >
                  <div>
                    <span style={{ fontSize: "0.68rem", color: "#64748b", display: "block", marginBottom: "2px" }}>Drug Name</span>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="e.g. Tab Panadol 500mg"
                      style={{ fontSize: "0.8rem", padding: "6px 8px" }}
                      value={med.medicine_name}
                      onChange={(e) => {
                        setClientError("");
                        onMedicineChange(idx, "medicine_name", e.target.value);
                      }}
                    />
                  </div>
                  <div>
                    <span style={{ fontSize: "0.68rem", color: "#64748b", display: "block", marginBottom: "2px" }}>Dosage</span>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="500mg"
                      style={{ fontSize: "0.8rem", padding: "6px 8px" }}
                      value={med.dosage}
                      onChange={(e) => onMedicineChange(idx, "dosage", e.target.value)}
                    />
                  </div>
                  <div>
                    <span style={{ fontSize: "0.68rem", color: "#64748b", display: "block", marginBottom: "2px" }}>Frequency</span>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="1-0-1"
                      style={{ fontSize: "0.8rem", padding: "6px 8px" }}
                      value={med.frequency}
                      onChange={(e) => onMedicineChange(idx, "frequency", e.target.value)}
                    />
                  </div>
                  <div>
                    <span style={{ fontSize: "0.68rem", color: "#64748b", display: "block", marginBottom: "2px" }}>Duration</span>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="5 days"
                      style={{ fontSize: "0.8rem", padding: "6px 8px" }}
                      value={med.duration}
                      onChange={(e) => onMedicineChange(idx, "duration", e.target.value)}
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() => onRemoveMedicineRow(idx)}
                    title="Remove medicine"
                    style={{
                      background: "none",
                      border: "none",
                      color: "#e11d48",
                      cursor: "pointer",
                      fontSize: "1.1rem",
                      padding: "4px",
                      marginTop: "14px",
                    }}
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Advice / Notes */}
          <div>
            <label style={{ display: "block", fontSize: "0.82rem", fontWeight: 700, color: "#334155", marginBottom: "4px" }}>
              Doctor Advice & Dietary Instructions
            </label>
            <textarea
              className="form-input"
              rows={3}
              value={prescriptionForm.advice}
              onChange={(e) => setPrescriptionForm({ ...prescriptionForm, advice: e.target.value })}
            />
          </div>

          {/* Actions */}
          <div style={{ display: "flex", gap: "10px", marginTop: "8px" }}>
            <button type="button" className="btn-secondary" onClick={onClose} style={{ flex: 1, padding: "10px 16px" }}>
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={isSubmitting || !isAssigned || successMessage}
              style={{
                flex: 2,
                padding: "10px 16px",
                fontSize: "0.86rem",
                fontWeight: 700,
                opacity: !isAssigned ? 0.6 : 1,
                cursor: !isAssigned ? "not-allowed" : "pointer",
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "8px",
              }}
            >
              {isSubmitting ? (
                <>
                  <span>⏳</span>
                  <span>Signing & Issuing Rx...</span>
                </>
              ) : !isAssigned ? (
                <>
                  <span>🔒</span>
                  <span>Restricted to {appointment.doctor_name || "Assigned Doctor"}</span>
                </>
              ) : (
                <>
                  <span>✍️</span>
                  <span>Sign & Issue Prescription</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
