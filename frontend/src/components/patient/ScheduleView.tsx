"use client";

import React from "react";
import { DoctorDirectoryItem, DoctorScheduleData } from "@/types";

interface ScheduleViewProps {
  doctorsList: DoctorDirectoryItem[];
  selectedDoctorId: string;
  setSelectedDoctorId: (id: string) => void;
  selectedScheduleDate: string;
  setSelectedScheduleDate: (date: string) => void;
  doctorSchedule: DoctorScheduleData | null;
  scheduleLoading: boolean;
  selectedSpecialtyFilter: string;
  setSelectedSpecialtyFilter: (s: string) => void;
  onSelectSlotToBook: (slot: any, doctor: DoctorDirectoryItem) => void;
  onFetchSchedule: (doctorId: string, date: string) => void;
}

export const ScheduleView: React.FC<ScheduleViewProps> = ({
  doctorsList,
  selectedDoctorId,
  setSelectedDoctorId,
  selectedScheduleDate,
  setSelectedScheduleDate,
  doctorSchedule,
  scheduleLoading,
  selectedSpecialtyFilter,
  setSelectedSpecialtyFilter,
  onSelectSlotToBook,
  onFetchSchedule,
}) => {
  // Extract unique specialties
  const specialties: string[] = ["ALL", ...(Array.from(new Set(doctorsList.map((d) => d.specialty).filter(Boolean))) as string[])];

  // Filter doctors by selected specialty
  const filteredDoctors = doctorsList.filter((doc) => {
    if (selectedSpecialtyFilter === "ALL") return true;
    return doc.specialty?.toLowerCase() === selectedSpecialtyFilter.toLowerCase();
  });

  const selectedDoctor =
    doctorsList.find((d) => (d.id || d.doctor_id) === selectedDoctorId) ||
    filteredDoctors[0] ||
    doctorsList[0];

  const handleDoctorDropdownChange = (docId: string) => {
    setSelectedDoctorId(docId);
    onFetchSchedule(docId, selectedScheduleDate);
  };

  const handleSpecialtyFilterClick = (spec: string) => {
    setSelectedSpecialtyFilter(spec);
    const matching = doctorsList.filter((d) => spec === "ALL" || d.specialty?.toLowerCase() === spec.toLowerCase());
    if (matching.length > 0) {
      const firstId = matching[0].id || matching[0].doctor_id || "";
      setSelectedDoctorId(firstId);
      onFetchSchedule(firstId, selectedScheduleDate);
    }
  };

  return (
    <div style={{ padding: "24px", overflowY: "auto", height: "100%", display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Top Banner & Comprehensive Controls Bar */}
      <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "20px", padding: "22px", boxShadow: "0 2px 8px rgba(0,0,0,0.03)" }}>
        {/* Title & Date Picker Row */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "14px" }}>
          <div>
            <h2 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#0f172a", display: "flex", alignItems: "center", gap: "8px" }}>
              <span>📅</span> Doctor Upcoming Schedules & Slot Booking
            </h2>
            <p style={{ fontSize: "0.82rem", color: "#64748b", marginTop: "4px" }}>
              Choose a specialist from the dropdown or filters below to view live appointment slots.
            </p>
          </div>

          {/* Consultation Date Picker */}
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <label style={{ fontSize: "0.82rem", fontWeight: 700, color: "#334155" }}>Consultation Date:</label>
            <input
              type="date"
              className="form-input"
              style={{ width: "auto", padding: "8px 14px", fontSize: "0.84rem", fontWeight: 600, borderColor: "#cbd5e1" }}
              value={selectedScheduleDate}
              onChange={(e) => {
                setSelectedScheduleDate(e.target.value);
                if (selectedDoctorId) onFetchSchedule(selectedDoctorId, e.target.value);
              }}
            />
          </div>
        </div>

        {/* 1. Specialty Filter Pills (Kept directly above as requested) */}
        <div style={{ marginTop: "18px" }}>
          <div style={{ fontSize: "0.74rem", fontWeight: 700, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "8px" }}>
            Filter by Clinical Specialty:
          </div>
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            {specialties.map((spec) => (
              <button
                key={spec}
                onClick={() => handleSpecialtyFilterClick(spec)}
                style={{
                  background: selectedSpecialtyFilter === spec ? "#0f766e" : "#f1f5f9",
                  color: selectedSpecialtyFilter === spec ? "#ffffff" : "#475569",
                  border: "none",
                  borderRadius: "20px",
                  padding: "7px 16px",
                  fontSize: "0.8rem",
                  fontWeight: 600,
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                  boxShadow: selectedSpecialtyFilter === spec ? "0 2px 8px rgba(15, 118, 110, 0.25)" : "none",
                }}
              >
                {spec}
              </button>
            ))}
          </div>
        </div>

        {/* 2. Doctor Dropdown Selector (New Prominent Dropdown) */}
        <div
          style={{
            marginTop: "16px",
            paddingTop: "16px",
            borderTop: "1px solid #f1f5f9",
            display: "flex",
            alignItems: "center",
            gap: "14px",
            flexWrap: "wrap",
            background: "#f0fdf9",
            padding: "14px 18px",
            borderRadius: "16px",
            border: "1px solid #ccfbf1",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px", minWidth: "150px" }}>
            <span style={{ fontSize: "1.3rem" }}>🩺</span>
            <div>
              <div style={{ fontSize: "0.85rem", fontWeight: 800, color: "#065f46" }}>Select Doctor:</div>
              <div style={{ fontSize: "0.72rem", color: "#047857" }}>Quick Dropdown Picker</div>
            </div>
          </div>

          {/* Styled Select Dropdown */}
          <div style={{ flex: 1, minWidth: "300px" }}>
            <select
              className="form-input"
              value={selectedDoctor ? (selectedDoctor.id || selectedDoctor.doctor_id) : ""}
              onChange={(e) => handleDoctorDropdownChange(e.target.value)}
              style={{
                width: "100%",
                padding: "10px 16px",
                fontSize: "0.9rem",
                fontWeight: 700,
                color: "#0f172a",
                background: "#ffffff",
                border: "2px solid #0f766e",
                borderRadius: "12px",
                cursor: "pointer",
                boxShadow: "0 2px 8px rgba(15, 118, 110, 0.1)",
              }}
            >
              {filteredDoctors.map((doc, idx) => {
                const docId = doc.id || doc.doctor_id || `doc_${idx}`;
                return (
                  <option key={docId} value={docId}>
                    {doc.full_name || doc.doctor_name} — {doc.specialty} ({doc.branch_name || "City Care"}) • PKR {doc.consultation_fee?.toLocaleString()}
                  </option>
                );
              })}
            </select>
          </div>

          <div style={{ fontSize: "0.78rem", color: "#065f46", fontWeight: 600 }}>
            Showing <strong>{filteredDoctors.length}</strong> available {selectedSpecialtyFilter === "ALL" ? "doctors" : `${selectedSpecialtyFilter} specialists`}
          </div>
        </div>
      </div>

      {/* Main Grid: Selected Doctor Details (Left) + Available Slot Booking (Right) */}
      <div style={{ display: "grid", gridTemplateColumns: "1.05fr 1.35fr", gap: "20px", alignItems: "start" }}>
        {/* Left Column: Selected Doctor Details Card */}
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {selectedDoctor && (
            <div
              style={{
                background: "#ffffff",
                border: "2px solid #0f766e",
                borderRadius: "20px",
                padding: "22px",
                boxShadow: "0 4px 16px rgba(15, 118, 110, 0.08)",
                position: "relative",
              }}
            >
              <div style={{ position: "absolute", top: "18px", right: "18px", textAlign: "right" }}>
                <div style={{ fontSize: "1.1rem", fontWeight: 800, color: "#059669" }}>
                  PKR {selectedDoctor.consultation_fee?.toLocaleString()}
                </div>
                <span style={{ fontSize: "0.68rem", color: "#64748b" }}>Consultation Fee</span>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "14px", marginBottom: "14px" }}>
                <div
                  style={{
                    width: "52px",
                    height: "52px",
                    borderRadius: "16px",
                    background: "linear-gradient(135deg, #0d9488, #0284c7)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "#ffffff",
                    fontSize: "1.5rem",
                    boxShadow: "0 4px 12px rgba(13, 148, 136, 0.3)",
                  }}
                >
                  🩺
                </div>
                <div>
                  <h3 style={{ fontSize: "1.15rem", fontWeight: 800, color: "#0f172a" }}>
                    {selectedDoctor.full_name || selectedDoctor.doctor_name}
                  </h3>
                  <div style={{ fontSize: "0.85rem", color: "#0f766e", fontWeight: 700 }}>
                    {selectedDoctor.specialty} Specialist
                  </div>
                </div>
              </div>

              <div style={{ background: "#f8fafc", borderRadius: "12px", padding: "14px", display: "flex", flexDirection: "column", gap: "8px", fontSize: "0.8rem", color: "#334155" }}>
                <div>
                  <strong>Qualification:</strong> {selectedDoctor.qualification}
                </div>
                <div>
                  <strong>Experience:</strong> {selectedDoctor.experience_years || 10} Years Clinical Practice
                </div>
                <div>
                  <strong>Clinic Branch:</strong> {selectedDoctor.branch_name || "City Care Clinics"}
                </div>
                <div>
                  <strong>PMDC Registration:</strong> {selectedDoctor.pmdc_number || "Verified Specialist"}
                </div>
              </div>

              {selectedDoctor.languages && selectedDoctor.languages.length > 0 && (
                <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", marginTop: "14px" }}>
                  {selectedDoctor.languages.map((lang) => (
                    <span key={lang} style={{ background: "#ecfdf5", color: "#065f46", fontSize: "0.72rem", fontWeight: 600, padding: "3px 10px", borderRadius: "10px" }}>
                      🗣️ {lang}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Column: Available Slots Grid */}
        <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "20px", padding: "22px", boxShadow: "0 2px 8px rgba(0,0,0,0.03)" }}>
          {selectedDoctor ? (
            <div>
              {/* Slot Header */}
              <div style={{ borderBottom: "1px solid #f1f5f9", paddingBottom: "14px", marginBottom: "16px", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px" }}>
                <div>
                  <h3 style={{ fontSize: "1.1rem", fontWeight: 800, color: "#0f172a" }}>
                    Available Consultation Slots
                  </h3>
                  <div style={{ fontSize: "0.8rem", color: "#0f766e", fontWeight: 600, marginTop: "2px" }}>
                    Dr. {selectedDoctor.full_name || selectedDoctor.doctor_name} • 📅 {selectedScheduleDate}
                  </div>
                </div>

                <div style={{ background: "#ecfdf5", border: "1px solid #a7f3d0", padding: "4px 10px", borderRadius: "10px", fontSize: "0.76rem", color: "#047857", fontWeight: 700 }}>
                  {doctorSchedule?.total_available || 0} Open Slots
                </div>
              </div>

              {scheduleLoading ? (
                <div style={{ textAlign: "center", padding: "50px 20px", color: "#64748b" }}>
                  <div style={{ fontSize: "2rem", marginBottom: "8px" }}>⏳</div>
                  <div style={{ fontWeight: 600 }}>Loading live doctor schedule...</div>
                </div>
              ) : doctorSchedule && doctorSchedule.available_slots && doctorSchedule.available_slots.length > 0 ? (
                <div>
                  <p style={{ fontSize: "0.82rem", color: "#64748b", marginBottom: "14px" }}>
                    Click any open time slot to confirm your booking:
                  </p>

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(135px, 1fr))", gap: "12px" }}>
                    {doctorSchedule.available_slots.map((slot: any, idx: number) => {
                      // Correctly resolve display_time from API payload
                      const timeStr =
                        typeof slot === "string"
                          ? slot
                          : slot.display_time ||
                            slot.time ||
                            (slot.slot_start ? slot.slot_start.slice(11, 16) : `Slot ${idx + 1}`);

                      return (
                        <button
                          key={idx}
                          type="button"
                          onClick={() => onSelectSlotToBook(slot, selectedDoctor)}
                          style={{
                            background: "#f0fdf9",
                            border: "1px solid #a7f3d0",
                            borderRadius: "14px",
                            padding: "12px 10px",
                            cursor: "pointer",
                            transition: "all 0.18s ease",
                            display: "flex",
                            flexDirection: "column",
                            alignItems: "center",
                            gap: "6px",
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background = "#ccfbf1";
                            e.currentTarget.style.borderColor = "#0f766e";
                            e.currentTarget.style.transform = "translateY(-2px)";
                            e.currentTarget.style.boxShadow = "0 4px 12px rgba(15, 118, 110, 0.15)";
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.background = "#f0fdf9";
                            e.currentTarget.style.borderColor = "#a7f3d0";
                            e.currentTarget.style.transform = "none";
                            e.currentTarget.style.boxShadow = "none";
                          }}
                        >
                          <span style={{ fontSize: "0.95rem", fontWeight: 800, color: "#065f46" }}>
                            {timeStr}
                          </span>
                          <span
                            style={{
                              fontSize: "0.72rem",
                              fontWeight: 700,
                              color: "#059669",
                              background: "#d1fae5",
                              padding: "2px 8px",
                              borderRadius: "6px",
                            }}
                          >
                            Book Slot ➔
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              ) : (
                <div style={{ textAlign: "center", padding: "50px 20px" }}>
                  <div style={{ fontSize: "2.5rem", marginBottom: "10px" }}>🗓️</div>
                  <h4 style={{ fontWeight: 700, color: "#1e293b", fontSize: "1rem" }}>
                    No Open Slots for Selected Date
                  </h4>
                  <p style={{ fontSize: "0.82rem", color: "#64748b", maxWidth: "380px", margin: "6px auto 16px" }}>
                    Dr. {selectedDoctor.full_name || selectedDoctor.doctor_name} has no available slots on {selectedScheduleDate}.
                  </p>

                  {/* Suggest alternatives if provided by backend */}
                  {doctorSchedule?.suggested_alternatives && doctorSchedule.suggested_alternatives.length > 0 && (
                    <div style={{ background: "#f0fdf9", border: "1px solid #ccfbf1", borderRadius: "14px", padding: "16px", marginTop: "14px", textAlign: "left" }}>
                      <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "#065f46", marginBottom: "8px" }}>
                        ✨ Suggested Alternative Slots:
                      </div>
                      <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                        {doctorSchedule.suggested_alternatives.map((alt: any, i: number) => (
                          <button
                            key={i}
                            className="btn-primary"
                            style={{ padding: "6px 12px", fontSize: "0.76rem" }}
                            onClick={() => onSelectSlotToBook(alt, selectedDoctor)}
                          >
                            {alt.display_date || alt.date}: {alt.display_time || alt.time}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div style={{ textAlign: "center", padding: "50px 20px", color: "#64748b" }}>
              Select a doctor from the dropdown above to view availability.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
