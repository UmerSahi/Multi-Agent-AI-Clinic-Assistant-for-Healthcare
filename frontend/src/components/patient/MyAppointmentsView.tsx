"use client";

import React, { useState } from "react";
import { Patient } from "@/types";

interface MyAppointmentsViewProps {
  appointments: any[];
  isLoading: boolean;
  currentPatient?: Patient | null;
  onSelectPatient?: (patientId: string) => void;
  onCancelAppointment: (appId: string) => void;
  onViewPrescription: (app: any) => void;
  onNavigateToSchedule: () => void;
}

export const MyAppointmentsView: React.FC<MyAppointmentsViewProps> = ({
  appointments,
  isLoading,
  currentPatient,
  onSelectPatient,
  onCancelAppointment,
  onViewPrescription,
  onNavigateToSchedule,
}) => {
  const [filterType, setFilterType] = useState<"all" | "prescriptions" | "upcoming">("all");
  const [searchPatientId, setSearchPatientId] = useState<string>("");

  const samplePatients = [
    { id: "p2", name: "Fatima Bibi", mrn: "CCC-PK-100002", icon: "🌸" },
    { id: "p1", name: "Ahmed Raza", mrn: "CCC-PK-100001", icon: "🩺" },
    { id: "p3", name: "Hamza Abbasi (Child)", mrn: "CCC-PK-100003", icon: "🧒" },
    { id: "p4", name: "Nazia Abbasi", mrn: "CCC-PK-100004", icon: "💊" },
    { id: "p5", name: "Tariq Mahmood", mrn: "CCC-PK-100005", icon: "🫀" },
  ];

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchPatientId.trim() && onSelectPatient) {
      onSelectPatient(searchPatientId.trim());
    }
  };

  const filteredAppointments = appointments.filter((app) => {
    const hasRx = !!app.has_prescription || !!app.prescription || !!app.prescription_id;
    const isCompleted = (app.status || "").toLowerCase() === "fulfilled" || (app.status || "").toLowerCase() === "completed";
    if (filterType === "prescriptions") {
      return hasRx || isCompleted;
    }
    if (filterType === "upcoming") {
      return !isCompleted && (app.status || "").toLowerCase() !== "cancelled";
    }
    return true;
  });

  const prescriptionsCount = appointments.filter((a) => !!a.has_prescription || !!a.prescription).length;
  const upcomingCount = appointments.filter((a) => (a.status || "").toLowerCase() === "booked" || (a.status || "").toLowerCase() === "confirmed").length;

  return (
    <div style={{ padding: "24px", overflowY: "auto", height: "100%", display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Header Banner */}
      <div
        style={{
          background: "linear-gradient(135deg, #ffffff 0%, #f0fdfa 100%)",
          border: "1px solid #ccfbf1",
          borderRadius: "20px",
          padding: "22px 24px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "16px",
          boxShadow: "0 4px 14px rgba(15, 118, 110, 0.05)",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ fontSize: "1.5rem" }}>📋</span>
            <h2 style={{ fontSize: "1.35rem", fontWeight: 800, color: "#0f172a" }}>
              My Appointments & Prescriptions
            </h2>
          </div>
          <p style={{ fontSize: "0.84rem", color: "#64748b", marginTop: "6px" }}>
            Instant access to confirmed bookings, previous outpatient visits, and downloadable official doctor prescriptions.
          </p>
        </div>

        <button
          className="btn-primary"
          onClick={onNavigateToSchedule}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            background: "#0f766e",
            color: "#ffffff",
            padding: "10px 18px",
            borderRadius: "12px",
            fontWeight: 700,
            fontSize: "0.85rem",
          }}
        >
          <span>+</span>
          <span>Book New Consultation</span>
        </button>
      </div>

      {/* Patient Switcher & Search Bar */}
      <div
        style={{
          background: "#ffffff",
          border: "1px solid #e2e8f0",
          borderRadius: "18px",
          padding: "16px 20px",
          display: "flex",
          flexDirection: "column",
          gap: "14px",
          boxShadow: "0 2px 8px rgba(0,0,0,0.02)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "0.82rem", fontWeight: 700, color: "#334155" }}>
            <span>👤</span>
            <span>Select Patient to View Records:</span>
          </div>

          {/* Quick Patient ID Search */}
          <form onSubmit={handleSearchSubmit} style={{ display: "flex", gap: "8px" }}>
            <input
              type="text"
              placeholder="Enter Patient ID (e.g. p2, p1, CCC-PK-100002)..."
              value={searchPatientId}
              onChange={(e) => setSearchPatientId(e.target.value)}
              style={{
                padding: "6px 12px",
                fontSize: "0.78rem",
                border: "1px solid #cbd5e1",
                borderRadius: "10px",
                width: "240px",
                outline: "none",
              }}
            />
            <button
              type="submit"
              className="btn-secondary"
              style={{ fontSize: "0.78rem", padding: "6px 12px", background: "#0f766e", color: "#ffffff" }}
            >
              Fetch Records
            </button>
          </form>
        </div>

        {/* Quick Sample Patient Buttons */}
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
          {samplePatients.map((sp) => {
            const isSelected = currentPatient?.patient_id === sp.id || currentPatient?.mrn === sp.mrn;
            return (
              <button
                key={sp.id}
                onClick={() => onSelectPatient && onSelectPatient(sp.id)}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "6px 12px",
                  borderRadius: "20px",
                  fontSize: "0.78rem",
                  fontWeight: 600,
                  border: isSelected ? "1.5px solid #0f766e" : "1px solid #e2e8f0",
                  background: isSelected ? "#f0fdfa" : "#f8fafc",
                  color: isSelected ? "#0f766e" : "#475569",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
              >
                <span>{sp.icon}</span>
                <span>{sp.name}</span>
                <span style={{ fontSize: "0.7rem", color: "#94a3b8", fontFamily: "var(--font-mono)" }}>
                  ({sp.id})
                </span>
              </button>
            );
          })}
        </div>

        {/* Active Patient Dossier Ribbon */}
        {currentPatient ? (
          <div
            style={{
              marginTop: "4px",
              padding: "10px 14px",
              background: "#f0fdf4",
              border: "1px solid #bbf7d0",
              borderRadius: "12px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "10px",
              fontSize: "0.8rem",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
              <span style={{ fontWeight: 700, color: "#166534" }}>
                Active Profile: {currentPatient.patient_name}
              </span>
              <span style={{ color: "#4b5563" }}>• MRN: <strong>{currentPatient.mrn || "N/A"}</strong></span>
              {currentPatient.phone && <span style={{ color: "#4b5563" }}>• Phone: <strong>{currentPatient.phone}</strong></span>}
            </div>

            <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
              {currentPatient.known_allergies && currentPatient.known_allergies.length > 0 && (
                <span style={{ background: "#fef2f2", color: "#b91c1c", padding: "2px 8px", borderRadius: "6px", fontSize: "0.72rem", fontWeight: 600 }}>
                  ⚠️ Allergy: {currentPatient.known_allergies.join(", ")}
                </span>
              )}
              {currentPatient.chronic_conditions && currentPatient.chronic_conditions.length > 0 && (
                <span style={{ background: "#eff6ff", color: "#1d4ed8", padding: "2px 8px", borderRadius: "6px", fontSize: "0.72rem", fontWeight: 600 }}>
                  Condition: {currentPatient.chronic_conditions.join(", ")}
                </span>
              )}
            </div>
          </div>
        ) : (
          <div
            style={{
              marginTop: "4px",
              padding: "10px 14px",
              background: "#f8fafc",
              border: "1px dashed #cbd5e1",
              borderRadius: "12px",
              display: "flex",
              alignItems: "center",
              gap: "10px",
              fontSize: "0.8rem",
              color: "#475569",
            }}
          >
            <span>👤</span>
            <span>
              <strong>Guest Patient Mode:</strong> Click any demo profile above (e.g. Fatima Bibi, Ahmed Raza) or enter your Patient ID / MRN to view past appointments and download doctor prescriptions.
            </span>
          </div>
        )}
      </div>

      {/* Filter Tabs Row */}
      <div style={{ display: "flex", gap: "10px", borderBottom: "1px solid #e2e8f0", paddingBottom: "8px" }}>
        <button
          onClick={() => setFilterType("all")}
          style={{
            padding: "8px 16px",
            borderRadius: "10px",
            fontSize: "0.82rem",
            fontWeight: 700,
            border: "none",
            background: filterType === "all" ? "#0f766e" : "transparent",
            color: filterType === "all" ? "#ffffff" : "#64748b",
            cursor: "pointer",
          }}
        >
          All Appointments ({appointments.length})
        </button>

        <button
          onClick={() => setFilterType("prescriptions")}
          style={{
            padding: "8px 16px",
            borderRadius: "10px",
            fontSize: "0.82rem",
            fontWeight: 700,
            border: "none",
            background: filterType === "prescriptions" ? "#059669" : "transparent",
            color: filterType === "prescriptions" ? "#ffffff" : "#64748b",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: "6px",
          }}
        >
          <span>💊</span>
          <span>Prescriptions & Fulfilled ({prescriptionsCount})</span>
        </button>

        <button
          onClick={() => setFilterType("upcoming")}
          style={{
            padding: "8px 16px",
            borderRadius: "10px",
            fontSize: "0.82rem",
            fontWeight: 700,
            border: "none",
            background: filterType === "upcoming" ? "#0284c7" : "transparent",
            color: filterType === "upcoming" ? "#ffffff" : "#64748b",
            cursor: "pointer",
          }}
        >
          Upcoming Bookings ({upcomingCount})
        </button>
      </div>

      {/* Appointments Grid */}
      {isLoading ? (
        <div style={{ textAlign: "center", padding: "60px 20px", color: "#64748b", background: "#ffffff", borderRadius: "18px", border: "1px solid #e2e8f0" }}>
          <div style={{ fontSize: "2rem", marginBottom: "8px" }}>⏳</div>
          <div style={{ fontWeight: 600 }}>Loading appointment records & prescriptions...</div>
        </div>
      ) : filteredAppointments.length === 0 ? (
        <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "20px", padding: "60px 20px", textAlign: "center" }}>
          <div style={{ fontSize: "2.5rem", marginBottom: "12px" }}>🗓️</div>
          <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#1e293b" }}>
            {!currentPatient ? "No Patient Profile Selected" : `No ${filterType === "prescriptions" ? "Prescriptions" : filterType === "upcoming" ? "Upcoming" : ""} Records Found`}
          </h3>
          <p style={{ fontSize: "0.82rem", color: "#64748b", maxWidth: "460px", margin: "8px auto 20px" }}>
            {!currentPatient
              ? "You are currently browsing as a Guest. Click any returning patient button above (e.g. Fatima Bibi, Ahmed Raza) or enter your Patient ID / MRN to view past appointments and download prescriptions."
              : filterType === "prescriptions"
              ? "No prescriptions found for this filter. Check all appointments or book a consultation."
              : "No appointments found for this profile. Select a patient above or book your next specialist appointment."}
          </p>
          <button className="btn-primary" onClick={onNavigateToSchedule}>
            Book Appointment Now
          </button>
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(360px, 1fr))", gap: "18px" }}>
          {filteredAppointments.map((app: any, idx: number) => {
            const isFulfilled = (app.status || "").toLowerCase() === "fulfilled" || (app.status || "").toLowerCase() === "completed";
            const isConfirmed = (app.status || "").toLowerCase() === "confirmed" || (app.status || "").toLowerCase() === "booked";
            const isCancelled = (app.status || "").toLowerCase() === "cancelled";
            const hasRx = !!app.has_prescription || !!app.prescription || !!app.prescription_id;
            const rx = app.prescription || {};
            const medicines = rx.medicines || rx.medications || [];
            const bookingRef = (app.booking_reference || app.booking_ref || app.id || "").replace("#", "").trim();
            const pdfUrl = `/api/prescriptions/${encodeURIComponent(bookingRef)}/pdf?download=true`;

            return (
              <div
                key={app.appointment_id || app.id || idx}
                style={{
                  background: "#ffffff",
                  border: hasRx ? "1.5px solid #a7f3d0" : "1px solid #e2e8f0",
                  borderRadius: "20px",
                  padding: "20px",
                  boxShadow: hasRx ? "0 4px 14px rgba(5, 150, 105, 0.06)" : "0 2px 8px rgba(0,0,0,0.03)",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  gap: "16px",
                  transition: "transform 0.15s ease, box-shadow 0.15s ease",
                }}
              >
                <div>
                  {/* Card Header: Ref & Status */}
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                      <span
                        style={{
                          fontSize: "0.75rem",
                          background: "#f1f5f9",
                          color: "#0f766e",
                          fontWeight: 800,
                          padding: "4px 9px",
                          borderRadius: "8px",
                          fontFamily: "var(--font-mono)",
                        }}
                      >
                        #{bookingRef}
                      </span>
                    </div>

                    <span
                      style={{
                        fontSize: "0.72rem",
                        fontWeight: 800,
                        padding: "3px 10px",
                        borderRadius: "20px",
                        background: isFulfilled ? "#ecfdf5" : isConfirmed ? "#eff6ff" : "#fff1f2",
                        color: isFulfilled ? "#047857" : isConfirmed ? "#1d4ed8" : "#be123c",
                        border: isFulfilled ? "1px solid #a7f3d0" : isConfirmed ? "1px solid #bfdbfe" : "1px solid #fecdd3",
                      }}
                    >
                      {isFulfilled ? "✓ FULFILLED" : isConfirmed ? "CONFIRMED" : "CANCELLED"}
                    </span>
                  </div>

                  {/* Doctor Info */}
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "10px" }}>
                    <div>
                      <h3 style={{ fontSize: "1.05rem", fontWeight: 800, color: "#0f172a" }}>
                        {app.doctor_name || "Specialist Physician"}
                      </h3>
                      <div style={{ fontSize: "0.82rem", color: "#0f766e", fontWeight: 700, marginTop: "2px" }}>
                        {app.specialty || app.doctor_specialty || "Clinical Specialist"}
                      </div>
                    </div>

                    {app.consultation_fee && (
                      <span style={{ fontSize: "0.76rem", background: "#f8fafc", color: "#475569", padding: "3px 8px", borderRadius: "6px", fontWeight: 700 }}>
                        PKR {app.consultation_fee.toLocaleString()}
                      </span>
                    )}
                  </div>

                  {/* Branch & Schedule Info */}
                  <div style={{ display: "flex", flexDirection: "column", gap: "6px", marginTop: "12px", fontSize: "0.78rem", color: "#475569" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                      <span>🏥</span>
                      <span>{app.branch_name || "City Care Clinics — DHA Lahore Branch"}</span>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
                        <span>📅</span>
                        <strong style={{ color: "#1e293b" }}>{app.display_date || app.date || "Scheduled Date"}</strong>
                      </div>
                      <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
                        <span>⏰</span>
                        <strong style={{ color: "#1e293b" }}>{app.display_time || app.time || app.time_slot}</strong>
                      </div>
                    </div>
                  </div>

                  {/* Reason for Visit */}
                  {app.reason_for_visit || app.reason ? (
                    <div
                      style={{
                        fontSize: "0.76rem",
                        color: "#475569",
                        marginTop: "10px",
                        background: "#f8fafc",
                        padding: "8px 12px",
                        borderRadius: "10px",
                        border: "1px solid #f1f5f9",
                      }}
                    >
                      <span style={{ fontWeight: 600, color: "#64748b" }}>Reason: </span>
                      {app.reason_for_visit || app.reason}
                    </div>
                  ) : null}

                  {/* PRESCRIPTION CALLOUT BLOCK */}
                  {hasRx && (
                    <div
                      style={{
                        marginTop: "14px",
                        background: "linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%)",
                        border: "1px solid #a7f3d0",
                        borderRadius: "14px",
                        padding: "14px",
                        display: "flex",
                        flexDirection: "column",
                        gap: "8px",
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.8rem", fontWeight: 800, color: "#065f46" }}>
                          <span>℞</span>
                          <span>Doctor Prescription Issued</span>
                        </div>
                        {rx.id && (
                          <span style={{ fontSize: "0.7rem", color: "#047857", fontWeight: 700, fontFamily: "var(--font-mono)" }}>
                            {rx.id}
                          </span>
                        )}
                      </div>

                      {rx.diagnosis && (
                        <div style={{ fontSize: "0.78rem", color: "#1e293b" }}>
                          <span style={{ fontWeight: 700, color: "#047857" }}>Diagnosis: </span>
                          <span>{rx.diagnosis}</span>
                        </div>
                      )}

                      {medicines.length > 0 && (
                        <div style={{ display: "flex", flexDirection: "column", gap: "4px", marginTop: "2px" }}>
                          <div style={{ fontSize: "0.72rem", color: "#475569", fontWeight: 700, textTransform: "uppercase" }}>
                            Prescribed Medications ({medicines.length}):
                          </div>
                          <div style={{ display: "flex", flexWrap: "wrap", gap: "4px" }}>
                            {medicines.map((m: any, mIdx: number) => (
                              <span
                                key={mIdx}
                                style={{
                                  fontSize: "0.72rem",
                                  background: "#ffffff",
                                  border: "1px solid #cbd5e1",
                                  color: "#0f172a",
                                  padding: "2px 8px",
                                  borderRadius: "6px",
                                  fontWeight: 600,
                                }}
                              >
                                💊 {m.medicine_name || m.drug_name || m.name} ({m.dosage})
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {rx.advice && (
                        <div style={{ fontSize: "0.72rem", color: "#047857", fontStyle: "italic", marginTop: "2px" }}>
                          "{rx.advice}"
                        </div>
                      )}
                    </div>
                  )}

                  {!hasRx && !isCancelled && (
                    <div
                      style={{
                        marginTop: "12px",
                        background: "#f8fafc",
                        border: "1px dashed #cbd5e1",
                        borderRadius: "10px",
                        padding: "8px 12px",
                        fontSize: "0.74rem",
                        color: "#64748b",
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                      }}
                    >
                      <span>⏳</span>
                      <span>Consultation pending — prescription will be issued after visit.</span>
                    </div>
                  )}
                </div>

                {/* Card Action Buttons */}
                <div style={{ display: "flex", flexDirection: "column", gap: "8px", borderTop: "1px solid #f1f5f9", paddingTop: "14px" }}>
                  {hasRx && (
                    <div style={{ display: "flex", gap: "8px" }}>
                      <button
                        className="btn-primary"
                        style={{
                          flex: 1,
                          padding: "8px 12px",
                          fontSize: "0.78rem",
                          background: "#059669",
                          color: "#ffffff",
                          display: "inline-flex",
                          alignItems: "center",
                          justifyContent: "center",
                          gap: "6px",
                          borderRadius: "10px",
                          fontWeight: 700,
                        }}
                        onClick={() => onViewPrescription(app)}
                      >
                        <span>📄</span>
                        <span>View Rx Details</span>
                      </button>

                      <a
                        href={pdfUrl}
                        download={`CityCare_Prescription_${bookingRef}.pdf`}
                        target="_blank"
                        rel="noreferrer"
                        className="btn-secondary"
                        style={{
                          padding: "8px 14px",
                          fontSize: "0.78rem",
                          background: "#0f766e",
                          color: "#ffffff",
                          textDecoration: "none",
                          display: "inline-flex",
                          alignItems: "center",
                          justifyContent: "center",
                          gap: "6px",
                          borderRadius: "10px",
                          fontWeight: 700,
                        }}
                        title="Download official PDF prescription"
                      >
                        <span>📥</span>
                        <span>Download PDF</span>
                      </a>
                    </div>
                  )}

                  <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                    {app.google_calendar_url && (
                      <a
                        href={app.google_calendar_url}
                        target="_blank"
                        rel="noreferrer"
                        className="btn-secondary"
                        style={{
                          flex: 1,
                          padding: "7px 10px",
                          fontSize: "0.74rem",
                          textDecoration: "none",
                          textAlign: "center",
                          borderRadius: "8px",
                          color: "#334155",
                          border: "1px solid #cbd5e1",
                        }}
                      >
                        📅 Add to Calendar
                      </a>
                    )}

                    {isConfirmed && (
                      <button
                        className="btn-secondary"
                        style={{
                          padding: "7px 12px",
                          fontSize: "0.74rem",
                          color: "#e11d48",
                          border: "1px solid #fecdd3",
                          borderRadius: "8px",
                          cursor: "pointer",
                        }}
                        onClick={() => onCancelAppointment(app.appointment_id || app.id)}
                      >
                        Cancel
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
