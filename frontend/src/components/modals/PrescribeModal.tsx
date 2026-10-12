"use client";

import React from "react";

interface PrescribeModalProps {
  isOpen: boolean;
  onClose: () => void;
  appointment: any;
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
  onSubmit: (e: React.FormEvent) => void;
}

export const PrescribeModal: React.FC<PrescribeModalProps> = ({
  isOpen,
  onClose,
  appointment,
  prescriptionForm,
  setPrescriptionForm,
  onAddMedicineRow,
  onRemoveMedicineRow,
  onMedicineChange,
  isSubmitting,
  onSubmit,
}) => {
  if (!isOpen || !appointment) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" style={{ maxWidth: "720px" }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <div>
            <h2 style={{ fontSize: "1.2rem", fontWeight: 700, color: "#0f172a" }}>
              💊 Issue Electronic Prescription (Rx)
            </h2>
            <div style={{ fontSize: "0.78rem", color: "#64748b" }}>
              Patient: <strong>{appointment.patient_name}</strong> (MRN: {appointment.mrn || appointment.patient_mrn || "P001"}) • Attending: <strong>{appointment.doctor_name || "Clinic Specialist"}</strong>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{ background: "transparent", border: "none", color: "#94a3b8", fontSize: "1.2rem", cursor: "pointer" }}
          >
            ✕
          </button>
        </div>

        <form onSubmit={onSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {/* Diagnosis */}
          <div>
            <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: "#334155", marginBottom: "4px" }}>
              Clinical Diagnosis / Assessment *
            </label>
            <input
              type="text"
              required
              className="form-input"
              placeholder="e.g. Acute Upper Respiratory Tract Infection (URTI) with mild fever"
              value={prescriptionForm.diagnosis}
              onChange={(e) => setPrescriptionForm({ ...prescriptionForm, diagnosis: e.target.value })}
            />
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
                style={{ background: "#ecfdf5", border: "1px solid #a7f3d0", color: "#047857", borderRadius: "8px", padding: "4px 10px", fontSize: "0.74rem", fontWeight: 600, cursor: "pointer" }}
              >
                + Add Medication
              </button>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {prescriptionForm.medicines.map((med, idx) => (
                <div key={idx} style={{ background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "10px", padding: "10px", display: "grid", gridTemplateColumns: "1.5fr 1fr 1fr 1fr auto", gap: "8px", alignItems: "center" }}>
                  <input
                    type="text"
                    required
                    className="form-input"
                    placeholder="Medicine (e.g. Tab Panadol)"
                    style={{ fontSize: "0.8rem", padding: "6px 8px" }}
                    value={med.medicine_name}
                    onChange={(e) => onMedicineChange(idx, "medicine_name", e.target.value)}
                  />
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Dosage (500mg)"
                    style={{ fontSize: "0.8rem", padding: "6px 8px" }}
                    value={med.dosage}
                    onChange={(e) => onMedicineChange(idx, "dosage", e.target.value)}
                  />
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Freq (1-0-1)"
                    style={{ fontSize: "0.8rem", padding: "6px 8px" }}
                    value={med.frequency}
                    onChange={(e) => onMedicineChange(idx, "frequency", e.target.value)}
                  />
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Duration (5 days)"
                    style={{ fontSize: "0.8rem", padding: "6px 8px" }}
                    value={med.duration}
                    onChange={(e) => onMedicineChange(idx, "duration", e.target.value)}
                  />
                  <button
                    type="button"
                    onClick={() => onRemoveMedicineRow(idx)}
                    style={{ background: "none", border: "none", color: "#e11d48", cursor: "pointer", fontSize: "1rem" }}
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Advice / Notes */}
          <div>
            <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: "#334155", marginBottom: "4px" }}>
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
          <div style={{ display: "flex", gap: "10px", marginTop: "6px" }}>
            <button type="button" className="btn-secondary" onClick={onClose} style={{ flex: 1 }}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={isSubmitting} style={{ flex: 2 }}>
              {isSubmitting ? "Signing & Issuing Rx..." : "Sign & Issue Prescription"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
