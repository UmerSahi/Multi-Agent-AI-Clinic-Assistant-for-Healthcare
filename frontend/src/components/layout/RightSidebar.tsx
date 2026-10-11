"use client";

import React from "react";
import { ActiveTab, PatientSubTab } from "@/types";

interface RightSidebarProps {
  setActiveTab: (tab: ActiveTab) => void;
  setPatientSubTab: (tab: PatientSubTab) => void;
  onSendPresetMessage?: (msg: string) => void;
}

export const RightSidebar: React.FC<RightSidebarProps> = ({
  setActiveTab,
  setPatientSubTab,
  onSendPresetMessage,
}) => {
  return (
    <aside className="right-support-sidebar">
      {/* Hero Header Card */}
      <div className="right-support-hero-card">
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "2px" }}>
          <div
            style={{
              width: "32px",
              height: "32px",
              borderRadius: "10px",
              background: "linear-gradient(135deg, #0d9488 0%, #0284c7 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#ffffff",
              boxShadow: "0 2px 8px rgba(13, 148, 136, 0.25)",
            }}
          >
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" />
            </svg>
          </div>
          <h3 style={{ fontSize: "0.95rem", fontWeight: 700, color: "#0f172a" }}>
            Quick & Easy Healthcare Support
          </h3>
        </div>
        <p style={{ fontSize: "0.78rem", color: "#64748b", lineHeight: 1.45 }}>
          Get instant answers, book appointments, manage your health — all in one place.
        </p>
      </div>

      {/* 4 Action Cards */}
      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        {/* Action 1: Ask Health Questions */}
        <div
          className="right-support-action-item"
          onClick={() => {
            setActiveTab("patient");
            setPatientSubTab("chat");
          }}
        >
          <div className="support-icon-badge" style={{ background: "#ecfdf5", color: "#059669" }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "#0f172a" }}>
              Ask Health Questions
            </div>
            <div style={{ fontSize: "0.72rem", color: "#64748b", marginTop: "1px" }}>
              Get trusted, instant answers
            </div>
          </div>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </div>

        {/* Action 2: Book Appointments */}
        <div
          className="right-support-action-item"
          onClick={() => {
            setActiveTab("patient");
            setPatientSubTab("schedule");
          }}
        >
          <div className="support-icon-badge" style={{ background: "#f0fdf4", color: "#0d9488" }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
              <line x1="16" y1="2" x2="16" y2="6" />
              <line x1="8" y1="2" x2="8" y2="6" />
              <line x1="3" y1="10" x2="21" y2="10" />
            </svg>
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "#0f172a" }}>
              Book Appointments
            </div>
            <div style={{ fontSize: "0.72rem", color: "#64748b", marginTop: "1px" }}>
              With your preferred doctor
            </div>
          </div>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </div>

        {/* Action 3: Access Records */}
        <div
          className="right-support-action-item"
          onClick={() => {
            setActiveTab("patient");
            setPatientSubTab("my_appointments");
          }}
        >
          <div className="support-icon-badge" style={{ background: "#faf5ff", color: "#7e22ce" }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
            </svg>
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "#0f172a" }}>
              Access Records
            </div>
            <div style={{ fontSize: "0.72rem", color: "#64748b", marginTop: "1px" }}>
              View your medical history
            </div>
          </div>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </div>

        {/* Action 4: Refill Prescriptions */}
        <div
          className="right-support-action-item"
          onClick={() => {
            if (onSendPresetMessage) {
              onSendPresetMessage("I need to check my prescriptions and request a medication refill.");
            } else {
              setActiveTab("patient");
              setPatientSubTab("my_appointments");
            }
          }}
        >
          <div className="support-icon-badge" style={{ background: "#fff7ed", color: "#ea580c" }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z" />
              <line x1="8.5" y1="8.5" x2="15.5" y2="15.5" />
            </svg>
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "#0f172a" }}>
              Refill Prescriptions
            </div>
            <div style={{ fontSize: "0.72rem", color: "#64748b", marginTop: "1px" }}>
              Stay on track with your medication
            </div>
          </div>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </div>
      </div>

      {/* Need to speak with a doctor CTA */}
      <div className="right-doctor-cta-card">
        <div style={{ display: "flex", gap: "12px", alignItems: "flex-start" }}>
          <div
            style={{
              width: "44px",
              height: "44px",
              borderRadius: "12px",
              background: "#ccfbf1",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#0f766e",
              flexShrink: 0,
            }}
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6V4a2 2 0 0 0-2-2h-1a.2.2 0 1 0 .3.3" />
              <path d="M8 15v1a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6v-4" />
              <circle cx="20" cy="10" r="2" />
            </svg>
          </div>
          <div>
            <div style={{ fontSize: "0.88rem", fontWeight: 700, color: "#0f172a", lineHeight: 1.2 }}>
              Need to speak with a doctor?
            </div>
            <div style={{ fontSize: "0.75rem", color: "#64748b", marginTop: "4px", lineHeight: 1.4 }}>
              Book a consultation with your trusted healthcare provider.
            </div>
          </div>
        </div>

        <button
          className="cta-appointment-btn"
          onClick={() => {
            setActiveTab("patient");
            setPatientSubTab("schedule");
          }}
        >
          <span>Book Appointment</span>
          <span>→</span>
        </button>
      </div>

      {/* Slogan Footer */}
      <div style={{ marginTop: "auto", textAlign: "center", display: "flex", alignItems: "center", justifyContent: "center", gap: "8px", fontSize: "0.76rem", color: "#64748b" }}>
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#0284c7" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" />
        </svg>
        <span>Better health. A brighter tomorrow.</span>
      </div>
    </aside>
  );
};
