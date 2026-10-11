"use client";

import React, { useState } from "react";
import { DoctorAccount, DoctorSubTab, PatientFullHistory, HITLTask } from "@/types";

interface DoctorPortalProps {
  doctorUser: DoctorAccount | null;
  doctorSubTab: DoctorSubTab;
  setDoctorSubTab: (tab: DoctorSubTab) => void;
  onOpenDoctorLogin: () => void;
  // Dossier props
  patientSearchQuery: string;
  setPatientSearchQuery: (q: string) => void;
  onSearchPatientHistory: (identifier: string) => void;
  patientHistoryData: PatientFullHistory | null;
  historyLoading: boolean;
  // Appointments props
  appointments: any[];
  appointmentFilter: "my" | "all";
  setAppointmentFilter: (f: "my" | "all") => void;
  appointmentSearch: string;
  setAppointmentSearch: (s: string) => void;
  onOpenPrescribeModal: (app: any) => void;
  onViewPrescription: (app: any) => void;
  // HITL Approvals props
  pendingTasks: HITLTask[];
  onApproveTask: (taskId: string, notes: string, editedText?: string) => void;
  onRejectTask: (taskId: string, notes: string) => void;
}

export const DoctorPortal: React.FC<DoctorPortalProps> = ({
  doctorUser,
  doctorSubTab,
  setDoctorSubTab,
  onOpenDoctorLogin,
  patientSearchQuery,
  setPatientSearchQuery,
  onSearchPatientHistory,
  patientHistoryData,
  historyLoading,
  appointments,
  appointmentFilter,
  setAppointmentFilter,
  appointmentSearch,
  setAppointmentSearch,
  onOpenPrescribeModal,
  onViewPrescription,
  pendingTasks,
  onApproveTask,
  onRejectTask,
}) => {
  const [editingTaskId, setEditingTaskId] = useState<string | null>(null);
  const [editedText, setEditedText] = useState<string>("");
  const [doctorNotes, setDoctorNotes] = useState<string>("");

  if (!doctorUser) {
    return (
      <div
        style={{
          padding: "40px 24px",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          background: "radial-gradient(circle at 50% 25%, #f0fdfa 0%, #f8fafc 100%)",
        }}
      >
        <div
          style={{
            maxWidth: "520px",
            width: "100%",
            background: "#ffffff",
            border: "1.5px solid #ccfbf1",
            borderRadius: "24px",
            padding: "36px 32px",
            textAlign: "center",
            boxShadow: "0 12px 36px rgba(15, 118, 110, 0.08)",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "18px",
          }}
        >
          <div
            style={{
              width: "72px",
              height: "72px",
              borderRadius: "22px",
              background: "linear-gradient(135deg, #0f766e 0%, #0d9488 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "2.2rem",
              boxShadow: "0 8px 20px rgba(15, 118, 110, 0.25)",
            }}
          >
            🩺
          </div>

          <div>
            <span
              style={{
                fontSize: "0.72rem",
                fontWeight: 800,
                color: "#0f766e",
                background: "#f0fdfa",
                border: "1px solid #99f6e4",
                padding: "4px 10px",
                borderRadius: "20px",
                textTransform: "uppercase",
                letterSpacing: "0.06em",
              }}
            >
              Restricted Clinical Workstation
            </span>
            <h2 style={{ fontSize: "1.45rem", fontWeight: 800, color: "#0f172a", marginTop: "10px" }}>
              Doctor Sign-In Required
            </h2>
            <p style={{ fontSize: "0.85rem", color: "#64748b", lineHeight: "1.6", marginTop: "8px" }}>
              This portal contains protected electronic health dossiers, human-in-the-loop review queues, and electronic prescription issuance. Access is restricted to authorized clinic physicians.
            </p>
          </div>

          <div
            style={{
              width: "100%",
              background: "#f8fafc",
              border: "1px solid #e2e8f0",
              borderRadius: "14px",
              padding: "14px",
              fontSize: "0.78rem",
              color: "#334155",
              textAlign: "left",
              display: "flex",
              flexDirection: "column",
              gap: "6px",
            }}
          >
            <div style={{ fontWeight: 700, color: "#0f172a" }}>🔒 Authorized Physician Access:</div>
            <div>• Review patient dossiers & EHR history</div>
            <div>• Approve or reject clinical safety advisories (HITL)</div>
            <div>• Issue official signed prescriptions (℞)</div>
          </div>

          <button
            className="btn-primary"
            onClick={onOpenDoctorLogin}
            style={{
              width: "100%",
              padding: "13px 20px",
              fontSize: "0.95rem",
              fontWeight: 700,
              borderRadius: "14px",
              background: "#0f766e",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "8px",
              boxShadow: "0 4px 14px rgba(15, 118, 110, 0.2)",
            }}
          >
            <span>🔐</span>
            <span>Sign In to Doctor Workstation</span>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: "24px", overflowY: "auto", height: "100%", display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Top Banner with Doctor Status & Sub-Tabs */}
      <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "20px", padding: "20px", boxShadow: "0 2px 8px rgba(0,0,0,0.03)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "14px" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <span style={{ fontSize: "1.5rem" }}>🩺</span>
              <div>
                <h2 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#0f172a" }}>
                  Doctor Clinical Workstation
                </h2>
                <div style={{ fontSize: "0.8rem", color: "#64748b" }}>
                  {doctorUser ? (
                    <span>Logged in as <strong>{doctorUser.doctor_name}</strong> ({doctorUser.specialty})</span>
                  ) : (
                    <span>Operating in demo clinician mode. Sign in to tie actions to your PMDC account.</span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {!doctorUser && (
            <button className="btn-primary" onClick={onOpenDoctorLogin}>
              Doctor Sign In
            </button>
          )}
        </div>

        {/* Sub-Tab Navigation */}
        <div style={{ display: "flex", gap: "8px", marginTop: "18px", borderTop: "1px solid #f1f5f9", paddingTop: "14px" }}>
          <button
            onClick={() => setDoctorSubTab("dossier")}
            style={{
              padding: "8px 16px",
              borderRadius: "12px",
              border: "none",
              fontSize: "0.84rem",
              fontWeight: 600,
              cursor: "pointer",
              background: doctorSubTab === "dossier" ? "#0f766e" : "#f1f5f9",
              color: doctorSubTab === "dossier" ? "#ffffff" : "#475569",
              transition: "all 0.15s ease",
            }}
          >
            📋 Patient Dossier (EHR)
          </button>

          <button
            onClick={() => setDoctorSubTab("appointments")}
            style={{
              padding: "8px 16px",
              borderRadius: "12px",
              border: "none",
              fontSize: "0.84rem",
              fontWeight: 600,
              cursor: "pointer",
              background: doctorSubTab === "appointments" ? "#0f766e" : "#f1f5f9",
              color: doctorSubTab === "appointments" ? "#ffffff" : "#475569",
              transition: "all 0.15s ease",
            }}
          >
            🗓️ Consultations & Prescriptions ({appointments.length})
          </button>

          <button
            onClick={() => setDoctorSubTab("approvals")}
            style={{
              padding: "8px 16px",
              borderRadius: "12px",
              border: "none",
              fontSize: "0.84rem",
              fontWeight: 600,
              cursor: "pointer",
              background: doctorSubTab === "approvals" ? "#0f766e" : "#f1f5f9",
              color: doctorSubTab === "approvals" ? "#ffffff" : "#475569",
              display: "flex",
              alignItems: "center",
              gap: "6px",
              transition: "all 0.15s ease",
            }}
          >
            <span>🛡️ HITL Approval Gate</span>
            {pendingTasks.length > 0 && (
              <span style={{ background: "#ea580c", color: "#ffffff", padding: "1px 6px", borderRadius: "10px", fontSize: "0.72rem" }}>
                {pendingTasks.length}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* VIEW 1: Patient Dossier */}
      {doctorSubTab === "dossier" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {/* Search Bar */}
          <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "16px", padding: "16px", display: "flex", gap: "10px", alignItems: "center" }}>
            <input
              type="text"
              className="form-input"
              placeholder="Search patient by MRN (e.g. MRN-1001) or phone number..."
              value={patientSearchQuery}
              onChange={(e) => setPatientSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && onSearchPatientHistory(patientSearchQuery)}
            />
            <button
              className="btn-primary"
              onClick={() => onSearchPatientHistory(patientSearchQuery)}
              disabled={historyLoading || !patientSearchQuery.trim()}
            >
              {historyLoading ? "Searching..." : "Search EHR"}
            </button>
          </div>

          {/* Dossier Results */}
          {patientHistoryData ? (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: "16px" }}>
              {/* Demographics & Vitals */}
              <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "18px", padding: "20px", display: "flex", flexDirection: "column", gap: "14px" }}>
                <div style={{ borderBottom: "1px solid #f1f5f9", paddingBottom: "12px" }}>
                  <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#0f172a" }}>
                    {patientHistoryData.patient_name}
                  </h3>
                  <div style={{ fontSize: "0.78rem", color: "#0f766e", fontWeight: 600 }}>
                    MRN: {patientHistoryData.mrn} • Age: {patientHistoryData.age} • Gender: {patientHistoryData.gender}
                  </div>
                  <div style={{ fontSize: "0.76rem", color: "#64748b", marginTop: "4px" }}>
                    Phone: {patientHistoryData.phone}
                  </div>
                </div>

                <div>
                  <h4 style={{ fontSize: "0.82rem", fontWeight: 700, color: "#334155", marginBottom: "6px" }}>Known Allergies:</h4>
                  <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                    {patientHistoryData.known_allergies?.length ? (
                      patientHistoryData.known_allergies.map((a, i) => (
                        <span key={i} style={{ background: "#fee2e2", color: "#b91c1c", fontSize: "0.74rem", padding: "3px 8px", borderRadius: "6px" }}>
                          ⚠️ {a}
                        </span>
                      ))
                    ) : (
                      <span style={{ fontSize: "0.78rem", color: "#64748b" }}>No known allergies</span>
                    )}
                  </div>
                </div>

                <div>
                  <h4 style={{ fontSize: "0.82rem", fontWeight: 700, color: "#334155", marginBottom: "6px" }}>Chronic Conditions:</h4>
                  <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                    {patientHistoryData.chronic_conditions?.length ? (
                      patientHistoryData.chronic_conditions.map((c, i) => (
                        <span key={i} style={{ background: "#fef3c7", color: "#b45309", fontSize: "0.74rem", padding: "3px 8px", borderRadius: "6px" }}>
                          {c}
                        </span>
                      ))
                    ) : (
                      <span style={{ fontSize: "0.78rem", color: "#64748b" }}>None recorded</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Longitudinal Consultations & Medications */}
              <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "18px", padding: "20px", display: "flex", flexDirection: "column", gap: "16px" }}>
                <h3 style={{ fontSize: "1rem", fontWeight: 700, color: "#0f172a" }}>
                  Clinical Encounter Timeline & Past Prescriptions
                </h3>

                {patientHistoryData.encounters && patientHistoryData.encounters.length > 0 ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                    {patientHistoryData.encounters.map((enc: any, idx: number) => (
                      <div key={idx} style={{ background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "12px", padding: "12px" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8rem", fontWeight: 700, color: "#0f766e" }}>
                          <span>{enc.date || "Past Visit"}</span>
                          <span>Dr. {enc.doctor_name || "Specialist"}</span>
                        </div>
                        <div style={{ fontSize: "0.82rem", color: "#334155", marginTop: "4px" }}>
                          {enc.complaint || enc.diagnosis || "Routine Clinical Consultation"}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p style={{ fontSize: "0.82rem", color: "#64748b" }}>
                    No prior clinical encounters logged for this patient.
                  </p>
                )}
              </div>
            </div>
          ) : (
            <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "18px", padding: "50px 20px", textAlign: "center" }}>
              <div style={{ fontSize: "2rem", marginBottom: "8px" }}>🔍</div>
              <h4 style={{ fontWeight: 700, color: "#334155" }}>Search for a Patient Record</h4>
              <p style={{ fontSize: "0.8rem", color: "#64748b", marginTop: "4px" }}>
                Enter an MRN or phone number above to inspect comprehensive clinical records, vitals, and medication histories.
              </p>
            </div>
          )}
        </div>
      )}

      {/* VIEW 2: Doctor Appointments & Prescriptions */}
      {doctorSubTab === "appointments" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {/* Controls */}
          <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "16px", padding: "14px", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px" }}>
            <div style={{ display: "flex", gap: "8px" }}>
              <button
                className={appointmentFilter === "my" ? "btn-primary" : "btn-secondary"}
                style={{ padding: "6px 14px", fontSize: "0.78rem" }}
                onClick={() => setAppointmentFilter("my")}
              >
                My Patients
              </button>
              <button
                className={appointmentFilter === "all" ? "btn-primary" : "btn-secondary"}
                style={{ padding: "6px 14px", fontSize: "0.78rem" }}
                onClick={() => setAppointmentFilter("all")}
              >
                All Clinic Appointments
              </button>
            </div>

            <input
              type="text"
              className="form-input"
              placeholder="Search by patient name, MRN, date..."
              style={{ width: "260px", padding: "6px 12px", fontSize: "0.8rem" }}
              value={appointmentSearch}
              onChange={(e) => setAppointmentSearch(e.target.value)}
            />
          </div>

          {/* Appointments Grid */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: "16px" }}>
            {appointments.map((app: any, idx: number) => {
              const hasRx = !!app.prescription || !!app.prescription_id;
              return (
                <div key={app.appointment_id || idx} style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "16px", padding: "18px", display: "flex", flexDirection: "column", justifyContent: "space-between", gap: "12px", boxShadow: "0 2px 6px rgba(0,0,0,0.02)" }}>
                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "8px" }}>
                      <span style={{ fontSize: "0.72rem", background: "#f1f5f9", color: "#0f766e", fontWeight: 700, padding: "2px 8px", borderRadius: "6px", fontFamily: "var(--font-mono)" }}>
                        {app.booking_reference || app.booking_ref || app.appointment_id}
                      </span>
                      <span style={{ fontSize: "0.7rem", fontWeight: 700, color: "#059669", background: "#ecfdf5", padding: "2px 8px", borderRadius: "10px" }}>
                        {app.status || "CONFIRMED"}
                      </span>
                    </div>

                    <h4 style={{ fontSize: "0.98rem", fontWeight: 700, color: "#0f172a" }}>
                      {app.patient_name || "Patient"}
                    </h4>
                    <div style={{ fontSize: "0.78rem", color: "#64748b" }}>
                      MRN: {app.mrn || "P001"} • Phone: {app.phone}
                    </div>

                    <div style={{ marginTop: "10px", fontSize: "0.78rem", color: "#334155" }}>
                      📅 {app.date} • ⏰ {app.time_slot || app.time}
                    </div>

                    {app.reason && (
                      <div style={{ fontSize: "0.74rem", color: "#64748b", marginTop: "6px", background: "#f8fafc", padding: "6px 8px", borderRadius: "6px" }}>
                        Chief Complaint: {app.reason}
                      </div>
                    )}
                  </div>

                  <div style={{ display: "flex", gap: "8px", borderTop: "1px solid #f1f5f9", paddingTop: "12px" }}>
                    <button
                      className="btn-primary"
                      style={{ flex: 1, padding: "8px 12px", fontSize: "0.78rem" }}
                      onClick={() => onOpenPrescribeModal(app)}
                    >
                      💊 Write Rx
                    </button>
                    {hasRx && (
                      <button
                        className="btn-secondary"
                        style={{ padding: "8px 12px", fontSize: "0.78rem" }}
                        onClick={() => onViewPrescription(app)}
                      >
                        View Rx
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* VIEW 3: HITL Approvals */}
      {doctorSubTab === "approvals" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div style={{ background: "#fffbeb", border: "1px solid #fde68a", borderRadius: "16px", padding: "16px", display: "flex", alignItems: "center", gap: "12px" }}>
            <span style={{ fontSize: "1.5rem" }}>🛡️</span>
            <div>
              <div style={{ fontWeight: 700, color: "#92400e", fontSize: "0.9rem" }}>
                Human-in-the-Loop (HITL) Medical Safety Gate
              </div>
              <div style={{ fontSize: "0.78rem", color: "#b45309" }}>
                AI responses with prescription updates or critical clinical guidance pause here for doctor sign-off before being delivered to the patient.
              </div>
            </div>
          </div>

          {pendingTasks.length === 0 ? (
            <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "18px", padding: "50px 20px", textAlign: "center" }}>
              <div style={{ fontSize: "2rem", marginBottom: "8px" }}>✅</div>
              <h4 style={{ fontWeight: 700, color: "#059669" }}>All Clinical Reviews Cleared</h4>
              <p style={{ fontSize: "0.8rem", color: "#64748b", marginTop: "4px" }}>
                There are currently no pending tasks in the Human-in-the-Loop queue.
              </p>
            </div>
          ) : (
            pendingTasks.map((task) => (
              <div key={task.task_id} style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "18px", padding: "20px", display: "flex", flexDirection: "column", gap: "14px", boxShadow: "0 2px 8px rgba(0,0,0,0.03)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div>
                    <span style={{ background: "#fee2e2", color: "#b91c1c", fontSize: "0.72rem", fontWeight: 700, padding: "3px 8px", borderRadius: "6px" }}>
                      URGENCY: {task.urgency_level || "HIGH"}
                    </span>
                    <span style={{ marginLeft: "8px", fontSize: "0.76rem", color: "#64748b" }}>
                      Patient: <strong>{task.patient_name || task.patient_id}</strong>
                    </span>
                  </div>
                  <span style={{ fontSize: "0.72rem", color: "#94a3b8" }}>{task.created_at}</span>
                </div>

                <div style={{ background: "#f8fafc", padding: "12px", borderRadius: "10px", fontSize: "0.82rem", color: "#334155" }}>
                  <strong>Trigger Reason:</strong> {task.reason || task.task_type}
                </div>

                {/* Proposed Message */}
                <div>
                  <div style={{ fontSize: "0.78rem", fontWeight: 700, color: "#0f766e", marginBottom: "6px" }}>
                    Proposed AI Response to Patient:
                  </div>
                  {editingTaskId === task.task_id ? (
                    <textarea
                      className="form-input"
                      rows={4}
                      value={editedText}
                      onChange={(e) => setEditedText(e.target.value)}
                    />
                  ) : (
                    <div style={{ background: "#f0fdf9", border: "1px solid #ccfbf1", borderRadius: "10px", padding: "12px", fontSize: "0.85rem", color: "#065f46", lineHeight: 1.5 }}>
                      {task.proposed_message_urdulish || task.proposed_response}
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderTop: "1px solid #f1f5f9", paddingTop: "12px" }}>
                  <button
                    className="btn-secondary"
                    style={{ fontSize: "0.78rem" }}
                    onClick={() => {
                      if (editingTaskId === task.task_id) {
                        setEditingTaskId(null);
                      } else {
                        setEditingTaskId(task.task_id);
                        setEditedText(task.proposed_message_urdulish || task.proposed_response || "");
                      }
                    }}
                  >
                    {editingTaskId === task.task_id ? "Cancel Edit" : "✏️ Edit Draft"}
                  </button>

                  <div style={{ display: "flex", gap: "8px" }}>
                    <button
                      className="btn-secondary"
                      style={{ color: "#e11d48", fontSize: "0.78rem" }}
                      onClick={() => onRejectTask(task.task_id, doctorNotes)}
                    >
                      Reject
                    </button>
                    <button
                      className="btn-primary"
                      style={{ fontSize: "0.78rem", background: "#059669" }}
                      onClick={() => onApproveTask(task.task_id, doctorNotes, editingTaskId === task.task_id ? editedText : undefined)}
                    >
                      ✅ Approve & Send to Patient
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};
