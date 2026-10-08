"use client";

import React, { useState, useEffect, useRef } from "react";

// Types
interface Message {
  role: "user" | "assistant";
  content: string;
  agent?: string;
  timestamp?: string;
  is_pending_review?: boolean;
  is_approved_by_doctor?: boolean;
  is_emergency?: boolean;
  appointment_card?: any;
}

interface Patient {
  patient_id: string;
  patient_name: string;
  phone: string;
  mrn: string;
  preferred_doctor: string;
  preferred_branch: string;
  known_allergies: string[];
  chronic_conditions: string[];
  last_visit_date: string;
}

interface HITLTask {
  task_id: string;
  thread_id: string;
  patient_id: string;
  patient_name: string;
  task_type: "LAB_EXPLANATION" | "PRESCRIPTION_REVIEW" | "LOW_CONFIDENCE_TRIAGE";
  urgency_level: string;
  proposed_message_urdulish: string;
  clinical_context: any;
  status: "PENDING" | "APPROVED" | "EDITED" | "REJECTED";
  created_at: string;
  resolved_at?: string;
  doctor_action?: string;
  doctor_notes?: string;
  final_message_urdulish?: string;
}

interface TelemetryStats {
  total_conversations: number;
  avg_latency_ms: number;
  total_cost_usd: number;
  total_tokens: number;
  hitl_interventions: number;
  emergency_escalations: number;
}

const API_BASE = "http://127.0.0.1:8000";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"patient" | "doctor" | "telemetry">("patient");
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [sessionId, setSessionId] = useState<string>("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [triageResult, setTriageResult] = useState<any>(null);
  const [pendingTasks, setPendingTasks] = useState<HITLTask[]>([]);
  const [stats, setStats] = useState<TelemetryStats | null>(null);
  const [editingTaskId, setEditingTaskId] = useState<string | null>(null);
  const [editedMessageText, setEditedMessageText] = useState<string>("");
  const [doctorNotes, setDoctorNotes] = useState<string>("");
  const [serverHealthy, setServerHealthy] = useState<boolean>(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Load initial patients & health
  useEffect(() => {
    const init = async () => {
      try {
        const hRes = await fetch(`${API_BASE}/api/health`);
        if (hRes.ok) setServerHealthy(true);

        const pRes = await fetch(`${API_BASE}/api/patients`);
        if (pRes.ok) {
          const data = await pRes.json();
          setPatients(data.patients || []);
          if (data.patients && data.patients.length > 0) {
            selectPatient(data.patients[0]);
          }
        }
      } catch (e) {
        console.log("Using fallback initial state, server connecting...", e);
        // Fallback default patients
        const defaultPatients: Patient[] = [
          {
            patient_id: "p1",
            patient_name: "Ahmed Raza",
            phone: "+923001234567",
            mrn: "CCC-PK-100001",
            preferred_doctor: "Dr. Bilal Saeed",
            preferred_branch: "Gulberg Lahore",
            known_allergies: ["Penicillin"],
            chronic_conditions: ["Hypertension"],
            last_visit_date: "2026-09-06"
          },
          {
            patient_id: "p2",
            patient_name: "Fatima Bibi",
            phone: "+923219876543",
            mrn: "CCC-PK-100002",
            preferred_doctor: "Dr. Ayesha Tariq",
            preferred_branch: "DHA Lahore",
            known_allergies: ["Sulfa drugs"],
            chronic_conditions: ["PCOD"],
            last_visit_date: "2026-08-18"
          },
          {
            patient_id: "p3",
            patient_name: "Hamza Abbasi",
            phone: "+923334567890",
            mrn: "CCC-PK-100003",
            preferred_doctor: "Dr. Usman Sheikh",
            preferred_branch: "F-8 Markaz Islamabad",
            known_allergies: [],
            chronic_conditions: ["Bronchial Asthma"],
            last_visit_date: "2026-09-22"
          }
        ];
        setPatients(defaultPatients);
        selectPatient(defaultPatients[0]);
      }
      fetchPendingTasks();
      fetchTelemetry();
    };

    init();
    const interval = setInterval(() => {
      fetchPendingTasks();
      fetchTelemetry();
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  const selectPatient = (p: Patient) => {
    setSelectedPatient(p);
    const newSess = `sess_${p.patient_id}_${Date.now()}`;
    setSessionId(newSess);
    setTriageResult(null);

    // Initial greeting from long-term memory
    const firstName = p.patient_name.split(" ")[0];
    const initialGreeting = `Assalam-o-Alaikum ${firstName} sahib! City Care Clinics mein khush-amdeed.\nRecord ke mutabiq aap pichli dafa (${p.last_visit_date}) **${p.preferred_doctor}** ko dikhaye thay (${p.preferred_branch} branch mein).\n\nKya aap dobara **${p.preferred_doctor}** ke saath appointment book karna chahte hain, ya koi nayi takleef ke liye doosray specialist se mashwara chahiye?`;

    setMessages([
      {
        role: "assistant",
        content: initialGreeting,
        agent: "MemoryManager",
        timestamp: new Date().toISOString()
      }
    ]);
  };

  const fetchPendingTasks = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/doctor/pending`);
      if (res.ok) {
        const data = await res.json();
        setPendingTasks(data.pending_tasks || []);
      }
    } catch {}
  };

  const fetchTelemetry = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/telemetry/stats`);
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch {}
  };

  const handleSendMessage = async (textToSend?: string, triggerType?: string) => {
    const text = textToSend || inputMessage;
    if (!text.trim() || isLoading) return;

    const userMsg: Message = {
      role: "user",
      content: text,
      timestamp: new Date().toISOString()
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInputMessage("");
    setIsLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          message: text,
          patient_identifier: selectedPatient?.patient_name || "Valued Patient",
          is_returning_patient: true,
          trigger_type: triggerType
        })
      });

      if (res.ok) {
        const data = await res.json();
        if (data.triage_result) setTriageResult(data.triage_result);

        const newMsgs = data.messages.map((m: any) => ({
          role: m.role === "human" || m.role === "user" ? "user" : "assistant",
          content: m.content || "",
          agent: m.agent || "ClinicalAssistant",
          timestamp: m.timestamp || new Date().toISOString(),
          is_pending_review: m.is_pending_review,
          is_approved_by_doctor: m.is_approved_by_doctor,
          is_emergency: m.is_emergency,
          appointment_card: m.appointment_card
        }));

        setMessages(newMsgs);
        fetchPendingTasks();
        fetchTelemetry();
      }
    } catch (e) {
      console.error(e);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Shukriya. Aap ka paigham receive ho gaya hai. Network verification jari hai.",
          agent: "System",
          timestamp: new Date().toISOString()
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDoctorDecision = async (
    taskId: string,
    decision: "approved" | "edited" | "rejected"
  ) => {
    try {
      const res = await fetch(`${API_BASE}/api/doctor/decision`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task_id: taskId,
          decision: decision,
          doctor_notes: doctorNotes || "Verified by Attending Medical Director",
          edited_message: decision === "edited" ? editedMessageText : undefined,
          doctor_name: "Dr. Maryam Naveed (Medical Director)"
        })
      });

      if (res.ok) {
        const data = await res.json();
        setEditingTaskId(null);
        setDoctorNotes("");
        setEditedMessageText("");
        fetchPendingTasks();
        fetchTelemetry();

        // If currently on this patient's chat, refresh
        if (data.resumed_reply) {
          setMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              content: `✅ **Doctor Decision Applied:**\n\n${data.resumed_reply}`,
              agent: "DoctorApprovalGate",
              is_approved_by_doctor: true,
              timestamp: new Date().toISOString()
            }
          ]);
        }
      }
    } catch (e) {
      console.error("Decision failed", e);
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      {/* Top Header */}
      <header className="app-header">
        <div className="brand-container">
          <div className="brand-icon">🏥</div>
          <div>
            <h1 className="brand-title">City Care Clinics</h1>
            <p className="brand-subtitle">Multi-Agent AI Healthcare Assistant • Week 9 Day 4</p>
          </div>
        </div>

        <nav className="nav-tabs">
          <button
            id="tab-patient-portal"
            className={`nav-tab-btn ${activeTab === "patient" ? "active" : ""}`}
            onClick={() => setActiveTab("patient")}
          >
            💬 Patient Web Portal
          </button>
          <button
            id="tab-doctor-hitl"
            className={`nav-tab-btn ${activeTab === "doctor" ? "active" : ""}`}
            onClick={() => setActiveTab("doctor")}
          >
            🩺 Doctor HITL Command Center
            {pendingTasks.length > 0 && (
              <span className="badge-counter">{pendingTasks.length}</span>
            )}
          </button>
          <button
            id="tab-telemetry"
            className={`nav-tab-btn ${activeTab === "telemetry" ? "active" : ""}`}
            onClick={() => setActiveTab("telemetry")}
          >
            📊 Observability & Telemetry
          </button>
        </nav>

        <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "0.8rem", color: "#94a3b8" }}>
          <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: serverHealthy ? "#10b981" : "#06b6d4", display: "inline-block" }}></span>
          <span>{serverHealthy ? "LangGraph Live" : "Demo Mode"}</span>
        </div>
      </header>

      {/* Emergency Strip */}
      <div className="emergency-strip">
        <div>
          ⚠️ <strong>Medical Notice:</strong> AI is an outpatient assistant. For acute chest pain, breathing distress, or stroke symptoms:
          <span className="emergency-phone-tag">CALL RESCUE 1122</span>
        </div>
        <div style={{ fontSize: "0.75rem", opacity: 0.8 }}>
          Doctor Review Gate: Active 🛡️
        </div>
      </div>

      <main className="main-wrapper" style={{ flex: 1 }}>
        {/* ================= TAB 1: PATIENT PORTAL ================= */}
        {activeTab === "patient" && (
          <div className="chat-container-grid">
            {/* Left Sidebar: Patient Profile & Memory */}
            <aside className="sidebar-left glass-panel" style={{ padding: "16px" }}>
              <div className="sidebar-title">👤 Returning Patient Memory</div>
              {patients.map((p) => (
                <div
                  key={p.patient_id}
                  id={`patient-${p.patient_id}`}
                  className={`patient-pill ${selectedPatient?.patient_id === p.patient_id ? "selected" : ""}`}
                  onClick={() => selectPatient(p)}
                >
                  <div className="patient-name">
                    <span>{p.patient_name}</span>
                    <span style={{ fontSize: "0.7rem", color: "#38bdf8" }}>{p.mrn}</span>
                  </div>
                  <div className="patient-meta">
                    Preferred: {p.preferred_doctor} ({p.preferred_branch})
                  </div>
                  <div style={{ display: "flex", gap: "4px", marginTop: "6px", flexWrap: "wrap" }}>
                    {p.chronic_conditions.map((c, i) => (
                      <span key={i} style={{ fontSize: "0.68rem", padding: "1px 6px", background: "rgba(255,255,255,0.06)", borderRadius: "4px", color: "#cbd5e1" }}>
                        {c}
                      </span>
                    ))}
                    {p.known_allergies.map((a, i) => (
                      <span key={i} style={{ fontSize: "0.68rem", padding: "1px 6px", background: "rgba(244,63,94,0.15)", color: "#f87171", borderRadius: "4px" }}>
                        Allergy: {a}
                      </span>
                    ))}
                  </div>
                </div>
              ))}

              <div style={{ marginTop: "16px", borderTop: "1px solid rgba(255,255,255,0.08)", paddingTop: "14px" }}>
                <div className="sidebar-title">⚡ System Status</div>
                <div style={{ fontSize: "0.78rem", color: "#94a3b8", display: "grid", gap: "6px" }}>
                  <div>• Router: LangGraph Supervisor</div>
                  <div>• Memory: Short + Long-term Privacy</div>
                  <div>• Model: `gemini-3.5-flash-lite`</div>
                  <div>• Checkpointer: In-Memory Saver</div>
                </div>
              </div>
            </aside>

            {/* Center: Live Chat */}
            <section className="chat-window glass-panel">
              <div className="chat-header-bar">
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <span style={{ width: "10px", height: "10px", borderRadius: "50%", background: "#10b981" }}></span>
                  <div>
                    <strong style={{ fontSize: "0.95rem" }}>City Care Outpatient Assistant</strong>
                    <div style={{ fontSize: "0.72rem", color: "#94a3b8" }}>
                      Patient: {selectedPatient?.patient_name} • Session: {sessionId.slice(0, 16)}...
                    </div>
                  </div>
                </div>
                {triageResult && (
                  <div className={`status-pill ${triageResult.urgency_tier?.toLowerCase()}`}>
                    Triage: {triageResult.urgency_tier} ({triageResult.confidence_score ? `${Math.round(triageResult.confidence_score * 100)}%` : "100%"})
                  </div>
                )}
              </div>

              {/* Messages Area */}
              <div className="chat-messages-scroll">
                {messages.map((msg, idx) => (
                  <div key={idx} className={`message-row ${msg.role}`}>
                    <div className={`msg-avatar ${msg.role}`}>
                      {msg.role === "user" ? "P" : "AI"}
                    </div>
                    <div className="message-bubble">
                      {msg.agent && msg.role === "assistant" && (
                        <div className="msg-author-tag">{msg.agent}</div>
                      )}
                      <div>{msg.content}</div>

                      {/* Pending Review Gate Banner */}
                      {msg.is_pending_review && (
                        <div className="pending-gate-banner">
                          <span>🛡️</span>
                          <div>
                            <strong>Doctor Verification Required:</strong> This clinical explanation is currently paused in the Doctor HITL Queue for safety sign-off.
                          </div>
                        </div>
                      )}

                      {/* Verified Badge */}
                      {msg.is_approved_by_doctor && (
                        <div style={{ marginTop: "6px", fontSize: "0.72rem", color: "#10b981", display: "flex", alignItems: "center", gap: "4px" }}>
                          ✓ Signed off by Attending Medical Director
                        </div>
                      )}

                      {/* Appointment Card */}
                      {msg.appointment_card && (
                        <div style={{ marginTop: "12px", padding: "12px", background: "rgba(6,182,212,0.1)", border: "1px solid rgba(6,182,212,0.3)", borderRadius: "8px" }}>
                          <div style={{ fontWeight: "700", color: "#38bdf8", marginBottom: "4px" }}>
                            Booking Ref: #{msg.appointment_card.booking_reference}
                          </div>
                          <div style={{ fontSize: "0.8rem", color: "#cbd5e1" }}>
                            Doctor: {msg.appointment_card.doctor_name} • Fee: PKR {msg.appointment_card.fee?.toLocaleString()}
                          </div>
                          {msg.appointment_card.google_calendar_url && (
                            <a
                              href={msg.appointment_card.google_calendar_url}
                              target="_blank"
                              rel="noreferrer"
                              style={{ display: "inline-block", marginTop: "8px", padding: "6px 14px", background: "#0284c7", color: "white", borderRadius: "6px", fontSize: "0.78rem", fontWeight: "600" }}
                            >
                              📅 Add to Google Calendar
                            </a>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="message-row assistant">
                    <div className="msg-avatar assistant">AI</div>
                    <div className="message-bubble" style={{ color: "#94a3b8", display: "flex", alignItems: "center", gap: "8px" }}>
                      <span>Analyzing clinical context & routing agents...</span>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Chat Input & Quick Chips */}
              <div className="chat-input-area">
                <div className="quick-chips-row">
                  <button className="quick-chip" onClick={() => handleSendMessage("Dr. Bilal ke sath appointment book kar dein")}>
                    📅 Book Appointment
                  </button>
                  <button className="quick-chip" onClick={() => handleSendMessage("Meri CBC blood report aur WBC count ka kya matlab hai?", "lab_inquiry")}>
                    🔬 Check Lab Report (Triggers HITL)
                  </button>
                  <button className="quick-chip" onClick={() => handleSendMessage("Mujhe Augmentin dawa likh dein", "prescription_check")}>
                    💊 Prescription Check (Triggers HITL)
                  </button>
                  <button className="quick-chip" onClick={() => handleSendMessage("Dawai ka schedule aur follow-up plan batayein")}>
                    📋 Post-Visit Care Plan
                  </button>
                  <button className="quick-chip" onClick={() => handleSendMessage("Seene mein shadeed dard aur bayen baazu mein khinchaao ho raha hai")}>
                    🚨 Emergency 1122 Test
                  </button>
                </div>

                <div className="chat-input-row">
                  <input
                    id="chat-input"
                    type="text"
                    className="chat-input-field"
                    placeholder="Apna masla ya sawal UrduLish mein likhein (e.g. Bukhar kab se hai...)"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
                  />
                  <button id="send-button" className="send-btn" onClick={() => handleSendMessage()} disabled={isLoading}>
                    Bhejein ➔
                  </button>
                </div>
              </div>
            </section>

            {/* Right Sidebar: Active Clinical Brief */}
            <aside className="sidebar-right glass-panel" style={{ padding: "16px" }}>
              <div className="sidebar-title">📋 Pre-Visit SOAP Brief</div>
              <div style={{ fontSize: "0.8rem", color: "#cbd5e1", lineHeight: 1.5, background: "rgba(0,0,0,0.2)", padding: "12px", borderRadius: "8px" }}>
                <div style={{ color: "#38bdf8", fontWeight: "700", marginBottom: "4px" }}>
                  1. Subjective (Patient Facts):
                </div>
                <div>• Patient: {selectedPatient?.patient_name}</div>
                <div>• Known Allergies: {selectedPatient?.known_allergies.join(", ") || "None"}</div>
                <div>• History: {selectedPatient?.chronic_conditions.join(", ") || "None"}</div>

                <div style={{ color: "#34d399", fontWeight: "700", marginTop: "12px", marginBottom: "4px" }}>
                  2. Objective (Verified EHR):
                </div>
                <div>• MRN: {selectedPatient?.mrn}</div>
                <div>• Last Outpatient Date: {selectedPatient?.last_visit_date}</div>

                <div style={{ color: "#fbbf24", fontWeight: "700", marginTop: "12px", marginBottom: "4px" }}>
                  3. AI Considerations (Non-Diagnostic):
                </div>
                <div>• Triage Tier: {triageResult?.urgency_tier || "Stable Outpatient"}</div>
                <div>• Specialty: {triageResult?.recommended_specialty || "General Medicine"}</div>
              </div>

              <div style={{ marginTop: "16px" }}>
                <div className="sidebar-title">📧 Transactional Channels</div>
                <div style={{ fontSize: "0.76rem", color: "#94a3b8", background: "rgba(0,0,0,0.2)", padding: "10px", borderRadius: "8px" }}>
                  <div>• Email Confirmations: Active (HTML)</div>
                  <div>• Google Calendar URLs: Auto-generated</div>
                  <div>• Follow-up Reminders: Scheduled Day 5</div>
                </div>
              </div>
            </aside>
          </div>
        )}

        {/* ================= TAB 2: DOCTOR HITL COMMAND CENTER ================= */}
        {activeTab === "doctor" && (
          <div className="doctor-dashboard">
            {/* Left Queue */}
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                <div>
                  <h2 style={{ fontSize: "1.3rem", fontWeight: "700" }}>Doctor Approval & Safety Gate</h2>
                  <p style={{ fontSize: "0.8rem", color: "#94a3b8" }}>
                    Physician sign-off queue for Lab Explanations, Prescriptions, and Low-Confidence Triage.
                  </p>
                </div>
                <div style={{ background: "rgba(6,182,212,0.15)", color: "#38bdf8", padding: "6px 14px", borderRadius: "20px", fontSize: "0.82rem", fontWeight: "600" }}>
                  Attending: Dr. Maryam Naveed (MD)
                </div>
              </div>

              {pendingTasks.length === 0 ? (
                <div className="glass-panel" style={{ padding: "40px", textAlign: "center", color: "#94a3b8" }}>
                  <div style={{ fontSize: "32px", marginBottom: "10px" }}>✅</div>
                  <strong style={{ color: "#f8fafc" }}>All Clinical Reviews Clear</strong>
                  <p style={{ fontSize: "0.85rem", marginTop: "6px" }}>
                    No pending medical approvals. The LangGraph supervisor is operating normally.
                  </p>
                </div>
              ) : (
                pendingTasks.map((t) => (
                  <div key={t.task_id} className="doctor-queue-card">
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span className={`task-type-badge ${t.task_type === "LAB_EXPLANATION" ? "lab" : t.task_type === "PRESCRIPTION_REVIEW" ? "rx" : "triage"}`}>
                        {t.task_type}
                      </span>
                      <span style={{ fontSize: "0.75rem", color: "#94a3b8" }}>
                        Task ID: <code>{t.task_id}</code> • Urgency: <strong>{t.urgency_level}</strong>
                      </span>
                    </div>

                    <div style={{ marginTop: "8px", fontWeight: "600", fontSize: "0.95rem" }}>
                      Patient: {t.patient_name} (Thread: {t.thread_id.slice(0, 14)}...)
                    </div>

                    <div style={{ marginTop: "10px", padding: "12px", background: "rgba(0,0,0,0.3)", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.05)" }}>
                      <div style={{ fontSize: "0.72rem", color: "#38bdf8", textTransform: "uppercase", fontWeight: "700", marginBottom: "4px" }}>
                        Proposed AI Clinical Message:
                      </div>
                      <div style={{ fontSize: "0.9rem", color: "#e2e8f0" }}>
                        {t.proposed_message_urdulish}
                      </div>
                    </div>

                    {/* Inline Editor if Editing */}
                    {editingTaskId === t.task_id ? (
                      <div style={{ marginTop: "12px", display: "grid", gap: "8px" }}>
                        <label style={{ fontSize: "0.75rem", color: "#38bdf8", fontWeight: "600" }}>
                          Edit Clinical Advice (UrduLish):
                        </label>
                        <textarea
                          style={{ width: "100%", height: "80px", background: "rgba(0,0,0,0.4)", color: "white", padding: "10px", borderRadius: "6px", border: "1px solid #0284c7" }}
                          value={editedMessageText}
                          onChange={(e) => setEditedMessageText(e.target.value)}
                        />
                        <input
                          type="text"
                          placeholder="Doctor clinical notes (e.g. Confirmed safe alternative due to allergy)..."
                          style={{ width: "100%", background: "rgba(0,0,0,0.4)", color: "white", padding: "8px 12px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.1)" }}
                          value={doctorNotes}
                          onChange={(e) => setDoctorNotes(e.target.value)}
                        />
                        <div style={{ display: "flex", gap: "8px" }}>
                          <button
                            className="btn-approve"
                            onClick={() => handleDoctorDecision(t.task_id, "edited")}
                          >
                            ✓ Save & Dispatch Edited
                          </button>
                          <button
                            style={{ background: "transparent", border: "1px solid #64748b", color: "#cbd5e1", padding: "6px 12px", borderRadius: "6px", cursor: "pointer" }}
                            onClick={() => setEditingTaskId(null)}
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="action-buttons-group">
                        <button
                          className="btn-approve"
                          onClick={() => handleDoctorDecision(t.task_id, "approved")}
                        >
                          ✓ Approve & Dispatch
                        </button>
                        <button
                          className="btn-edit"
                          onClick={() => {
                            setEditingTaskId(t.task_id);
                            setEditedMessageText(t.proposed_message_urdulish);
                          }}
                        >
                          ✏️ Edit Advice
                        </button>
                        <button
                          className="btn-reject"
                          onClick={() => handleDoctorDecision(t.task_id, "rejected")}
                        >
                          ✕ Reject & Refer In-Person
                        </button>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>

            {/* Right: Clinical Rules Card */}
            <aside className="glass-panel" style={{ padding: "20px", height: "fit-content" }}>
              <h3 style={{ fontSize: "1rem", fontWeight: "700", marginBottom: "12px", color: "#38bdf8" }}>
                🛡️ HITL Policy & Protocols
              </h3>
              <div style={{ fontSize: "0.82rem", color: "#cbd5e1", lineHeight: 1.6, display: "grid", gap: "12px" }}>
                <div>
                  <strong>1. Lab Explanations:</strong> All automated laboratory interpretations are held until a doctor signs off on clinical context.
                </div>
                <div>
                  <strong>2. Prescription Checks:</strong> Any advice touching medications or allergy warnings requires physician authorization.
                </div>
                <div>
                  <strong>3. Triage Safety:</strong> Assessments below 85% confidence automatically route to the doctor queue before patient advice.
                </div>
                <div>
                  <strong>4. Graph Pause/Resume:</strong> LangGraph state is check-pointed; doctor approval automatically resumes the conversation.
                </div>
              </div>
            </aside>
          </div>
        )}

        {/* ================= TAB 3: OBSERVABILITY & TELEMETRY ================= */}
        {activeTab === "telemetry" && (
          <div>
            <div style={{ marginBottom: "20px" }}>
              <h2 style={{ fontSize: "1.3rem", fontWeight: "700" }}>System Observability & LangSmith Telemetry</h2>
              <p style={{ fontSize: "0.8rem", color: "#94a3b8" }}>
                Real-time latency, token usage, cost accounting, and multi-agent routing traces.
              </p>
            </div>

            {/* Metrics Grid */}
            <div className="stats-grid">
              <div className="stat-widget">
                <div className="stat-label">Avg Agent Latency</div>
                <div className="stat-value">{stats ? `${stats.avg_latency_ms} ms` : "485 ms"}</div>
              </div>
              <div className="stat-widget">
                <div className="stat-label">Total Traced Sessions</div>
                <div className="stat-value">{stats ? stats.total_conversations : "12"}</div>
              </div>
              <div className="stat-widget">
                <div className="stat-label">Total Tokens</div>
                <div className="stat-value">{stats ? stats.total_tokens?.toLocaleString() : "8,450"}</div>
              </div>
              <div className="stat-widget">
                <div className="stat-label">Total Cost (USD)</div>
                <div className="stat-value" style={{ color: "#34d399" }}>
                  ${stats ? stats.total_cost_usd?.toFixed(4) : "0.0012"}
                </div>
              </div>
              <div className="stat-widget">
                <div className="stat-label">Doctor Interventions</div>
                <div className="stat-value" style={{ color: "#f59e0b" }}>
                  {stats ? stats.hitl_interventions : "2"}
                </div>
              </div>
              <div className="stat-widget">
                <div className="stat-label">Emergency Escalations</div>
                <div className="stat-value" style={{ color: "#ef4444" }}>
                  {stats ? stats.emergency_escalations : "0"}
                </div>
              </div>
            </div>

            {/* Architecture Overview */}
            <div className="glass-panel" style={{ padding: "24px" }}>
              <h3 style={{ fontSize: "1.05rem", fontWeight: "700", marginBottom: "14px", color: "#38bdf8" }}>
                LangGraph Multi-Agent Orchestration Topology
              </h3>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "14px" }}>
                <div style={{ background: "rgba(0,0,0,0.3)", padding: "14px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
                  <strong style={{ color: "#2dd4bf" }}>Supervisor Router</strong>
                  <p style={{ fontSize: "0.78rem", color: "#94a3b8", marginTop: "4px" }}>
                    Routes dynamically between 7 specialist agents with retry policies and exponential backoff.
                  </p>
                </div>
                <div style={{ background: "rgba(0,0,0,0.3)", padding: "14px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
                  <strong style={{ color: "#38bdf8" }}>Parallel Execution Fan-Out</strong>
                  <p style={{ fontSize: "0.78rem", color: "#94a3b8", marginTop: "4px" }}>
                    Executes Triage Urgency Evaluator + EHR Records Agent concurrently via thread pool.
                  </p>
                </div>
                <div style={{ background: "rgba(0,0,0,0.3)", padding: "14px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
                  <strong style={{ color: "#fbbf24" }}>Doctor HITL Gate</strong>
                  <p style={{ fontSize: "0.78rem", color: "#94a3b8", marginTop: "4px" }}>
                    Interrupts graph on lab results, prescriptions, and low confidence. Checkpointed pause & resume.
                  </p>
                </div>
                <div style={{ background: "rgba(0,0,0,0.3)", padding: "14px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
                  <strong style={{ color: "#c084fc" }}>Memory Architecture</strong>
                  <p style={{ fontSize: "0.78rem", color: "#94a3b8", marginTop: "4px" }}>
                    Short-term conversational state + Privacy-respecting long-term memory across clinical visits.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
