"use client";

import React from "react";
import { ActiveTab, PatientSubTab } from "@/types";

interface SidebarProps {
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
  patientSubTab: PatientSubTab;
  setPatientSubTab: (tab: PatientSubTab) => void;
  pendingApprovalsCount?: number;
  unreadMessagesCount?: number;
  doctorUser?: any | null;
  onOpenDoctorLogin?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  patientSubTab,
  setPatientSubTab,
  pendingApprovalsCount = 0,
  unreadMessagesCount = 2,
  doctorUser = null,
  onOpenDoctorLogin,
}) => {
  const isChatActive = activeTab === "patient" && patientSubTab === "chat";
  const isAppointmentsActive = activeTab === "patient" && patientSubTab === "schedule";
  const isRecordsActive = activeTab === "patient" && patientSubTab === "my_appointments";
  const isDoctorPortalActive = activeTab === "doctor";
  const isLabActive = activeTab === "lab";
  const isTelemetryActive = activeTab === "telemetry";

  return (
    <aside className="app-sidebar">
      {/* Brand Header */}
      <div className="sidebar-logo">
        <div className="logo-badge">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" />
            <path d="M12 7v6M9 10h6" stroke="#ffffff" strokeWidth="2.2" strokeLinecap="round" />
          </svg>
        </div>
        <div>
          <div className="logo-text-title">City Care</div>
          <div className="logo-text-sub">Clinics</div>
        </div>
      </div>

      {/* Nav Menu Items */}
      <nav className="sidebar-nav">
        {/* Chat */}
        <button
          className={`nav-item ${isChatActive ? "active" : ""}`}
          onClick={() => {
            setActiveTab("patient");
            setPatientSubTab("chat");
          }}
        >
          <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
          <span>Chat</span>
        </button>

        {/* Appointments (Schedule booking) */}
        <button
          className={`nav-item ${isAppointmentsActive ? "active" : ""}`}
          onClick={() => {
            setActiveTab("patient");
            setPatientSubTab("schedule");
          }}
        >
          <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
            <line x1="16" y1="2" x2="16" y2="6" />
            <line x1="8" y1="2" x2="8" y2="6" />
            <line x1="3" y1="10" x2="21" y2="10" />
          </svg>
          <span>Appointments</span>
        </button>

        {/* Medical Records (Patient Appointments & History) */}
        <button
          className={`nav-item ${isRecordsActive ? "active" : ""}`}
          onClick={() => {
            setActiveTab("patient");
            setPatientSubTab("my_appointments");
          }}
        >
          <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
            <polyline points="10 9 9 9 8 9" />
          </svg>
          <span>Medical Records</span>
        </button>

        {/* Prescriptions (quick view of records tab) */}
        <button
          className={`nav-item ${isRecordsActive ? "active" : ""}`}
          onClick={() => {
            setActiveTab("patient");
            setPatientSubTab("my_appointments");
          }}
        >
          <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z" />
            <line x1="8.5" y1="8.5" x2="15.5" y2="15.5" />
          </svg>
          <span>Prescriptions</span>
        </button>

        {/* Messages with badge */}
        <button
          className="nav-item"
          onClick={() => {
            setActiveTab("patient");
            setPatientSubTab("chat");
          }}
        >
          <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
            <polyline points="22,6 12,13 2,6" />
          </svg>
          <span>Messages</span>
          {unreadMessagesCount > 0 && <span className="nav-badge-count">{unreadMessagesCount}</span>}
        </button>

        {/* Doctors Directory */}
        <button
          className={`nav-item ${isAppointmentsActive ? "active" : ""}`}
          onClick={() => {
            setActiveTab("patient");
            setPatientSubTab("schedule");
          }}
        >
          <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
            <circle cx="9" cy="7" r="4" />
            <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
            <path d="M16 3.13a4 4 0 0 1 0 7.75" />
          </svg>
          <span>Doctors</span>
        </button>

        <div style={{ height: "1px", background: "#edf2f7", margin: "8px 0" }} />

        {/* Doctor Portal (HITL & Prescribe & Dossier) */}
        <button
          className={`nav-item ${isDoctorPortalActive ? "active" : ""}`}
          onClick={() => {
            setActiveTab("doctor");
            if (!doctorUser && onOpenDoctorLogin) {
              onOpenDoctorLogin();
            }
          }}
        >
          <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6V4a2 2 0 0 0-2-2h-1a.2.2 0 1 0 .3.3" />
            <path d="M8 15v1a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6v-4" />
            <circle cx="20" cy="10" r="2" />
          </svg>
          <span>Doctor Portal</span>
          {pendingApprovalsCount > 0 && (
            <span className="nav-badge-count" style={{ background: "#f59e0b" }}>
              {pendingApprovalsCount}
            </span>
          )}
        </button>

        {/* Lab Vision AI */}
        <button
          className={`nav-item ${isLabActive ? "active" : ""}`}
          onClick={() => setActiveTab("lab")}
        >
          <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M10 2v7.31L4.62 18.5A2 2 0 0 0 6.34 22h11.32a2 2 0 0 0 1.72-3.5L14 9.31V2" />
            <line x1="8.5" y1="2" x2="15.5" y2="2" />
            <line x1="6.5" y1="16" x2="17.5" y2="16" />
          </svg>
          <span>Lab Vision AI</span>
        </button>

        {/* Telemetry */}
        <button
          className={`nav-item ${isTelemetryActive ? "active" : ""}`}
          onClick={() => setActiveTab("telemetry")}
        >
          <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
          </svg>
          <span>Telemetry</span>
        </button>
      </nav>

      {/* Bottom Health Matters Card */}
      <div className="sidebar-footer-card">
        <div className="sidebar-footer-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" />
          </svg>
        </div>
        <div>
          <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "#065f46" }}>Your health matters</div>
          <div style={{ fontSize: "0.72rem", color: "#047857", marginTop: "1px" }}>We're here for you, anytime.</div>
        </div>
      </div>

      {/* Organic Botanical Graphic illustration at corner */}
      <svg className="sidebar-botanical-graphic" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M10 90C30 80 40 50 60 40C70 35 90 45 90 70C90 90 60 100 10 90Z" fill="#a7f3d0" fillOpacity="0.5" />
        <path d="M0 100C15 75 35 60 55 70C65 75 70 95 60 100C45 105 15 105 0 100Z" fill="#99f6e4" fillOpacity="0.6" />
        <path d="M25 100C40 85 55 85 70 95C75 100 65 105 50 105C35 105 25 100 25 100Z" fill="#fed7aa" fillOpacity="0.5" />
      </svg>
    </aside>
  );
};
