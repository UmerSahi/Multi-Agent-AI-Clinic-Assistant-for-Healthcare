"use client";

import React, { useState } from "react";
import { Patient, DoctorAccount } from "@/types";

interface HeaderProps {
  patientUser: Patient | null;
  doctorUser: DoctorAccount | null;
  onOpenDoctorLogin: () => void;
  onPatientSignOut: () => void;
  onDoctorSignOut: () => void;
  onFetchPatientById: (id: string) => void;
  language: "Urdu" | "English";
  setLanguage: (lang: "Urdu" | "English") => void;
  serverHealthy: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  patientUser,
  doctorUser,
  onOpenDoctorLogin,
  onPatientSignOut,
  onDoctorSignOut,
  onFetchPatientById,
  language,
  setLanguage,
  serverHealthy,
}) => {
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);
  const [quickIdInput, setQuickIdInput] = useState("");

  const getInitials = (name?: string) => {
    if (!name) return "PT";
    const parts = name.trim().split(" ");
    if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    return name.slice(0, 2).toUpperCase();
  };

  const handleQuickFetch = (e: React.FormEvent) => {
    e.preventDefault();
    if (quickIdInput.trim()) {
      onFetchPatientById(quickIdInput.trim());
      setQuickIdInput("");
      setUserDropdownOpen(false);
    }
  };

  return (
    <header className="workspace-header">
      {/* Left: Assistant Status */}
      <div className="assistant-chip">
        <div className="assistant-avatar">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" />
          </svg>
        </div>
        <div>
          <div className="assistant-status-text">City Care Assistant</div>
          <div style={{ fontSize: "0.74rem", color: "#64748b", display: "flex", alignItems: "center", marginTop: "1px" }}>
            <span className="online-dot" />
            <span>Online</span>
          </div>
        </div>
      </div>

      {/* Right Actions */}
      <div className="header-actions">
        {/* Language Toggle */}
        <button
          className="header-icon-btn"
          style={{ width: "auto", borderRadius: "20px", padding: "0 10px", fontSize: "0.78rem", fontWeight: 600, gap: "6px" }}
          onClick={() => setLanguage(language === "Urdu" ? "English" : "Urdu")}
          title="Switch Language"
        >
          <span>🌐</span>
          <span>{language === "Urdu" ? "UrduLish" : "English"}</span>
        </button>

        {/* Server Status Dot */}
        <div
          title={serverHealthy ? "Connected to Multi-Agent API" : "Connecting to API..."}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "5px",
            fontSize: "0.72rem",
            color: serverHealthy ? "#059669" : "#f59e0b",
            background: serverHealthy ? "#ecfdf5" : "#fffbeb",
            padding: "4px 8px",
            borderRadius: "12px",
            border: `1px solid ${serverHealthy ? "#a7f3d0" : "#fde68a"}`,
          }}
        >
          <span style={{ width: 6, height: 6, borderRadius: "50%", background: serverHealthy ? "#10b981" : "#f59e0b" }} />
          <span>{serverHealthy ? "Live" : "Connecting"}</span>
        </div>

        {/* Notification Bell */}
        <button className="header-icon-btn" title="Notifications">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
            <path d="M13.73 21a2 2 0 0 1-3.46 0" />
          </svg>
          <span className="header-icon-badge" />
        </button>

        {/* User Profile Chip (No sign in barrier for patients!) */}
        <div style={{ position: "relative" }}>
          {patientUser ? (
            <div
              className="user-profile-pill"
              onClick={() => setUserDropdownOpen(!userDropdownOpen)}
              title="Click to view record or switch patient"
            >
              <div className="user-avatar-circle">
                {getInitials(patientUser.patient_name)}
              </div>
              <div style={{ display: "flex", flexDirection: "column", textAlign: "left" }}>
                <span className="user-name">{patientUser.patient_name}</span>
                <span style={{ fontSize: "0.68rem", color: "#0f766e", fontWeight: 700 }}>
                  ID: {patientUser.patient_id || patientUser.mrn}
                </span>
              </div>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#64748b" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </div>
          ) : doctorUser ? (
            <div
              className="user-profile-pill"
              onClick={() => setUserDropdownOpen(!userDropdownOpen)}
              style={{ background: "#ecfdf5", borderColor: "#a7f3d0" }}
            >
              <div className="user-avatar-circle" style={{ background: "#d1fae5", color: "#065f46" }}>
                Dr
              </div>
              <span className="user-name">{doctorUser.doctor_name || "Doctor"}</span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#64748b" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </div>
          ) : (
            <div
              className="user-profile-pill"
              onClick={() => setUserDropdownOpen(!userDropdownOpen)}
              title="Click to fetch your record by Patient ID"
            >
              <div className="user-avatar-circle" style={{ background: "#f1f5f9", color: "#64748b" }}>
                👤
              </div>
              <span className="user-name">Guest Patient</span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#64748b" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </div>
          )}

          {/* User Dropdown Menu */}
          {userDropdownOpen && (
            <div
              style={{
                position: "absolute",
                top: "calc(100% + 8px)",
                right: 0,
                width: "250px",
                background: "#ffffff",
                border: "1px solid #e2e8f0",
                borderRadius: "16px",
                boxShadow: "0 10px 30px rgba(15, 23, 42, 0.12)",
                padding: "10px",
                zIndex: 50,
                display: "flex",
                flexDirection: "column",
                gap: "8px",
              }}
            >
              {patientUser ? (
                <>
                  <div style={{ padding: "8px 10px", background: "#f0fdf9", border: "1px solid #ccfbf1", borderRadius: "10px" }}>
                    <div style={{ fontWeight: 700, fontSize: "0.88rem", color: "#0f172a" }}>
                      {patientUser.patient_name}
                    </div>
                    <div style={{ fontSize: "0.74rem", color: "#0f766e", fontWeight: 600, marginTop: "2px" }}>
                      Patient ID: {patientUser.patient_id} • MRN: {patientUser.mrn}
                    </div>
                    {patientUser.phone && (
                      <div style={{ fontSize: "0.72rem", color: "#64748b", marginTop: "2px" }}>
                        Phone: {patientUser.phone}
                      </div>
                    )}
                  </div>
                  <button
                    className="nav-item"
                    style={{ padding: "8px 12px", fontSize: "0.82rem", color: "#e11d48" }}
                    onClick={() => {
                      setUserDropdownOpen(false);
                      onPatientSignOut();
                    }}
                  >
                    <span>Clear / Switch Patient</span>
                  </button>
                </>
              ) : doctorUser ? (
                <>
                  <div style={{ padding: "8px 12px", borderBottom: "1px solid #f1f5f9" }}>
                    <div style={{ fontWeight: 700, fontSize: "0.88rem", color: "#0f172a" }}>
                      {doctorUser.doctor_name}
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "#0d9488", marginTop: "2px" }}>
                      {doctorUser.specialty || "Physician"}
                    </div>
                  </div>
                  <button
                    className="nav-item"
                    style={{ padding: "8px 12px", fontSize: "0.84rem", color: "#e11d48" }}
                    onClick={() => {
                      setUserDropdownOpen(false);
                      onDoctorSignOut();
                    }}
                  >
                    <span>Doctor Sign Out</span>
                  </button>
                </>
              ) : (
                <>
                  {/* Quick Fetch Form by Patient ID */}
                  <form onSubmit={handleQuickFetch} style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                    <label style={{ fontSize: "0.76rem", fontWeight: 700, color: "#334155" }}>
                      Returning Patient? Enter ID:
                    </label>
                    <div style={{ display: "flex", gap: "6px" }}>
                      <input
                        type="text"
                        placeholder="e.g. p1 or CCC-PK-100001"
                        value={quickIdInput}
                        onChange={(e) => setQuickIdInput(e.target.value)}
                        style={{
                          flex: 1,
                          border: "1px solid #cbd5e1",
                          borderRadius: "8px",
                          padding: "6px 8px",
                          fontSize: "0.78rem",
                          outline: "none",
                        }}
                      />
                      <button
                        type="submit"
                        className="btn-primary"
                        style={{ padding: "6px 10px", fontSize: "0.74rem" }}
                      >
                        Fetch
                      </button>
                    </div>
                  </form>

                  <div style={{ height: "1px", background: "#f1f5f9", margin: "4px 0" }} />

                  {/* Doctor Portal Sign In */}
                  <button
                    className="nav-item"
                    style={{ padding: "8px 10px", fontSize: "0.82rem" }}
                    onClick={() => {
                      setUserDropdownOpen(false);
                      onOpenDoctorLogin();
                    }}
                  >
                    <span>🩺 Doctor Workstation Sign In</span>
                  </button>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
