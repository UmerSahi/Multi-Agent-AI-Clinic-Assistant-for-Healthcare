"use client";

import React, { useState, useEffect } from "react";
import {
  ActiveTab,
  PatientSubTab,
  DoctorSubTab,
  Message,
  Patient,
  DoctorAccount,
  DoctorDirectoryItem,
  DoctorScheduleData,
  PatientFullHistory,
  HITLTask,
  TelemetryStats,
  LabSample,
  LabAnalysisResult,
} from "@/types";

// Modular Components
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { RightSidebar } from "@/components/layout/RightSidebar";

import { ChatView } from "@/components/patient/ChatView";
import { ScheduleView } from "@/components/patient/ScheduleView";
import { MyAppointmentsView } from "@/components/patient/MyAppointmentsView";

import { DoctorPortal } from "@/components/doctor/DoctorPortal";
import { LabVisionView } from "@/components/lab/LabVisionView";
import { TelemetryView } from "@/components/telemetry/TelemetryView";

// Modals
import { DoctorLoginModal } from "@/components/modals/DoctorLoginModal";
import { SignupModal } from "@/components/modals/SignupModal";
import { BookingSlotModal } from "@/components/modals/BookingSlotModal";
import { PrescribeModal } from "@/components/modals/PrescribeModal";
import { ViewRxModal } from "@/components/modals/ViewRxModal";

export default function ClinicApp() {
  // Navigation State
  const [activeTab, setActiveTab] = useState<ActiveTab>("patient");
  const [patientSubTab, setPatientSubTab] = useState<PatientSubTab>("chat");
  const [doctorSubTab, setDoctorSubTab] = useState<DoctorSubTab>("dossier");
  const [language, setLanguage] = useState<"Urdu" | "English">("Urdu");

  // Health Status
  const [serverHealthy, setServerHealthy] = useState<boolean>(false);

  // Patient Profile (NO password login barrier - identified by ID from database!)
  const [patientUser, setPatientUser] = useState<Patient | null>(null);

  // Authentication: Doctor Workstation Only
  const [doctorUser, setDoctorUser] = useState<DoctorAccount | null>(null);
  const [showDoctorLoginModal, setShowDoctorLoginModal] = useState<boolean>(false);
  const [loginEmail, setLoginEmail] = useState<string>("");
  const [loginPassword, setLoginPassword] = useState<string>("");
  const [loginError, setLoginError] = useState<string>("");

  // Patient Registration (Quick Add)
  const [showSignupModal, setShowSignupModal] = useState<boolean>(false);
  const [signupForm, setSignupForm] = useState({
    full_name: "",
    phone: "",
    age: "28",
    gender: "Male",
    email: "",
    password: "",
    address: "Lahore, Pakistan",
    blood_group: "B+",
  });
  const [signupSubmitting, setSignupSubmitting] = useState<boolean>(false);

  // Chat & Conversation State
  const [sessionId, setSessionId] = useState<string>(() => "session_" + Date.now());
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [restoreInputRef, setRestoreInputRef] = useState<string>("");
  const [restoreLoading, setRestoreLoading] = useState<boolean>(false);

  // Doctor Directory & Scheduling
  const [doctorsList, setDoctorsList] = useState<DoctorDirectoryItem[]>([]);
  const [selectedDoctorId, setSelectedDoctorId] = useState<string>("");
  const [selectedScheduleDate, setSelectedScheduleDate] = useState<string>(() => {
    const d = new Date();
    return d.toISOString().split("T")[0];
  });
  const [doctorSchedule, setDoctorSchedule] = useState<DoctorScheduleData | null>(null);
  const [scheduleLoading, setScheduleLoading] = useState<boolean>(false);
  const [selectedSpecialtyFilter, setSelectedSpecialtyFilter] = useState<string>("ALL");

  // Booking Modal
  const [bookingSlotModal, setBookingSlotModal] = useState<any | null>(null);
  const [bookingDoctor, setBookingDoctor] = useState<DoctorDirectoryItem | null>(null);
  const [bookingReason, setBookingReason] = useState<string>("Clinical Consultation");
  const [bookingSubmitting, setBookingSubmitting] = useState<boolean>(false);
  const [bookingSuccessResult, setBookingSuccessResult] = useState<any | null>(null);

  // Patient Appointments
  const [myAppointments, setMyAppointments] = useState<any[]>([]);
  const [myAppointmentsLoading, setMyAppointmentsLoading] = useState<boolean>(false);

  // Doctor Workstation: Dossier & Appointments
  const [patientSearchQuery, setPatientSearchQuery] = useState<string>("");
  const [patientHistoryData, setPatientHistoryData] = useState<PatientFullHistory | null>(null);
  const [historyLoading, setHistoryLoading] = useState<boolean>(false);
  const [doctorAppointments, setDoctorAppointments] = useState<any[]>([]);
  const [doctorAppointmentFilter, setDoctorAppointmentFilter] = useState<"my" | "all">("my");
  const [doctorAppointmentSearch, setDoctorAppointmentSearch] = useState<string>("");

  // Prescriptions Modals
  const [showPrescribeModal, setShowPrescribeModal] = useState<boolean>(false);
  const [prescribingApp, setPrescribingApp] = useState<any | null>(null);
  const [prescriptionForm, setPrescriptionForm] = useState<{
    diagnosis: string;
    advice: string;
    medicines: Array<{ medicine_name: string; dosage: string; frequency: string; duration: string; instructions: string }>;
  }>({
    diagnosis: "",
    advice: "Take medicines on time as prescribed. Keep well hydrated and take adequate rest. Contact clinic if symptoms worsen.",
    medicines: [
      { medicine_name: "Tab Panadol", dosage: "500mg", frequency: "1-0-1", duration: "5 days", instructions: "After meals" },
      { medicine_name: "Syp Hydryllin", dosage: "10ml", frequency: "1-1-1", duration: "5 days", instructions: "For cough relief" },
    ],
  });
  const [prescribeSubmitting, setPrescribeSubmitting] = useState<boolean>(false);
  const [prescribeModalError, setPrescribeModalError] = useState<string>("");
  const [prescribeModalSuccess, setPrescribeModalSuccess] = useState<boolean>(false);
  const [viewRxModalApp, setViewRxModalApp] = useState<any | null>(null);

  // HITL & Telemetry
  const [pendingTasks, setPendingTasks] = useState<HITLTask[]>([]);
  const [stats, setStats] = useState<TelemetryStats | null>(null);

  // Multimodal Lab Vision
  const [labSamples, setLabSamples] = useState<LabSample[]>([]);
  const [selectedSampleFile, setSelectedSampleFile] = useState<string>("");
  const [labResult, setLabResult] = useState<LabAnalysisResult | null>(null);
  const [labLoading, setLabLoading] = useState<boolean>(false);
  const [showRawJson, setShowRawJson] = useState<boolean>(false);

  // ================= DATA FETCHING =================
  const fetchDoctorsDirectory = async () => {
    try {
      const res = await fetch(`/api/doctors`);
      if (res.ok) {
        const data = await res.json();
        const docs = data.doctors || [];
        setDoctorsList(docs);
        if (docs.length > 0 && !selectedDoctorId) {
          setSelectedDoctorId(docs[0].id);
          fetchDoctorSchedule(docs[0].id, selectedScheduleDate);
        }
      }
    } catch (e) {
      console.warn("Could not fetch doctors directory:", e);
    }
  };

  const fetchDoctorSchedule = async (docId?: string, dateStr?: string) => {
    const targetDocId = docId || selectedDoctorId;
    const targetDate = dateStr || selectedScheduleDate;
    if (!targetDocId) return;

    setScheduleLoading(true);
    try {
      const res = await fetch(`/api/doctors/${targetDocId}/schedule?date=${targetDate}`);
      if (res.ok) {
        const data = await res.json();
        setDoctorSchedule(data);
      }
    } catch (e) {
      console.warn("Could not fetch doctor schedule:", e);
    } finally {
      setScheduleLoading(false);
    }
  };

  const fetchMyAppointments = async (identifier?: string) => {
    const targetId = identifier || patientUser?.mrn || patientUser?.patient_id;
    if (!targetId) {
      setMyAppointments([]);
      return;
    }
    setMyAppointmentsLoading(true);
    try {
      const res = await fetch(`/api/patients/${encodeURIComponent(targetId)}/appointments`);
      if (res.ok) {
        const data = await res.json();
        setMyAppointments(data.appointments || []);
      }
    } catch (e) {
      console.warn("Could not fetch patient appointments:", e);
    } finally {
      setMyAppointmentsLoading(false);
    }
  };

  const fetchDoctorAppointments = async () => {
    try {
      const res = await fetch(`/api/doctor/appointments`);
      if (res.ok) {
        const data = await res.json();
        setDoctorAppointments(data.appointments || []);
      }
    } catch (e) {
      console.warn("Could not fetch doctor appointments:", e);
    }
  };

  const fetchPatientHistory = async (identifier: string) => {
    if (!identifier.trim()) return;
    setHistoryLoading(true);
    try {
      const res = await fetch(`/api/patients/${encodeURIComponent(identifier.trim())}/history`);
      if (res.ok) {
        const data = await res.json();
        setPatientHistoryData(data);
      } else {
        alert("Patient record not found. Try searching with p1, p2, or MRN.");
      }
    } catch (e) {
      console.warn("Could not fetch patient history:", e);
    } finally {
      setHistoryLoading(false);
    }
  };

  // FETCH PATIENT RECORD FROM DATABASE BY ID (No login required!)
  const handleFetchPatientRecord = async (identifier: string) => {
    const cleanId = identifier.trim();
    if (!cleanId) return;

    try {
      // Query history or memory endpoint
      const res = await fetch(`/api/patients/${encodeURIComponent(cleanId)}/history`);
      if (res.ok) {
        const data = await res.json();
        const pRecord: Patient = {
          patient_id: data.patient_id || cleanId,
          patient_name: data.patient_name || "Valued Patient",
          mrn: data.mrn || cleanId,
          phone: data.phone || "",
          age: data.age || 30,
          gender: data.gender || "Unspecified",
          known_allergies: data.known_allergies || [],
          chronic_conditions: data.chronic_conditions || [],
        };
        setPatientUser(pRecord);
        fetchMyAppointments(pRecord.patient_id);

        // Add friendly confirmation bubble into chat
        const confirmMsg: Message = {
          id: "record_found_" + Date.now(),
          role: "assistant",
          agent: "MemoryManager",
          content: `✅ **Record Found!** Welcome back, **${pRecord.patient_name}**!\n\nI have retrieved your medical history from the database (Patient ID: \`${pRecord.patient_id}\`, MRN: \`${pRecord.mrn}\`).\n${pRecord.known_allergies?.length ? `• Known Allergies: **${pRecord.known_allergies.join(", ")}**\n` : ""}How can I assist you today?`,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        };
        setMessages((prev) => [...prev, confirmMsg]);
      } else {
        // Fallback: check /api/patients/{id}/memory
        const memRes = await fetch(`/api/patients/${encodeURIComponent(cleanId)}/memory`);
        if (memRes.ok) {
          const mem = await memRes.json();
          const pRecord: Patient = {
            patient_id: mem.patient_id || cleanId,
            patient_name: mem.patient_name || "Valued Patient",
            mrn: mem.mrn || cleanId,
            phone: mem.phone || "",
            age: mem.age || 30,
            gender: mem.gender || "Unspecified",
            known_allergies: mem.known_allergies || [],
            chronic_conditions: mem.chronic_conditions || [],
          };
          setPatientUser(pRecord);
          fetchMyAppointments(pRecord.patient_id);

          const confirmMsg: Message = {
            id: "record_found_" + Date.now(),
            role: "assistant",
            agent: "MemoryManager",
            content: `✅ **Record Found!** Welcome back, **${pRecord.patient_name}**!\n\nI have retrieved your profile from the clinic database (Patient ID: \`${pRecord.patient_id}\`). How can I assist you today?`,
            timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          };
          setMessages((prev) => [...prev, confirmMsg]);
        } else {
          alert(`No patient record found for ID: ${cleanId}. You can still chat freely as a guest patient!`);
        }
      }
    } catch (err) {
      console.error("Error fetching patient record:", err);
    }
  };

  const fetchLabSamples = async () => {
    try {
      const res = await fetch(`/api/lab/samples`);
      if (res.ok) {
        const data = await res.json();
        setLabSamples(data.samples || []);
      }
    } catch (e) {
      console.warn("Could not fetch lab samples:", e);
    }
  };

  const fetchPendingTasks = async () => {
    try {
      const res = await fetch(`/api/doctor/pending`);
      if (res.ok) {
        const data = await res.json();
        setPendingTasks(data.tasks || []);
      }
    } catch (e) {
      console.warn("Could not fetch pending tasks:", e);
    }
  };

  const fetchTelemetry = async () => {
    try {
      const res = await fetch(`/api/telemetry/stats`);
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (e) {
      console.warn("Could not fetch telemetry:", e);
    }
  };

  // Initial load
  useEffect(() => {
    const init = async () => {
      try {
        const hRes = await fetch(`/api/health`);
        if (hRes.ok) setServerHealthy(true);
      } catch (e) {
        console.warn("Health check failed:", e);
      }
      fetchDoctorsDirectory();
      fetchLabSamples();
      fetchPendingTasks();
      fetchTelemetry();
      fetchDoctorAppointments();
    };
    init();

    const interval = setInterval(() => {
      fetchPendingTasks();
      fetchTelemetry();
    }, 8000);

    return () => clearInterval(interval);
  }, []);

  // Sync appointments when navigating to my_appointments tab if patient is selected
  useEffect(() => {
    if (patientSubTab === "my_appointments" && patientUser) {
      fetchMyAppointments(patientUser.patient_id || patientUser.mrn);
    }
  }, [patientSubTab, patientUser]);

  // ================= ACTION HANDLERS =================
  const handleSendMessage = async (textToSend?: string) => {
    const userMsg = (textToSend || inputMessage).trim();
    if (!userMsg || isLoading) return;

    setInputMessage("");
    const newMsg: Message = {
      id: "msg_" + Date.now(),
      role: "user",
      content: userMsg,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, newMsg]);
    setIsLoading(true);

    // AUTO-DETECT PATIENT ID IN CHAT (e.g. "p1", "p2", "CCC-PK-100001", "my id is p1", "patient id: p2")
    const idPattern = /^(?:my\s+id\s+is\s+|patient\s+id:?\s+|mrn:?\s+)?(p\d+|CCC-PK-\d+|MRN-\d+)\b/i;
    const match = userMsg.match(idPattern);
    let detectedId = patientUser?.patient_id || patientUser?.mrn;

    if (match && !patientUser) {
      const parsedId = match[1].toLowerCase();
      detectedId = parsedId;
      // Fetch record from database in background
      handleFetchPatientRecord(parsedId);
    }

    try {
      const res = await fetch(`/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          message: userMsg,
          language: language,
          patient_identifier: detectedId,
          patient_id: detectedId || "p1",
          patient_name: patientUser?.patient_name || "Valued Patient",
          phone: patientUser?.phone || "03001234567",
        }),
      });

      if (res.ok) {
        const data = await res.json();
        if (data.session_id) setSessionId(data.session_id);

        if (data.messages && Array.isArray(data.messages)) {
          const formatted = data.messages.map((m: any, idx: number) => ({
            id: m.id || `res_${Date.now()}_${idx}`,
            role: m.role || "assistant",
            content: m.content || "",
            agent: m.agent,
            timestamp: m.timestamp || new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          }));
          setMessages(formatted);
        } else if (data.reply || data.response) {
          setMessages((prev) => [
            ...prev,
            {
              id: "asst_" + Date.now(),
              role: "assistant",
              content: data.reply || data.response,
              agent: data.agent || data.current_agent,
              timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
            },
          ]);
        }

        // If backend recognized returning patient, update patient profile and appointments
        if (data.patient && data.patient.patient_name && data.patient.patient_name !== "Guest Patient" && data.patient.patient_name !== "Valued Patient") {
          setPatientUser((prev) => ({
            patient_id: data.patient.patient_id || prev?.patient_id || "p1",
            patient_name: data.patient.patient_name,
            mrn: data.patient.mrn || prev?.mrn || "",
            phone: data.patient.phone || prev?.phone || "",
            age: prev?.age || 30,
            gender: prev?.gender || "Unspecified",
            known_allergies: prev?.known_allergies || [],
            chronic_conditions: prev?.chronic_conditions || []
          }));
          fetchMyAppointments(data.patient.patient_id || data.patient.mrn);
        }
      }
    } catch (e) {
      console.error("Chat error:", e);
      setMessages((prev) => [
        ...prev,
        {
          id: "err_" + Date.now(),
          role: "assistant",
          content: "Sorry, I encountered a temporary connection issue. Please check your backend connection.",
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const extractLabData = (raw: any): LabAnalysisResult | null => {
    if (!raw) return null;
    if (raw.data && typeof raw.data === "object" && raw.data.tests) {
      return raw.data as LabAnalysisResult;
    }
    if (raw.tests) {
      return raw as LabAnalysisResult;
    }
    return (raw.data || raw) as LabAnalysisResult;
  };

  const handleChatFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || !e.target.files[0]) return;
    const file = e.target.files[0];

    const formData = new FormData();
    formData.append("file", file);

    setLabLoading(true);
    try {
      const upRes = await fetch(`/api/lab/upload`, { method: "POST", body: formData });
      if (upRes.ok) {
        const upData = await upRes.json();
        const labData = extractLabData(upData);
        if (labData) {
          setLabResult(labData);
          setSelectedSampleFile(file.name);

          const reportLabel = labData.panel || "Laboratory Investigation";
          const explanation = labData.urdulish_summary || "Aap ki lab report extract ho chuki hai.";

          // Sync with backend session
          try {
            await fetch(`/api/lab/chat-sync`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                session_id: sessionId,
                patient_identifier: patientUser?.patient_id || "p1",
                file_name: file.name,
                user_prompt: `📎 Uploaded Lab Report: ${file.name} (${reportLabel})`,
                agent_explanation: explanation,
                panel: labData.panel,
                abnormal_count: labData.abnormal_count || 0,
              }),
            });
          } catch (syncErr) {
            console.warn("Lab chat-sync note:", syncErr);
          }

          // Add User & Assistant messages to chat
          const userMsg: Message = {
            id: "user_upload_" + Date.now(),
            role: "user",
            content: `📎 **Uploaded Lab Report:** \`${file.name}\` (${reportLabel})\n*Multimodal Vision AI Analysis (100% Non-Diagnostic)*`,
            timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          };

          const agentMsg: Message = {
            id: "lab_agent_" + Date.now(),
            role: "assistant",
            agent: "Lab Intelligence & Records Agent",
            content: explanation,
            timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          };

          setMessages((prev) => [...prev, userMsg, agentMsg]);
        }
      } else {
        const err = await upRes.json().catch(() => ({ detail: "Upload failed" }));
        alert(`Failed to analyze uploaded file: ${err.detail || upRes.statusText}`);
      }
    } catch (err) {
      console.error("File upload failed:", err);
      alert("Lab report upload failed. Please verify server connection.");
    } finally {
      setLabLoading(false);
      e.target.value = "";
    }
  };

  const handleLabFileUpload = async (file: File) => {
    setSelectedSampleFile(file.name);
    setLabLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(`/api/lab/upload`, {
        method: "POST",
        body: formData,
      });

      if (res.ok) {
        const raw = await res.json();
        const labData = extractLabData(raw);
        setLabResult(labData);
      } else {
        const err = await res.json().catch(() => ({ detail: "Upload failed" }));
        alert(`Failed to analyze uploaded lab report: ${err.detail || res.statusText}`);
      }
    } catch (err) {
      console.error("Lab upload failed:", err);
      alert("Failed to connect to the backend server for lab analysis.");
    } finally {
      setLabLoading(false);
    }
  };

  const handleAnalyzeSample = async (filename: string) => {
    setSelectedSampleFile(filename);
    setLabLoading(true);
    try {
      const res = await fetch(`/api/lab/analyze-sample?filename=${encodeURIComponent(filename)}`, { method: "POST" });
      if (res.ok) {
        const raw = await res.json();
        const labData = extractLabData(raw);
        setLabResult(labData);
      } else {
        const err = await res.json().catch(() => ({ detail: "Analysis failed" }));
        console.error("Sample analysis failed:", err);
      }
    } catch (e) {
      console.error("Sample analysis failed:", e);
    } finally {
      setLabLoading(false);
    }
  };

  const handleSendLabResultToChat = async () => {
    if (!labResult) return;

    const reportLabel = labResult.panel || "Laboratory Investigation";
    const refId = labResult.report_id || selectedSampleFile || "Lab Report";
    const agentExplanation = labResult.urdulish_summary || "Lab values extracted successfully.";

    // 1. Sync with backend LangGraph session
    try {
      await fetch(`/api/lab/chat-sync`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          patient_identifier: patientUser?.patient_id || "p1",
          file_name: refId,
          user_prompt: `🧪 I am sharing my lab report (${reportLabel}) for clinical consultation.`,
          agent_explanation: agentExplanation,
          panel: labResult.panel,
          abnormal_count: labResult.abnormal_count || 0,
        }),
      });
    } catch (err) {
      console.warn("Could not sync lab report to chat session:", err);
    }

    // 2. Add both User and Assistant messages to chat state
    const userMsg: Message = {
      id: "lab_share_user_" + Date.now(),
      role: "user",
      content: `🧪 **Lab Report:** \`${refId}\` (${reportLabel})\n*Shared from Lab Vision Intelligence*`,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    const agentMsg: Message = {
      id: "lab_share_agent_" + Date.now(),
      role: "assistant",
      agent: "Lab Intelligence & Records Agent",
      content: agentExplanation,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg, agentMsg]);

    // 3. Switch to patient chat view
    setActiveTab("patient");
    setPatientSubTab("chat");
  };

  const handleConfirmBooking = async () => {
    if (!bookingDoctor || !bookingSlotModal) return;

    setBookingSubmitting(true);
    try {
      const res = await fetch(`/api/appointments/book`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          doctor_id: bookingDoctor.id || bookingDoctor.doctor_id,
          patient_name: patientUser ? patientUser.patient_name : "Valued Patient",
          phone: patientUser ? patientUser.phone : "03001234567",
          mrn: patientUser ? patientUser.mrn : "p1",
          date: selectedScheduleDate,
          time_slot: typeof bookingSlotModal === "string" ? bookingSlotModal : bookingSlotModal.display_time || bookingSlotModal.time || bookingSlotModal.slot_id,
          slot_iso: bookingSlotModal?.slot_start || `${selectedScheduleDate}T12:00:00+00:00`,
          reason: bookingReason,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setBookingSuccessResult(data);
        fetchDoctorSchedule(bookingDoctor.id, selectedScheduleDate);
        fetchMyAppointments();
        fetchDoctorAppointments();
      } else {
        alert("Booking failed. Please try an alternative slot.");
      }
    } catch (e) {
      console.error("Booking error:", e);
    } finally {
      setBookingSubmitting(false);
    }
  };

  const handleCancelAppointment = async (appId: string) => {
    if (!confirm("Are you sure you want to cancel this appointment?")) return;
    try {
      const res = await fetch(`/api/appointments/${appId}/cancel`, { method: "POST" });
      if (res.ok) {
        fetchMyAppointments();
        fetchDoctorAppointments();
        if (selectedDoctorId) fetchDoctorSchedule(selectedDoctorId, selectedScheduleDate);
      }
    } catch (e) {
      console.error("Cancel appointment error:", e);
    }
  };

  const handleDoctorLogin = async (e?: React.FormEvent, customEmail?: string, customPassword?: string) => {
    if (e && e.preventDefault) e.preventDefault();
    setLoginError("");

    const targetEmail = (customEmail || loginEmail).trim();
    const targetPassword = (customPassword || loginPassword).trim();

    try {
      const res = await fetch(`/api/doctor/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: targetEmail, password: targetPassword }),
      });

      if (res.ok) {
        const data = await res.json();
        const doc = data.doctor;
        setDoctorUser({
          ...doc,
          doctor_name: doc.doctor_name || doc.name || "Doctor",
          doctor_id: doc.doctor_id || doc.id,
        });
        setShowDoctorLoginModal(false);
        setActiveTab("doctor");
      } else {
        const err = await res.json().catch(() => ({ detail: "Invalid doctor email or password" }));
        setLoginError(err.detail || "Invalid doctor email or password");
      }
    } catch (err) {
      setLoginError("Connection to doctor auth failed");
    }
  };

  const handleSignupSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSignupSubmitting(true);

    try {
      const res = await fetch(`/api/patients/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(signupForm),
      });

      if (res.ok) {
        const data = await res.json();
        setPatientUser(data.patient);
        setShowSignupModal(false);
        alert(`Patient registered successfully! Generated MRN: ${data.mrn || data.patient?.mrn}`);
      } else {
        alert("Registration failed. Please try again.");
      }
    } catch (err) {
      alert("Registration failed due to connection error.");
    } finally {
      setSignupSubmitting(false);
    }
  };

  const handleApproveTask = async (taskId: string, notes: string, editedText?: string) => {
    try {
      const res = await fetch(`/api/doctor/decision`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task_id: taskId,
          action: "APPROVE",
          doctor_notes: notes,
          final_message_urdulish: editedText,
        }),
      });
      if (res.ok) {
        fetchPendingTasks();
        fetchTelemetry();
      }
    } catch (e) {
      console.error("Approve task failed:", e);
    }
  };

  const handleRejectTask = async (taskId: string, notes: string) => {
    try {
      const res = await fetch(`/api/doctor/decision`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task_id: taskId,
          action: "REJECT",
          doctor_notes: notes,
        }),
      });
      if (res.ok) {
        fetchPendingTasks();
        fetchTelemetry();
      }
    } catch (e) {
      console.error("Reject task failed:", e);
    }
  };

  const handleSubmitPrescription = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prescribingApp) return;

    if (!prescriptionForm.diagnosis || !prescriptionForm.diagnosis.trim()) {
      setPrescribeModalError("Please provide a clinical diagnosis / assessment.");
      return;
    }

    setPrescribeSubmitting(true);
    setPrescribeModalError("");
    try {
      const res = await fetch(`/api/doctor/prescribe`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          appointment_id: prescribingApp.appointment_id || prescribingApp.id || prescribingApp.booking_reference,
          patient_id: prescribingApp.patient_id || prescribingApp.mrn || "p1",
          doctor_id: doctorUser?.doctor_id || doctorUser?.id || prescribingApp.doctor_id,
          doctor_name: doctorUser?.doctor_name || (doctorUser as any)?.name,
          doctor_specialty: doctorUser?.specialty,
          pmdc_number: doctorUser?.pmdc_number,
          diagnosis: prescriptionForm.diagnosis,
          advice: prescriptionForm.advice,
          medicines: prescriptionForm.medicines,
        }),
      });

      const data = await res.json().catch(() => ({}));

      if (res.ok) {
        setPrescribeModalSuccess(true);
        const targetRef = (prescribingApp.booking_reference || prescribingApp.id || "").replace("#", "").trim();
        setDoctorAppointments((prev) =>
          prev.map((a) => {
            const ref = (a.booking_reference || a.id || "").replace("#", "").trim();
            if (ref === targetRef) {
              return {
                ...a,
                status: "fulfilled",
                has_prescription: true,
                prescription: data.prescription,
              };
            }
            return a;
          })
        );
        fetchDoctorAppointments();
        fetchMyAppointments();
        setTimeout(() => {
          setShowPrescribeModal(false);
          setPrescribeModalSuccess(false);
        }, 1500);
      } else {
        setPrescribeModalError(data.detail || "Failed to issue prescription. You are only authorized to prescribe for your own booked patients.");
      }
    } catch (err: any) {
      console.error("Prescribe error:", err);
      setPrescribeModalError("Network error: Could not reach the server. Please check your connection.");
    } finally {
      setPrescribeSubmitting(false);
    }
  };

  const handleRestoreAppointment = async (ref: string) => {
    if (!ref.trim()) return;
    setRestoreLoading(true);
    try {
      const res = await fetch(`/api/appointments/${encodeURIComponent(ref.trim())}/restore`);
      if (res.ok) {
        const data = await res.json();
        if (data.session_id) setSessionId(data.session_id);
        if (data.messages && data.messages.length > 0) {
          setMessages(data.messages);
        }
        alert(`Session restored for booking reference: ${ref}`);
      } else {
        alert("Booking reference not found.");
      }
    } catch (e) {
      console.error("Restore error:", e);
    } finally {
      setRestoreLoading(false);
    }
  };

  return (
    <>
      {/* Ambient Pastel Glow Blobs in Background */}
      <div className="ambient-bg">
        <div className="ambient-blob-1" />
        <div className="ambient-blob-2" />
        <div className="ambient-blob-3" />
      </div>

      {/* Main App Outer Shell */}
      <div className="app-shell">
        {/* Left Sidebar */}
        <Sidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          patientSubTab={patientSubTab}
          setPatientSubTab={setPatientSubTab}
          pendingApprovalsCount={pendingTasks.length}
          doctorUser={doctorUser}
          onOpenDoctorLogin={() => setShowDoctorLoginModal(true)}
        />

        {/* Main Workspace Card */}
        <div className="main-workspace-card">
          {/* Header */}
          <Header
            patientUser={patientUser}
            doctorUser={doctorUser}
            onOpenDoctorLogin={() => setShowDoctorLoginModal(true)}
            onPatientSignOut={() => setPatientUser(null)}
            onDoctorSignOut={() => setDoctorUser(null)}
            onFetchPatientById={handleFetchPatientRecord}
            language={language}
            setLanguage={setLanguage}
            serverHealthy={serverHealthy}
          />

          {/* Workspace Body Split */}
          <div className="workspace-body-split">
            {/* Center Viewport */}
            <div className="center-viewport">
              {/* PATIENT VIEW 1: Chat */}
              {activeTab === "patient" && patientSubTab === "chat" && (
                <ChatView
                  messages={messages}
                  inputMessage={inputMessage}
                  setInputMessage={setInputMessage}
                  onSendMessage={handleSendMessage}
                  isLoading={isLoading}
                  language={language}
                  patientUser={patientUser}
                  onFetchPatientById={handleFetchPatientRecord}
                  onNavigateToSchedule={() => setPatientSubTab("schedule")}
                  onNavigateToRecords={() => setPatientSubTab("my_appointments")}
                  onFileUpload={handleChatFileUpload}
                  labLoading={labLoading}
                  restoreInputRef={restoreInputRef}
                  setRestoreInputRef={setRestoreInputRef}
                  onRestoreAppointment={handleRestoreAppointment}
                  restoreLoading={restoreLoading}
                />
              )}

              {/* PATIENT VIEW 2: Doctor Schedule & Booking */}
              {activeTab === "patient" && patientSubTab === "schedule" && (
                <ScheduleView
                  doctorsList={doctorsList}
                  selectedDoctorId={selectedDoctorId}
                  setSelectedDoctorId={setSelectedDoctorId}
                  selectedScheduleDate={selectedScheduleDate}
                  setSelectedScheduleDate={setSelectedScheduleDate}
                  doctorSchedule={doctorSchedule}
                  scheduleLoading={scheduleLoading}
                  selectedSpecialtyFilter={selectedSpecialtyFilter}
                  setSelectedSpecialtyFilter={setSelectedSpecialtyFilter}
                  onSelectSlotToBook={(slot, doctor) => {
                    setBookingSlotModal(slot);
                    setBookingDoctor(doctor);
                    setBookingSuccessResult(null);
                  }}
                  onFetchSchedule={fetchDoctorSchedule}
                />
              )}

              {/* PATIENT VIEW 3: My Appointments */}
              {activeTab === "patient" && patientSubTab === "my_appointments" && (
                <MyAppointmentsView
                  appointments={myAppointments}
                  isLoading={myAppointmentsLoading}
                  currentPatient={patientUser}
                  onSelectPatient={(pid) => {
                    handleFetchPatientRecord(pid);
                    fetchMyAppointments(pid);
                  }}
                  onCancelAppointment={handleCancelAppointment}
                  onViewPrescription={(app) => setViewRxModalApp(app)}
                  onNavigateToSchedule={() => setPatientSubTab("schedule")}
                />
              )}

              {/* DOCTOR VIEW: Workstation */}
              {activeTab === "doctor" && (
                <DoctorPortal
                  doctorUser={doctorUser}
                  doctorSubTab={doctorSubTab}
                  setDoctorSubTab={setDoctorSubTab}
                  onOpenDoctorLogin={() => setShowDoctorLoginModal(true)}
                  patientSearchQuery={patientSearchQuery}
                  setPatientSearchQuery={setPatientSearchQuery}
                  onSearchPatientHistory={fetchPatientHistory}
                  patientHistoryData={patientHistoryData}
                  historyLoading={historyLoading}
                  appointments={doctorAppointments}
                  appointmentFilter={doctorAppointmentFilter}
                  setAppointmentFilter={setDoctorAppointmentFilter}
                  appointmentSearch={doctorAppointmentSearch}
                  setAppointmentSearch={setDoctorAppointmentSearch}
                  onOpenPrescribeModal={(app) => {
                    setPrescribingApp(app);
                    setPrescribeModalError("");
                    setPrescribeModalSuccess(false);
                    setPrescriptionForm({
                      diagnosis: app.reason || app.reason_for_visit || "Clinical Consultation Assessment",
                      advice: "Take medicines on time as prescribed. Keep well hydrated and take adequate rest. Contact clinic if symptoms worsen.",
                      medicines: [
                        { medicine_name: "Tab Panadol", dosage: "500mg", frequency: "1-0-1", duration: "5 days", instructions: "After meals" },
                        { medicine_name: "Syp Hydryllin", dosage: "10ml", frequency: "1-1-1", duration: "5 days", instructions: "For cough relief" },
                      ],
                    });
                    setShowPrescribeModal(true);
                  }}
                  onViewPrescription={(app) => setViewRxModalApp(app)}
                  pendingTasks={pendingTasks}
                  onApproveTask={handleApproveTask}
                  onRejectTask={handleRejectTask}
                />
              )}

              {/* LAB VIEW: Multimodal Vision */}
              {activeTab === "lab" && (
                <LabVisionView
                  labSamples={labSamples}
                  selectedSampleFile={selectedSampleFile}
                  onAnalyzeSample={handleAnalyzeSample}
                  onFileUpload={handleLabFileUpload}
                  labLoading={labLoading}
                  labResult={labResult}
                  showRawJson={showRawJson}
                  setShowRawJson={setShowRawJson}
                  onSendResultToChat={handleSendLabResultToChat}
                />
              )}

              {/* TELEMETRY VIEW: LangSmith Observability */}
              {activeTab === "telemetry" && <TelemetryView stats={stats} />}
            </div>

            {/* Right Healthcare Support Panel (Visible on patient view matching screenshot) */}
            {activeTab === "patient" && (
              <RightSidebar
                setActiveTab={setActiveTab}
                setPatientSubTab={setPatientSubTab}
                onSendPresetMessage={(msg) => handleSendMessage(msg)}
              />
            )}
          </div>
        </div>
      </div>

      {/* ================= MODALS ================= */}
      {/* Doctor Login Modal (Only for doctor workstation) */}
      <DoctorLoginModal
        isOpen={showDoctorLoginModal}
        onClose={() => setShowDoctorLoginModal(false)}
        email={loginEmail}
        setEmail={setLoginEmail}
        password={loginPassword}
        setPassword={setLoginPassword}
        error={loginError}
        onSubmit={handleDoctorLogin}
        onQuickLogin={(eMail, pwd) => handleDoctorLogin(undefined, eMail, pwd)}
      />

      {/* Signup Modal (Optional quick patient registration) */}
      <SignupModal
        isOpen={showSignupModal}
        onClose={() => setShowSignupModal(false)}
        form={signupForm}
        setForm={setSignupForm}
        isSubmitting={signupSubmitting}
        onSubmit={handleSignupSubmit}
      />

      {/* Booking Slot Modal */}
      <BookingSlotModal
        isOpen={!!bookingSlotModal}
        onClose={() => {
          setBookingSlotModal(null);
          setBookingSuccessResult(null);
        }}
        slot={bookingSlotModal}
        doctor={bookingDoctor}
        date={selectedScheduleDate}
        patientUser={patientUser}
        reason={bookingReason}
        setReason={setBookingReason}
        isSubmitting={bookingSubmitting}
        successResult={bookingSuccessResult}
        onConfirm={handleConfirmBooking}
        onDismissSuccess={() => {
          setBookingSlotModal(null);
          setBookingSuccessResult(null);
          setPatientSubTab("my_appointments");
        }}
      />

      {/* Prescribe Modal */}
      <PrescribeModal
        isOpen={showPrescribeModal}
        onClose={() => {
          setShowPrescribeModal(false);
          setPrescribeModalError("");
          setPrescribeModalSuccess(false);
        }}
        appointment={prescribingApp}
        doctorUser={doctorUser}
        prescriptionForm={prescriptionForm}
        setPrescriptionForm={setPrescriptionForm}
        onAddMedicineRow={() =>
          setPrescriptionForm((prev) => ({
            ...prev,
            medicines: [
              ...prev.medicines,
              { medicine_name: "", dosage: "", frequency: "1-0-1", duration: "5 days", instructions: "After meals" },
            ],
          }))
        }
        onRemoveMedicineRow={(idx) =>
          setPrescriptionForm((prev) => ({
            ...prev,
            medicines: prev.medicines.filter((_, i) => i !== idx),
          }))
        }
        onMedicineChange={(idx, field, val) =>
          setPrescriptionForm((prev) => ({
            ...prev,
            medicines: prev.medicines.map((m, i) => (i === idx ? { ...m, [field]: val } : m)),
          }))
        }
        isSubmitting={prescribeSubmitting}
        errorMessage={prescribeModalError}
        successMessage={prescribeModalSuccess}
        onSubmit={handleSubmitPrescription}
      />

      {/* View Prescription Modal */}
      <ViewRxModal
        isOpen={!!viewRxModalApp}
        onClose={() => setViewRxModalApp(null)}
        appointment={viewRxModalApp}
      />
    </>
  );
}
