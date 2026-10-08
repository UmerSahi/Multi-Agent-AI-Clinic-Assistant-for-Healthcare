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

interface DoctorAccount {
  id: string;
  email: string;
  password?: string;
  name: string;
  specialty: string;
  branch: string;
  role: string;
  pmdc_number: string;
}

interface PatientFullHistory {
  patient_id: string;
  patient_name: string;
  mrn: string;
  phone: string;
  age: number;
  gender: string;
  preferred_doctor: string;
  preferred_branch: string;
  preferred_language: string;
  known_allergies: string[];
  chronic_conditions: string[];
  past_complaints: string[];
  last_visit_date: string;
  encounters: any[];
  observations: any[];
  medications: any[];
  soap_note: any;
}

export default function Home() {
  const [activeTab, setActiveTab] = useState<"patient" | "doctor" | "telemetry">("patient");
  const [language, setLanguage] = useState<"Urdu" | "English">("Urdu");

  // Patients
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [sessionId, setSessionId] = useState<string>("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [triageResult, setTriageResult] = useState<any>(null);

  // Doctor Auth & Portal
  const [doctorUser, setDoctorUser] = useState<DoctorAccount | null>(null);
  const [showDoctorLoginModal, setShowDoctorLoginModal] = useState<boolean>(false);
  const [doctorAccounts, setDoctorAccounts] = useState<DoctorAccount[]>([]);
  const [loginEmail, setLoginEmail] = useState<string>("");
  const [loginPassword, setLoginPassword] = useState<string>("");
  const [loginError, setLoginError] = useState<string>("");
  const [doctorSubTab, setDoctorSubTab] = useState<"dossier" | "appointments" | "approvals">("dossier");
  const [doctorAppointments, setDoctorAppointments] = useState<any[]>([]);
  const [selectedHistoryMRN, setSelectedHistoryMRN] = useState<string>("");
  const [patientHistoryData, setPatientHistoryData] = useState<PatientFullHistory | null>(null);
  const [historyLoading, setHistoryLoading] = useState<boolean>(false);
  const [patientSearchQuery, setPatientSearchQuery] = useState<string>("");

  // Patient Sign Up Modal
  const [showSignupModal, setShowSignupModal] = useState<boolean>(false);
  const [signupForm, setSignupForm] = useState({
    name: "",
    phone: "",
    age: "32",
    gender: "Male",
    allergies: "None",
    conditions: "None",
    doctor: "Dr. Bilal Saeed",
    branch: "Gulberg Lahore",
    language: "English",
    complaint: ""
  });
  const [signupSubmitting, setSignupSubmitting] = useState<boolean>(false);

  // HITL & Telemetry
  const [pendingTasks, setPendingTasks] = useState<HITLTask[]>([]);
  const [stats, setStats] = useState<TelemetryStats | null>(null);
  const [editingTaskId, setEditingTaskId] = useState<string | null>(null);
  const [editedMessageText, setEditedMessageText] = useState<string>("");
  const [doctorNotes, setDoctorNotes] = useState<string>("");
  const [serverHealthy, setServerHealthy] = useState<boolean>(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Initial load
  useEffect(() => {
    const init = async () => {
      try {
        const hRes = await fetch(`/api/health`);
        if (hRes.ok) setServerHealthy(true);

        const pRes = await fetch(`/api/patients`);
        if (pRes.ok) {
          const data = await pRes.json();
          setPatients(data.patients || []);
          if (data.patients && data.patients.length > 0) {
            selectPatient(data.patients[0]);
          }
        }

        // Fetch Doctor Demo Credentials
        const dRes = await fetch(`/api/doctor/credentials`);
        if (dRes.ok) {
          const dData = await dRes.json();
          setDoctorAccounts(dData.accounts || []);
        }
      } catch (e) {
        console.log("Initialization fallback connecting...", e);
      }
      fetchPendingTasks();
      fetchTelemetry();
      fetchDoctorAppointments();
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
    setMessages([]); // Start clean: patient sends the first message!
  };

  const fetchPendingTasks = async () => {
    try {
      const res = await fetch(`/api/doctor/pending`);
      if (res.ok) {
        const data = await res.json();
        setPendingTasks(data.pending_tasks || []);
      }
    } catch {}
  };

  const fetchTelemetry = async () => {
    try {
      const res = await fetch(`/api/telemetry/stats`);
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch {}
  };

  const fetchDoctorAppointments = async () => {
    try {
      const res = await fetch(`/api/doctor/appointments`);
      if (res.ok) {
        const data = await res.json();
        setDoctorAppointments(data.appointments || []);
      }
    } catch {}
  };

  const fetchPatientHistory = async (identifier: string) => {
    if (!identifier) return;
    setHistoryLoading(true);
    try {
      const res = await fetch(`/api/patients/${encodeURIComponent(identifier)}/history`);
      if (res.ok) {
        const data = await res.json();
        setPatientHistoryData(data);
        setSelectedHistoryMRN(data.mrn || identifier);
      }
    } catch (e) {
      console.error("Failed to load patient history", e);
    } finally {
      setHistoryLoading(false);
    }
  };

  // Chat message sending
  const handleSendMessage = async (textToSend?: string, triggerType?: string) => {
    const text = textToSend || inputMessage;
    if (!text.trim() || isLoading) return;

    const activeSess = sessionId || `sess_${selectedPatient?.patient_id || "p1"}_${Date.now()}`;
    if (!sessionId) setSessionId(activeSess);

    const userMsg: Message = {
      role: "user",
      content: text,
      timestamp: new Date().toISOString()
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInputMessage("");
    setIsLoading(true);

    try {
      const res = await fetch(`/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: activeSess,
          message: text,
          patient_identifier: selectedPatient?.patient_id || selectedPatient?.patient_name || "Valued Patient",
          is_returning_patient: !!selectedPatient,
          language: language,
          trigger_type: triggerType
        })
      });

      if (res.ok) {
        const data = await res.json();
        if (data.triage_result) setTriageResult(data.triage_result);

        const newMsgs = data.messages.map((m: any) => ({
          role: m.role === "human" || m.role === "user" ? "user" : "assistant",
          content: m.content || "",
          agent: m.agent || (m.role === "user" ? undefined : (data.current_agent || "ClinicalAssistant")),
          timestamp: m.timestamp || new Date().toISOString(),
          is_pending_review: m.is_pending_review,
          is_approved_by_doctor: m.is_approved_by_doctor,
          is_emergency: m.is_emergency,
          appointment_card: m.appointment_card
        }));

        setMessages(newMsgs);
        fetchPendingTasks();
        fetchTelemetry();
        fetchDoctorAppointments();
      } else {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: language === "English"
              ? "We experienced a temporary connectivity error. Please try again."
              : "Server se rabta mein takheer hui. Baraye meharbani dobara koshish karein.",
            agent: "System",
            timestamp: new Date().toISOString()
          }
        ]);
      }
    } catch (e: any) {
      console.error("Chat fetch error:", e);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Network connection error (${e.message || "Network Error"}).`,
          agent: "System",
          timestamp: new Date().toISOString()
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Doctor Login
  const handleDoctorLogin = async (e?: React.FormEvent, directAccount?: DoctorAccount) => {
    if (e) e.preventDefault();
    setLoginError("");

    const email = directAccount ? directAccount.email : loginEmail;
    const password = directAccount ? (directAccount.password || "Doctor123!") : loginPassword;

    try {
      const res = await fetch(`/api/doctor/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });

      if (res.ok) {
        const data = await res.json();
        setDoctorUser(data.doctor);
        setShowDoctorLoginModal(false);
        setActiveTab("doctor");
        fetchDoctorAppointments();
        // Load first patient history automatically
        if (patients.length > 0) {
          fetchPatientHistory(patients[0].mrn || patients[0].patient_id);
        }
      } else {
        const err = await res.json();
        setLoginError(err.detail || "Invalid credentials.");
      }
    } catch (err) {
      setLoginError("Login service unreachable.");
    }
  };

  // Doctor Sign Off / HITL Decision
  const handleDoctorDecision = async (
    taskId: string,
    decision: "approved" | "edited" | "rejected"
  ) => {
    try {
      const res = await fetch(`/api/doctor/decision`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task_id: taskId,
          decision: decision,
          doctor_notes: doctorNotes || (doctorUser ? `Approved by ${doctorUser.name}` : "Verified by Attending Physician"),
          edited_message: decision === "edited" ? editedMessageText : undefined,
          doctor_name: doctorUser?.name || "Dr. Maryam Naveed (Medical Director)"
        })
      });

      if (res.ok) {
        const data = await res.json();
        setEditingTaskId(null);
        setDoctorNotes("");
        setEditedMessageText("");
        fetchPendingTasks();
        fetchTelemetry();

        if (data.resumed_reply) {
          setMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              content: `✅ **Doctor Decision Applied (${decision.toUpperCase()}):**\n\n${data.resumed_reply}`,
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

  // Patient Sign Up
  const handleSignupSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!signupForm.name.trim() || !signupForm.phone.trim()) return;

    setSignupSubmitting(true);
    try {
      const res = await fetch(`/api/patients/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patient_name: signupForm.name,
          phone: signupForm.phone,
          age: parseInt(signupForm.age) || 30,
          gender: signupForm.gender,
          known_allergies: signupForm.allergies.split(",").map((s) => s.trim()),
          chronic_conditions: signupForm.conditions.split(",").map((s) => s.trim()),
          preferred_doctor_name: signupForm.doctor,
          preferred_branch: signupForm.branch,
          preferred_language: signupForm.language,
          initial_complaint: signupForm.complaint || "General Outpatient Checkup"
        })
      });

      if (res.ok) {
        const data = await res.json();
        const newPatient: Patient = {
          patient_id: data.patient.patient_id,
          patient_name: data.patient.patient_name,
          phone: data.patient.phone,
          mrn: data.patient.mrn,
          preferred_doctor: data.patient.preferred_doctor_name,
          preferred_branch: data.patient.preferred_branch,
          known_allergies: data.patient.known_allergies || [],
          chronic_conditions: data.patient.chronic_conditions || [],
          last_visit_date: data.patient.last_visit_date
        };

        setPatients((prev) => [newPatient, ...prev]);
        selectPatient(newPatient);
        setShowSignupModal(false);
        setActiveTab("patient");
        // Reset form
        setSignupForm({
          name: "",
          phone: "",
          age: "32",
          gender: "Male",
          allergies: "None",
          conditions: "None",
          doctor: "Dr. Bilal Saeed",
          branch: "Gulberg Lahore",
          language: "English",
          complaint: ""
        });
      }
    } catch (e) {
      console.error("Signup failed", e);
    } finally {
      setSignupSubmitting(false);
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

        {/* Central Nav Tabs */}
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
            onClick={() => {
              if (doctorUser) {
                setActiveTab("doctor");
              } else {
                setShowDoctorLoginModal(true);
              }
            }}
          >
            🩺 Doctor Portal
            {doctorUser ? (
              <span style={{ fontSize: "0.7rem", background: "#10b981", color: "#fff", padding: "1px 6px", borderRadius: "10px", marginLeft: "6px" }}>
                Active
              </span>
            ) : pendingTasks.length > 0 ? (
              <span className="badge-counter">{pendingTasks.length}</span>
            ) : null}
          </button>
          <button
            id="tab-telemetry"
            className={`nav-tab-btn ${activeTab === "telemetry" ? "active" : ""}`}
            onClick={() => setActiveTab("telemetry")}
          >
            📊 Observability & Telemetry
          </button>
        </nav>

        {/* Right Header Controls: Language Switcher & Doctor Profile / Register */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          {/* Language Switcher */}
          <div style={{ display: "flex", background: "rgba(0,0,0,0.35)", borderRadius: "20px", padding: "3px", border: "1px solid rgba(255,255,255,0.1)" }}>
            <button
              style={{
                padding: "5px 12px",
                borderRadius: "16px",
                fontSize: "0.75rem",
                fontWeight: "600",
                border: "none",
                cursor: "pointer",
                background: language === "Urdu" ? "linear-gradient(135deg, #0284c7, #06b6d4)" : "transparent",
                color: language === "Urdu" ? "#fff" : "#94a3b8",
                transition: "all 0.2s"
              }}
              onClick={() => setLanguage("Urdu")}
            >
              🇵🇰 اردو (UrduLish)
            </button>
            <button
              style={{
                padding: "5px 12px",
                borderRadius: "16px",
                fontSize: "0.75rem",
                fontWeight: "600",
                border: "none",
                cursor: "pointer",
                background: language === "English" ? "linear-gradient(135deg, #0284c7, #06b6d4)" : "transparent",
                color: language === "English" ? "#fff" : "#94a3b8",
                transition: "all 0.2s"
              }}
              onClick={() => setLanguage("English")}
            >
              🇬🇧 English
            </button>
          </div>

          {/* Doctor Status / Login Button */}
          {doctorUser ? (
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <div style={{ fontSize: "0.78rem", background: "rgba(6,182,212,0.15)", border: "1px solid rgba(6,182,212,0.3)", padding: "4px 10px", borderRadius: "8px", color: "#38bdf8" }}>
                👨‍⚕️ <strong>{doctorUser.name}</strong>
              </div>
              <button
                style={{ background: "transparent", border: "1px solid rgba(255,255,255,0.2)", color: "#cbd5e1", borderRadius: "6px", padding: "4px 8px", fontSize: "0.75rem", cursor: "pointer" }}
                onClick={() => setDoctorUser(null)}
              >
                Sign Out
              </button>
            </div>
          ) : (
            <button
              style={{ padding: "6px 14px", borderRadius: "8px", background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.15)", color: "#f8fafc", fontSize: "0.78rem", cursor: "pointer", fontWeight: "600" }}
              onClick={() => setShowDoctorLoginModal(true)}
            >
              Doctor Sign In ➔
            </button>
          )}
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
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                <div className="sidebar-title" style={{ margin: 0 }}>👤 Patient Profiles</div>
                <button
                  style={{
                    padding: "4px 8px",
                    borderRadius: "6px",
                    background: "rgba(6, 182, 212, 0.2)",
                    border: "1px solid rgba(6, 182, 212, 0.4)",
                    color: "#38bdf8",
                    fontSize: "0.72rem",
                    fontWeight: "700",
                    cursor: "pointer"
                  }}
                  onClick={() => setShowSignupModal(true)}
                >
                  + Sign Up Patient
                </button>
              </div>

              {patients.map((p) => (
                <div
                  key={p.patient_id}
                  className={`patient-card ${selectedPatient?.patient_id === p.patient_id ? "active" : ""}`}
                  onClick={() => selectPatient(p)}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                    <span className="patient-name">{p.patient_name}</span>
                    <span className="patient-mrn">{p.mrn}</span>
                  </div>
                  <div className="patient-pref">
                    <div>👨‍⚕️ {p.preferred_doctor}</div>
                    <div>🏥 {p.preferred_branch}</div>
                    <div>📅 Last Visit: {p.last_visit_date}</div>
                  </div>
                  {p.known_allergies.length > 0 && (
                    <div style={{ marginTop: "6px", fontSize: "0.72rem", color: "#f43f5e" }}>
                      ⚠️ Allergy: {p.known_allergies.join(", ")}
                    </div>
                  )}
                </div>
              ))}

              {/* Memory Integrity Checklist */}
              <div style={{ marginTop: "16px", padding: "12px", background: "rgba(0,0,0,0.25)", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.05)" }}>
                <div style={{ fontSize: "0.75rem", fontWeight: "700", color: "#38bdf8", marginBottom: "6px", textTransform: "uppercase" }}>
                  Clinical Memory Engine
                </div>
                <div style={{ fontSize: "0.72rem", color: "#94a3b8", lineHeight: 1.6 }}>
                  <div>• Router: LangGraph Supervisor</div>
                  <div>• Memory: Short + Long-term Privacy</div>
                  <div>• Active Language: <strong>{language}</strong></div>
                  <div>• Model: `gemini-3.5-flash-lite`</div>
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
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span style={{ fontSize: "0.75rem", background: "rgba(255,255,255,0.06)", padding: "3px 8px", borderRadius: "12px", color: "#38bdf8" }}>
                    Language: {language}
                  </span>
                  {triageResult && (
                    <div className={`status-pill ${triageResult.urgency_tier?.toLowerCase()}`}>
                      Triage: {triageResult.urgency_tier} ({triageResult.confidence_score ? `${Math.round(triageResult.confidence_score * 100)}%` : "100%"})
                    </div>
                  )}
                </div>
              </div>

              {/* Messages Area */}
              <div className="chat-messages-scroll">
                {messages.length === 0 && (
                  <div style={{ margin: "auto", textAlign: "center", padding: "28px 16px", maxWidth: "480px" }}>
                    <div style={{ fontSize: "40px", marginBottom: "10px" }}>💬</div>
                    <h3 style={{ fontSize: "1.1rem", fontWeight: "700", color: "#f8fafc", marginBottom: "6px" }}>
                      {language === "English" ? "Start Chat with City Care Assistant" : "City Care Assistant ke sath Guftagu Shuru Karein"}
                    </h3>
                    <p style={{ fontSize: "0.82rem", color: "#94a3b8", lineHeight: 1.5, marginBottom: "18px" }}>
                      {selectedPatient
                        ? `${language === "English" ? "Consulting as" : "Mariz"}: ${selectedPatient.patient_name} (${selectedPatient.mrn}). ${language === "English" ? "Send your first message below:" : "Neechay apna pehla paigham bhejein:"}`
                        : "Type your query below or pick a suggestion to begin:"}
                    </p>
                    <div style={{ display: "grid", gap: "8px" }}>
                      <button
                        style={{ padding: "10px 16px", borderRadius: "8px", background: "rgba(6, 182, 212, 0.12)", border: "1px solid rgba(6, 182, 212, 0.3)", color: "#38bdf8", cursor: "pointer", fontSize: "0.85rem", textAlign: "left" }}
                        onClick={() => handleSendMessage(language === "English" ? "Hello, I need a general checkup" : "Assalam-o-Alaikum, mujhe checkup karwana hai")}
                      >
                        👋 {language === "English" ? '"Hello, I need a general checkup"' : '"Assalam-o-Alaikum, mujhe checkup karwana hai"'}
                      </button>
                      <button
                        style={{ padding: "10px 16px", borderRadius: "8px", background: "rgba(255, 255, 255, 0.05)", border: "1px solid rgba(255, 255, 255, 0.1)", color: "#cbd5e1", cursor: "pointer", fontSize: "0.85rem", textAlign: "left" }}
                        onClick={() => handleSendMessage(language === "English" ? "I want to book an appointment with Dr. Bilal" : "Dr. Bilal ke sath appointment chahiye")}
                      >
                        📅 {language === "English" ? '"I want to book an appointment with Dr. Bilal"' : '"Dr. Bilal ke sath appointment chahiye"'}
                      </button>
                      <button
                        style={{ padding: "10px 16px", borderRadius: "8px", background: "rgba(255, 255, 255, 0.05)", border: "1px solid rgba(255, 255, 255, 0.1)", color: "#cbd5e1", cursor: "pointer", fontSize: "0.85rem", textAlign: "left" }}
                        onClick={() => handleSendMessage(language === "English" ? "I have had a high fever for 2 days" : "Mujhe 2 din se tez bukhar hai")}
                      >
                        🩺 {language === "English" ? '"I have had a high fever for 2 days"' : '"Mujhe 2 din se tez bukhar hai"'}
                      </button>
                    </div>
                  </div>
                )}
                {messages.map((msg, idx) => (
                  <div key={idx} className={`message-row ${msg.role}`}>
                    <div className={`msg-avatar ${msg.role}`}>
                      {msg.role === "user" ? "P" : "AI"}
                    </div>
                    <div className="message-bubble">
                      {msg.agent && msg.role === "assistant" && (
                        <div className="msg-author-tag">{msg.agent}</div>
                      )}
                      <div style={{ whiteSpace: "pre-line" }}>{msg.content}</div>

                      {/* Pending Review Gate Banner */}
                      {msg.is_pending_review && (
                        <div className="pending-gate-banner">
                          <span>🛡️</span>
                          <div>
                            <strong>Doctor Verification Required:</strong> This clinical explanation is currently paused in the Doctor HITL Queue for safety sign-off.
                          </div>
                        </div>
                      )}

                      {/* Approved Badge */}
                      {msg.is_approved_by_doctor && (
                        <div style={{ marginTop: "6px", fontSize: "0.72rem", color: "#34d399", display: "flex", alignItems: "center", gap: "4px" }}>
                          <span>✓</span> Verified and authorized by Medical Director
                        </div>
                      )}

                      {/* Emergency Badge */}
                      {msg.is_emergency && (
                        <div style={{ marginTop: "10px", padding: "10px", background: "rgba(244, 63, 94, 0.15)", border: "1px solid #f43f5e", borderRadius: "8px" }}>
                          <strong style={{ color: "#fb7185", fontSize: "0.85rem" }}>
                            🚨 RESCUE 1122 EMERGENCY DIRECTIVE ACTIVE
                          </strong>
                          <div style={{ fontSize: "0.75rem", marginTop: "4px", color: "#cbd5e1" }}>
                            Do not wait for standard clinic hours. Head to the nearest Emergency Room.
                          </div>
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
                  <button className="quick-chip" onClick={() => handleSendMessage(language === "English" ? "Book an appointment with Dr. Bilal" : "Dr. Bilal ke sath appointment book kar dein")}>
                    📅 {language === "English" ? "Book Appointment" : "Appointment Book Karein"}
                  </button>
                  <button className="quick-chip" onClick={() => handleSendMessage(language === "English" ? "Explain my recent CBC blood report and elevated WBC" : "Meri CBC blood report aur WBC count ka kya matlab hai?", "lab_inquiry")}>
                    🔬 {language === "English" ? "Check Lab Report (HITL)" : "Lab Report Check (HITL)"}
                  </button>
                  <button className="quick-chip" onClick={() => handleSendMessage(language === "English" ? "Can you prescribe Augmentin 625mg for my infection?" : "Mujhe Augmentin dawa likh dein", "prescription_check")}>
                    💊 {language === "English" ? "Prescription Check (HITL)" : "Prescription Check (HITL)"}
                  </button>
                  <button className="quick-chip" onClick={() => handleSendMessage(language === "English" ? "Provide my post-consultation medication schedule" : "Dawai ka schedule aur follow-up plan batayein")}>
                    📋 {language === "English" ? "Care Plan" : "Care Plan"}
                  </button>
                  <button className="quick-chip" onClick={() => handleSendMessage(language === "English" ? "I have severe chest pain and breathlessness" : "Seene mein shadeed dard aur paseenay arahe hain")}>
                    🚨 Emergency Test
                  </button>
                </div>

                <div className="chat-input-row">
                  <input
                    id="chat-input"
                    type="text"
                    className="chat-input-field"
                    placeholder={language === "English" ? "Type your symptoms or question in English (or Urdu)..." : "Apna masla ya sawal UrduLish mein likhein (e.g. Bukhar kab se hai...)"}
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
                  />
                  <button id="send-button" className="send-btn" onClick={() => handleSendMessage()} disabled={isLoading}>
                    {language === "English" ? "Send ➔" : "Bhejein ➔"}
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
                <div>• MRN: {selectedPatient?.mrn}</div>
                <div>• Known Allergies: {selectedPatient?.known_allergies.join(", ") || "None"}</div>
                <div>• Chronic Conditions: {selectedPatient?.chronic_conditions.join(", ") || "None"}</div>

                <div style={{ color: "#10b981", fontWeight: "700", marginTop: "10px", marginBottom: "4px" }}>
                  2. Objective Continuity:
                </div>
                <div>• Last Clinic Visit: {selectedPatient?.last_visit_date}</div>
                <div>• Preferred Doctor: {selectedPatient?.preferred_doctor}</div>

                <div style={{ color: "#f59e0b", fontWeight: "700", marginTop: "10px", marginBottom: "4px" }}>
                  3. AI Urgency Stratification:
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

        {/* ================= TAB 2: DOCTOR CLINICAL PORTAL ================= */}
        {activeTab === "doctor" && (
          <div style={{ padding: "8px 0" }}>
            {/* Doctor Sub-Navigation */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
              <div>
                <h2 style={{ fontSize: "1.3rem", fontWeight: "700" }}>Doctor Clinical Command Center</h2>
                <p style={{ fontSize: "0.8rem", color: "#94a3b8" }}>
                  {doctorUser ? `Logged in as ${doctorUser.name} (${doctorUser.specialty}) • ${doctorUser.pmdc_number}` : "Access patient medical records, clinic appointments, and approval gates."}
                </p>
              </div>

              {/* Doctor Sub Tabs */}
              <div style={{ display: "flex", gap: "8px", background: "rgba(0,0,0,0.3)", padding: "4px", borderRadius: "10px" }}>
                <button
                  style={{
                    padding: "8px 16px",
                    borderRadius: "8px",
                    border: "none",
                    cursor: "pointer",
                    fontSize: "0.82rem",
                    fontWeight: "600",
                    background: doctorSubTab === "dossier" ? "rgba(6,182,212,0.25)" : "transparent",
                    color: doctorSubTab === "dossier" ? "#38bdf8" : "#94a3b8"
                  }}
                  onClick={() => setDoctorSubTab("dossier")}
                >
                  📋 Patient Medical Dossier
                </button>
                <button
                  style={{
                    padding: "8px 16px",
                    borderRadius: "8px",
                    border: "none",
                    cursor: "pointer",
                    fontSize: "0.82rem",
                    fontWeight: "600",
                    background: doctorSubTab === "appointments" ? "rgba(6,182,212,0.25)" : "transparent",
                    color: doctorSubTab === "appointments" ? "#38bdf8" : "#94a3b8"
                  }}
                  onClick={() => {
                    setDoctorSubTab("appointments");
                    fetchDoctorAppointments();
                  }}
                >
                  📅 Clinic Appointments ({doctorAppointments.length})
                </button>
                <button
                  style={{
                    padding: "8px 16px",
                    borderRadius: "8px",
                    border: "none",
                    cursor: "pointer",
                    fontSize: "0.82rem",
                    fontWeight: "600",
                    background: doctorSubTab === "approvals" ? "rgba(6,182,212,0.25)" : "transparent",
                    color: doctorSubTab === "approvals" ? "#38bdf8" : "#94a3b8"
                  }}
                  onClick={() => setDoctorSubTab("approvals")}
                >
                  🛡️ Safety Gate Queue ({pendingTasks.length})
                </button>
              </div>
            </div>

            {/* Sub-Tab 1: Patient Medical Dossier & Full History Retrieval */}
            {doctorSubTab === "dossier" && (
              <div style={{ display: "grid", gridTemplateColumns: "320px 1fr", gap: "20px" }}>
                {/* Left: Patient Selector & Search */}
                <aside className="glass-panel" style={{ padding: "16px", height: "fit-content" }}>
                  <div style={{ fontSize: "0.85rem", fontWeight: "700", color: "#38bdf8", marginBottom: "10px" }}>
                    🔍 Search Patient Records
                  </div>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Search by name, MRN, phone..."
                    value={patientSearchQuery}
                    onChange={(e) => setPatientSearchQuery(e.target.value)}
                    style={{ marginBottom: "14px" }}
                  />

                  <div style={{ display: "grid", gap: "8px", maxHeight: "65vh", overflowY: "auto" }}>
                    {patients
                      .filter((p) => {
                        const q = patientSearchQuery.toLowerCase();
                        return (
                          p.patient_name.toLowerCase().includes(q) ||
                          p.mrn.toLowerCase().includes(q) ||
                          p.phone.includes(q)
                        );
                      })
                      .map((p) => (
                        <div
                          key={p.patient_id}
                          style={{
                            padding: "10px 12px",
                            borderRadius: "8px",
                            background: selectedHistoryMRN === p.mrn ? "rgba(6,182,212,0.18)" : "rgba(255,255,255,0.03)",
                            border: `1px solid ${selectedHistoryMRN === p.mrn ? "rgba(6,182,212,0.5)" : "rgba(255,255,255,0.06)"}`,
                            cursor: "pointer"
                          }}
                          onClick={() => fetchPatientHistory(p.mrn)}
                        >
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                            <strong style={{ fontSize: "0.88rem", color: "#f8fafc" }}>{p.patient_name}</strong>
                            <span style={{ fontSize: "0.72rem", color: "#38bdf8", fontFamily: "var(--font-mono)" }}>{p.mrn}</span>
                          </div>
                          <div style={{ fontSize: "0.75rem", color: "#94a3b8", marginTop: "4px" }}>
                            📞 {p.phone} • Last: {p.last_visit_date}
                          </div>
                        </div>
                      ))}
                  </div>
                </aside>

                {/* Right: Full Medical Dossier */}
                <section className="glass-panel" style={{ padding: "24px" }}>
                  {historyLoading ? (
                    <div style={{ padding: "60px", textAlign: "center", color: "#94a3b8" }}>
                      Retrieving comprehensive electronic health record from FHIR database...
                    </div>
                  ) : patientHistoryData ? (
                    <div>
                      {/* Patient Dossier Header */}
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", paddingBottom: "18px", borderBottom: "1px solid rgba(255,255,255,0.1)", marginBottom: "18px" }}>
                        <div>
                          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                            <h2 style={{ fontSize: "1.4rem", fontWeight: "800", color: "#f8fafc" }}>
                              {patientHistoryData.patient_name}
                            </h2>
                            <span style={{ padding: "3px 10px", background: "rgba(6,182,212,0.2)", color: "#38bdf8", borderRadius: "12px", fontSize: "0.78rem", fontWeight: "700" }}>
                              MRN: {patientHistoryData.mrn}
                            </span>
                          </div>
                          <div style={{ fontSize: "0.82rem", color: "#94a3b8", marginTop: "6px" }}>
                            Age: <strong>{patientHistoryData.age}</strong> • Gender: <strong>{patientHistoryData.gender}</strong> • Phone: <strong>{patientHistoryData.phone}</strong> • Branch: <strong>{patientHistoryData.preferred_branch}</strong>
                          </div>
                        </div>

                        <div style={{ textAlign: "right" }}>
                          <span style={{ fontSize: "0.75rem", color: "#94a3b8" }}>Attending Primary Doctor:</span>
                          <div style={{ color: "#38bdf8", fontWeight: "700", fontSize: "0.95rem" }}>
                            {patientHistoryData.preferred_doctor}
                          </div>
                        </div>
                      </div>

                      {/* Clinical Badges: Allergies & Chronic Conditions */}
                      <div style={{ display: "flex", gap: "12px", marginBottom: "18px" }}>
                        <div style={{ flex: 1, padding: "10px 14px", borderRadius: "8px", background: patientHistoryData.known_allergies.length > 0 ? "rgba(244,63,94,0.15)" : "rgba(16,185,129,0.15)", border: `1px solid ${patientHistoryData.known_allergies.length > 0 ? "rgba(244,63,94,0.3)" : "rgba(16,185,129,0.3)"}` }}>
                          <div style={{ fontSize: "0.72rem", textTransform: "uppercase", fontWeight: "700", color: patientHistoryData.known_allergies.length > 0 ? "#fb7185" : "#34d399" }}>
                            Known Drug Allergies
                          </div>
                          <div style={{ fontSize: "0.88rem", fontWeight: "600", marginTop: "4px" }}>
                            {patientHistoryData.known_allergies.length > 0 ? patientHistoryData.known_allergies.join(", ") : "None Reported"}
                          </div>
                        </div>

                        <div style={{ flex: 1, padding: "10px 14px", borderRadius: "8px", background: "rgba(245,158,11,0.15)", border: "1px solid rgba(245,158,11,0.3)" }}>
                          <div style={{ fontSize: "0.72rem", textTransform: "uppercase", fontWeight: "700", color: "#fbbf24" }}>
                            Chronic Medical Conditions
                          </div>
                          <div style={{ fontSize: "0.88rem", fontWeight: "600", marginTop: "4px" }}>
                            {patientHistoryData.chronic_conditions.length > 0 ? patientHistoryData.chronic_conditions.join(", ") : "None Reported"}
                          </div>
                        </div>
                      </div>

                      {/* Dossier Section: Past Complaints & Visits Timeline */}
                      <div className="dossier-section">
                        <div className="dossier-section-title">
                          📅 Past Visit Complaints & Timeline
                        </div>
                        {patientHistoryData.past_complaints && patientHistoryData.past_complaints.length > 0 ? (
                          <div style={{ display: "grid", gap: "8px" }}>
                            {patientHistoryData.past_complaints.map((c, i) => (
                              <div key={i} className="history-timeline-item">
                                <div style={{ fontSize: "0.88rem", color: "#f8fafc", fontWeight: "500" }}>{c}</div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div style={{ fontSize: "0.82rem", color: "#94a3b8" }}>No past recorded complaints.</div>
                        )}
                      </div>

                      {/* Dossier Section: Electronic Health Record Encounters */}
                      {patientHistoryData.encounters && patientHistoryData.encounters.length > 0 && (
                        <div className="dossier-section">
                          <div className="dossier-section-title">
                            🏥 Previous Clinical Encounters (EHR)
                          </div>
                          {patientHistoryData.encounters.map((enc, idx) => (
                            <div key={idx} style={{ padding: "12px", background: "rgba(255,255,255,0.02)", borderRadius: "8px", marginBottom: "8px", border: "1px solid rgba(255,255,255,0.05)" }}>
                              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                                <strong style={{ color: "#38bdf8", fontSize: "0.85rem" }}>
                                  {enc.doctor_name || "Consultant"} ({enc.doctor_specialty || "General Medicine"})
                                </strong>
                                <span style={{ fontSize: "0.75rem", color: "#94a3b8" }}>
                                  Date: {enc.encounter_date ? enc.encounter_date.slice(0, 10) : "2026-09-06"} • Ref: {enc.encounter_reference || "ENC-2026-1000"}
                                </span>
                              </div>
                              <div style={{ fontSize: "0.82rem", color: "#e2e8f0", marginBottom: "6px" }}>
                                <strong>Chief Complaint:</strong> {enc.chief_complaint}
                              </div>
                              {enc.soap_assessment && (
                                <div style={{ fontSize: "0.8rem", color: "#cbd5e1" }}>
                                  <strong>Assessment:</strong> {enc.soap_assessment}
                                </div>
                              )}
                              {enc.soap_plan && (
                                <div style={{ fontSize: "0.8rem", color: "#94a3b8", marginTop: "4px" }}>
                                  <strong>Plan:</strong> {enc.soap_plan}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Dossier Section: Laboratory Observations */}
                      {patientHistoryData.observations && patientHistoryData.observations.length > 0 && (
                        <div className="dossier-section">
                          <div className="dossier-section-title">
                            🔬 Laboratory Blood & Diagnostic Results
                          </div>
                          <div style={{ borderRadius: "8px", overflow: "hidden", border: "1px solid rgba(255,255,255,0.08)" }}>
                            <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr", padding: "8px 12px", background: "rgba(0,0,0,0.5)", fontSize: "0.72rem", color: "#94a3b8", fontWeight: "700" }}>
                              <div>TEST NAME</div>
                              <div>VALUE</div>
                              <div>REFERENCE RANGE</div>
                              <div>STATUS</div>
                            </div>
                            {patientHistoryData.observations.map((obs, idx) => (
                              <div key={idx} className="lab-result-row">
                                <div style={{ fontWeight: "600", color: "#f8fafc" }}>{obs.test_name}</div>
                                <div style={{ color: "#38bdf8", fontFamily: "var(--font-mono)" }}>
                                  {obs.numeric_value} {obs.unit}
                                </div>
                                <div style={{ color: "#94a3b8" }}>
                                  {obs.reference_range_low} - {obs.reference_range_high} {obs.unit}
                                </div>
                                <div>
                                  <span className={`flag-badge ${obs.flag?.toLowerCase() || "normal"}`}>
                                    {obs.flag || "NORMAL"}
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Dossier Section: Pre-Visit SOAP Brief */}
                      {patientHistoryData.soap_note && (
                        <div className="dossier-section">
                          <div className="dossier-section-title">
                            📋 Pre-Visit SOAP Brief (Clinical Summary Agent)
                          </div>
                          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", fontSize: "0.82rem" }}>
                            <div style={{ padding: "10px", background: "rgba(0,0,0,0.3)", borderRadius: "6px" }}>
                              <strong style={{ color: "#38bdf8" }}>Subjective (Fact):</strong>
                              <div style={{ marginTop: "4px", color: "#cbd5e1" }}>
                                {patientHistoryData.soap_note.subjective_facts || "Patient follow-up and clinical checkup."}
                              </div>
                            </div>
                            <div style={{ padding: "10px", background: "rgba(0,0,0,0.3)", borderRadius: "6px" }}>
                              <strong style={{ color: "#10b981" }}>Assessment & Plan:</strong>
                              <div style={{ marginTop: "4px", color: "#cbd5e1" }}>
                                {patientHistoryData.soap_note.assessment_hypotheses || "Routine outpatient follow-up recommended."}
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div style={{ padding: "60px", textAlign: "center", color: "#94a3b8" }}>
                      Select a patient from the left directory to inspect their complete medical record dossier.
                    </div>
                  )}
                </section>
              </div>
            )}

            {/* Sub-Tab 2: Clinic Appointments Table */}
            {doctorSubTab === "appointments" && (
              <div className="glass-panel" style={{ padding: "20px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                  <h3 style={{ fontSize: "1.1rem", fontWeight: "700" }}>Scheduled Patient Appointments</h3>
                  <button
                    style={{ padding: "6px 12px", borderRadius: "6px", background: "rgba(6,182,212,0.2)", border: "1px solid rgba(6,182,212,0.4)", color: "#38bdf8", cursor: "pointer", fontSize: "0.78rem" }}
                    onClick={fetchDoctorAppointments}
                  >
                    🔄 Refresh Schedule
                  </button>
                </div>

                <div className="appointment-table-wrap">
                  <table className="appointment-table">
                    <thead>
                      <tr>
                        <th>Booking Ref</th>
                        <th>Patient Name & MRN</th>
                        <th>Doctor / Specialty</th>
                        <th>Scheduled Date & Time</th>
                        <th>Branch</th>
                        <th>Urgency</th>
                        <th>Status</th>
                        <th>Reason for Visit</th>
                      </tr>
                    </thead>
                    <tbody>
                      {doctorAppointments.length === 0 ? (
                        <tr>
                          <td colSpan={8} style={{ textAlign: "center", padding: "30px", color: "#94a3b8" }}>
                            No appointments found in the system.
                          </td>
                        </tr>
                      ) : (
                        doctorAppointments.slice(0, 25).map((app, idx) => (
                          <tr key={idx}>
                            <td>
                              <code style={{ color: "#38bdf8", fontWeight: "700" }}>
                                #{app.booking_reference || `BK-${idx + 1000}`}
                              </code>
                            </td>
                            <td>
                              <strong>{app.patient_name || "Valued Patient"}</strong>
                              <div style={{ fontSize: "0.72rem", color: "#94a3b8" }}>{app.patient_mrn || app.patient_id}</div>
                            </td>
                            <td>
                              <div>{app.doctor_name || "Dr. Bilal Saeed"}</div>
                              <div style={{ fontSize: "0.72rem", color: "#94a3b8" }}>{app.specialty || app.doctor_specialty || "General Medicine"}</div>
                            </td>
                            <td>
                              {app.scheduled_start ? app.scheduled_start.replace("T", " ").slice(0, 16) : "2026-10-09 10:20"}
                            </td>
                            <td>{app.branch_name || "Gulberg Lahore"}</td>
                            <td>
                              <span className={`status-pill ${app.urgency_tier?.toLowerCase() || "routine"}`}>
                                {app.urgency_tier || "ROUTINE"}
                              </span>
                            </td>
                            <td>
                              <span style={{ color: app.status === "booked" ? "#34d399" : "#94a3b8", textTransform: "capitalize" }}>
                                {app.status || "booked"}
                              </span>
                            </td>
                            <td>{app.reason_for_visit || "Clinical Consultation"}</td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Sub-Tab 3: Safety Approvals Queue (HITL) */}
            {doctorSubTab === "approvals" && (
              <div className="doctor-dashboard">
                <div>
                  <h3 style={{ fontSize: "1.1rem", fontWeight: "700", marginBottom: "16px" }}>
                    Physician Sign-Off & Review Queue
                  </h3>

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

                        {editingTaskId === t.task_id ? (
                          <div style={{ marginTop: "12px", display: "grid", gap: "8px" }}>
                            <label style={{ fontSize: "0.75rem", color: "#38bdf8", fontWeight: "600" }}>
                              Edit Clinical Advice:
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
                <div className="stat-label">Total Conversations</div>
                <div className="stat-value">{stats?.total_conversations || 1}</div>
              </div>
              <div className="stat-widget">
                <div className="stat-label">Total Tokens Processed</div>
                <div className="stat-value">{stats ? stats.total_tokens.toLocaleString() : "2,450"}</div>
              </div>
              <div className="stat-widget">
                <div className="stat-label">Estimated LLM Cost (USD)</div>
                <div className="stat-value">${stats ? stats.total_cost_usd.toFixed(4) : "0.0004"}</div>
              </div>
              <div className="stat-widget">
                <div className="stat-label">Doctor HITL Interventions</div>
                <div className="stat-value" style={{ color: "#34d399" }}>
                  {stats?.hitl_interventions || 0}
                </div>
              </div>
            </div>

            {/* Multi-Agent Architecture Graph Diagram */}
            <div className="glass-panel" style={{ padding: "20px", marginTop: "20px" }}>
              <h3 style={{ fontSize: "1rem", fontWeight: "700", marginBottom: "8px", color: "#38bdf8" }}>
                Multi-Agent StateGraph Architecture
              </h3>
              <p style={{ fontSize: "0.82rem", color: "#94a3b8", marginBottom: "16px" }}>
                LangGraph conditional orchestration with parallel fan-out (Triage + Records) and checkpointer memory.
              </p>
              <div style={{ background: "rgba(0,0,0,0.4)", padding: "16px", borderRadius: "8px", fontFamily: "var(--font-mono)", fontSize: "0.78rem", color: "#cbd5e1", overflowX: "auto", lineHeight: 1.6 }}>
                <code>
                  [START] ➔ supervisor (Router)<br/>
                  &nbsp;&nbsp;├── [first_msg & returning] ➔ returning_greeting ➔ [END]<br/>
                  &nbsp;&nbsp;├── [intake_active] ➔ intake ➔ [END]<br/>
                  &nbsp;&nbsp;├── [intake_done] ➔ parallel_triage_records (Triage + Records Concurrently)<br/>
                  &nbsp;&nbsp;├── [routine_care] ➔ scheduling ➔ [END]<br/>
                  &nbsp;&nbsp;├── [rx_check] ➔ prescription_safety ➔ hitl_gate (Doctor Approval Gate)<br/>
                  &nbsp;&nbsp;├── [emergency_flag] ➔ emergency_escalation (1122 Notice) ➔ [END]<br/>
                  &nbsp;&nbsp;└── [followup] ➔ followup (Outreach Reminders) ➔ [END]
                </code>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* ================= MODAL 1: PATIENT SIGN UP ================= */}
      {showSignupModal && (
        <div className="modal-backdrop" onClick={() => setShowSignupModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <h2 style={{ fontSize: "1.25rem", fontWeight: "700", color: "#f8fafc" }}>
                👤 New Patient Registration
              </h2>
              <button
                style={{ background: "transparent", border: "none", color: "#94a3b8", fontSize: "1.2rem", cursor: "pointer" }}
                onClick={() => setShowSignupModal(false)}
              >
                ✕
              </button>
            </div>
            <p style={{ fontSize: "0.8rem", color: "#94a3b8", marginBottom: "18px" }}>
              Register a new patient to generate their Medical Record Number (MRN) and start a personalized clinical session.
            </p>

            <form onSubmit={handleSignupSubmit}>
              <div className="form-grid-2">
                <div className="form-group">
                  <label className="form-label">Full Name *</label>
                  <input
                    type="text"
                    required
                    className="form-input"
                    placeholder="e.g. Zainab Bibi"
                    value={signupForm.name}
                    onChange={(e) => setSignupForm({ ...signupForm, name: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Phone Number *</label>
                  <input
                    type="text"
                    required
                    className="form-input"
                    placeholder="e.g. +923451122334"
                    value={signupForm.phone}
                    onChange={(e) => setSignupForm({ ...signupForm, phone: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-grid-2">
                <div className="form-group">
                  <label className="form-label">Age</label>
                  <input
                    type="number"
                    className="form-input"
                    value={signupForm.age}
                    onChange={(e) => setSignupForm({ ...signupForm, age: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Gender</label>
                  <select
                    className="form-select"
                    value={signupForm.gender}
                    onChange={(e) => setSignupForm({ ...signupForm, gender: e.target.value })}
                  >
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
              </div>

              <div className="form-grid-2">
                <div className="form-group">
                  <label className="form-label">Known Allergies</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. Penicillin, Sulfa, None"
                    value={signupForm.allergies}
                    onChange={(e) => setSignupForm({ ...signupForm, allergies: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Chronic Illnesses</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. Hypertension, Diabetes, Asthma"
                    value={signupForm.conditions}
                    onChange={(e) => setSignupForm({ ...signupForm, conditions: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-grid-2">
                <div className="form-group">
                  <label className="form-label">Preferred Doctor</label>
                  <select
                    className="form-select"
                    value={signupForm.doctor}
                    onChange={(e) => setSignupForm({ ...signupForm, doctor: e.target.value })}
                  >
                    <option value="Dr. Bilal Saeed">Dr. Bilal Saeed (General Medicine)</option>
                    <option value="Dr. Ayesha Tariq">Dr. Ayesha Tariq (Gynaecology)</option>
                    <option value="Dr. Usman Sheikh">Dr. Usman Sheikh (Paediatrics)</option>
                    <option value="Dr. Maryam Naveed">Dr. Maryam Naveed (Medical Director)</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Preferred Branch</label>
                  <select
                    className="form-select"
                    value={signupForm.branch}
                    onChange={(e) => setSignupForm({ ...signupForm, branch: e.target.value })}
                  >
                    <option value="Gulberg Lahore">Gulberg Lahore</option>
                    <option value="DHA Lahore">DHA Lahore</option>
                    <option value="F-8 Markaz Islamabad">F-8 Markaz Islamabad</option>
                    <option value="Johar Town Lahore">Johar Town Lahore</option>
                  </select>
                </div>
              </div>

              <div className="form-grid-2">
                <div className="form-group">
                  <label className="form-label">Preferred Language</label>
                  <select
                    className="form-select"
                    value={signupForm.language}
                    onChange={(e) => setSignupForm({ ...signupForm, language: e.target.value })}
                  >
                    <option value="English">English</option>
                    <option value="Urdu">Urdu (UrduLish)</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Initial Medical Concern</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. Fever, routine follow-up"
                    value={signupForm.complaint}
                    onChange={(e) => setSignupForm({ ...signupForm, complaint: e.target.value })}
                  />
                </div>
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "18px" }}>
                <button
                  type="button"
                  style={{ background: "transparent", border: "1px solid rgba(255,255,255,0.15)", color: "#cbd5e1", padding: "10px 16px", borderRadius: "8px", cursor: "pointer" }}
                  onClick={() => setShowSignupModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={signupSubmitting}
                  style={{ background: "linear-gradient(135deg, #0284c7, #06b6d4)", border: "none", color: "white", padding: "10px 20px", borderRadius: "8px", cursor: "pointer", fontWeight: "700" }}
                >
                  {signupSubmitting ? "Registering..." : "Register & Start Chat ➔"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ================= MODAL 2: DOCTOR LOGIN ================= */}
      {showDoctorLoginModal && (
        <div className="modal-backdrop" onClick={() => setShowDoctorLoginModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
              <h2 style={{ fontSize: "1.25rem", fontWeight: "700", color: "#f8fafc" }}>
                🩺 Doctor Clinical Sign In
              </h2>
              <button
                style={{ background: "transparent", border: "none", color: "#94a3b8", fontSize: "1.2rem", cursor: "pointer" }}
                onClick={() => setShowDoctorLoginModal(false)}
              >
                ✕
              </button>
            </div>
            <p style={{ fontSize: "0.8rem", color: "#94a3b8", marginBottom: "16px" }}>
              Sign in as an attending physician to inspect patient histories, check appointments, and sign off on HITL medical advice.
            </p>

            {/* Quick 1-Click Login Cards */}
            <div style={{ marginBottom: "20px" }}>
              <div style={{ fontSize: "0.72rem", color: "#38bdf8", textTransform: "uppercase", fontWeight: "700", marginBottom: "8px" }}>
                ⚡ Quick 1-Click Doctor Logins (Predefined Staff Credentials):
              </div>
              <div style={{ display: "grid", gap: "8px" }}>
                {doctorAccounts.map((doc) => (
                  <div key={doc.id} className="doctor-cred-card">
                    <div>
                      <strong style={{ fontSize: "0.88rem", color: "#f8fafc" }}>{doc.name}</strong>
                      <div style={{ fontSize: "0.74rem", color: "#94a3b8" }}>
                        {doc.specialty} • {doc.branch} • <code>{doc.email}</code>
                      </div>
                    </div>
                    <button
                      style={{
                        padding: "6px 14px",
                        borderRadius: "6px",
                        background: "rgba(6, 182, 212, 0.2)",
                        border: "1px solid rgba(6, 182, 212, 0.4)",
                        color: "#38bdf8",
                        cursor: "pointer",
                        fontWeight: "700",
                        fontSize: "0.78rem"
                      }}
                      onClick={() => handleDoctorLogin(undefined, doc)}
                    >
                      Sign In ➔
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Manual Form */}
            <form onSubmit={handleDoctorLogin} style={{ borderTop: "1px solid rgba(255,255,255,0.08)", paddingTop: "16px" }}>
              <div style={{ fontSize: "0.72rem", color: "#94a3b8", textTransform: "uppercase", fontWeight: "700", marginBottom: "10px" }}>
                Or Sign In Manually:
              </div>

              {loginError && (
                <div style={{ padding: "8px 12px", background: "rgba(244,63,94,0.15)", border: "1px solid #f43f5e", borderRadius: "6px", color: "#fb7185", fontSize: "0.78rem", marginBottom: "12px" }}>
                  {loginError}
                </div>
              )}

              <div className="form-group">
                <label className="form-label">Doctor Email</label>
                <input
                  type="email"
                  className="form-input"
                  placeholder="e.g. dr.bilal@citycare.com"
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Password</label>
                <input
                  type="password"
                  className="form-input"
                  placeholder="Doctor123!"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                />
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "14px" }}>
                <button
                  type="button"
                  style={{ background: "transparent", border: "1px solid rgba(255,255,255,0.15)", color: "#cbd5e1", padding: "8px 14px", borderRadius: "8px", cursor: "pointer" }}
                  onClick={() => setShowDoctorLoginModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  style={{ background: "linear-gradient(135deg, #0284c7, #06b6d4)", border: "none", color: "white", padding: "8px 18px", borderRadius: "8px", cursor: "pointer", fontWeight: "700" }}
                >
                  Sign In ➔
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer style={{ padding: "14px 28px", borderTop: "1px solid var(--border-subtle)", background: "rgba(9, 13, 22, 0.9)", fontSize: "0.75rem", color: "#64748b", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>City Care Clinics — Multi-Agent AI Healthcare Assistant • Week 9 Day 4</div>
        <div>FastAPI Port 8000 (LangGraph + MemorySaver) • Next.js Port 3000</div>
      </footer>
    </div>
  );
}
