"use client";

import React, { useRef, useEffect } from "react";
import { Message, Patient } from "@/types";

interface ChatViewProps {
  messages: Message[];
  inputMessage: string;
  setInputMessage: (val: string) => void;
  onSendMessage: (textToSend?: string) => void;
  isLoading: boolean;
  language: "Urdu" | "English";
  patientUser: Patient | null;
  onFetchPatientById: (id: string) => void;
  onNavigateToSchedule: () => void;
  onNavigateToRecords: () => void;
  onFileUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  labLoading: boolean;
  restoreInputRef: string;
  setRestoreInputRef: (val: string) => void;
  onRestoreAppointment: (ref: string) => void;
  restoreLoading: boolean;
}

export const ChatView: React.FC<ChatViewProps> = ({
  messages,
  inputMessage,
  setInputMessage,
  onSendMessage,
  isLoading,
  language,
  patientUser,
  onFetchPatientById,
  onNavigateToSchedule,
  onNavigateToRecords,
  onFileUpload,
  labLoading,
  restoreInputRef,
  setRestoreInputRef,
  onRestoreAppointment,
  restoreLoading,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const renderFormattedContent = (text: string) => {
    if (!text) return null;
    const lines = text.split("\n");

    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
        {lines.map((rawLine, idx) => {
          if (!rawLine.trim()) return <div key={idx} style={{ height: "4px" }} />;

          let isBullet = false;
          let content = rawLine;
          if (rawLine.trim().startsWith("• ") || rawLine.trim().startsWith("- ") || rawLine.trim().startsWith("* ")) {
            isBullet = true;
            content = rawLine.trim().replace(/^([•\-\*]\s+)/, "");
          }

          // Parse **bold** and `code`
          const tokenRegex = /(\*\*([^*]+)\*\*|`([^`]+)`)/g;
          const elements: React.ReactNode[] = [];
          let lastIndex = 0;
          let match: RegExpExecArray | null;
          let key = 0;

          while ((match = tokenRegex.exec(content)) !== null) {
            if (match.index > lastIndex) {
              elements.push(<span key={`t-${key++}`}>{content.substring(lastIndex, match.index)}</span>);
            }
            if (match[2]) {
              elements.push(<strong key={`b-${key++}`} style={{ fontWeight: 700, color: "#0f172a" }}>{match[2]}</strong>);
            } else if (match[3]) {
              elements.push(
                <code key={`c-${key++}`} style={{ background: "#f1f5f9", color: "#0f766e", padding: "1px 5px", borderRadius: "4px", fontSize: "0.85em", fontFamily: "var(--font-mono)" }}>
                  {match[3]}
                </code>
              );
            }
            lastIndex = match.index + match[0].length;
          }

          if (lastIndex < content.length) {
            elements.push(<span key={`rem-${key++}`}>{content.substring(lastIndex)}</span>);
          }

          if (isBullet) {
            return (
              <div key={idx} style={{ display: "flex", alignItems: "flex-start", gap: "8px", paddingLeft: "4px" }}>
                <span style={{ color: "#0d9488", fontWeight: "bold" }}>•</span>
                <div style={{ flex: 1, lineHeight: "1.5" }}>{elements}</div>
              </div>
            );
          }

          return <div key={idx} style={{ lineHeight: "1.5" }}>{elements}</div>;
        })}
      </div>
    );
  };

  const getAgentLabel = (rawAgent?: string) => {
    if (!rawAgent) return null;
    if (rawAgent.includes("emergency")) return <span style={{ background: "#fee2e2", color: "#b91c1c", fontSize: "0.68rem", fontWeight: 700, padding: "2px 6px", borderRadius: "4px" }}>Emergency</span>;
    if (rawAgent.includes("triage")) return <span style={{ background: "#fef3c7", color: "#b45309", fontSize: "0.68rem", fontWeight: 700, padding: "2px 6px", borderRadius: "4px" }}>Clinical Triage</span>;
    if (rawAgent.includes("prescription")) return <span style={{ background: "#ede9fe", color: "#6d28d9", fontSize: "0.68rem", fontWeight: 700, padding: "2px 6px", borderRadius: "4px" }}>Rx Safety</span>;
    if (rawAgent.includes("MemoryManager") || rawAgent.includes("returning")) return <span style={{ background: "#ccfbf1", color: "#0f766e", fontSize: "0.68rem", fontWeight: 700, padding: "2px 6px", borderRadius: "4px" }}>Memory Manager</span>;
    return null;
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", position: "relative" }}>
      {/* Messages Scroll Area */}
      <div className="chat-scroll-area">
        {/* Assistant Welcome Card */}
        <div className="message-row assistant">
          <div className="message-avatar">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" />
            </svg>
          </div>
          <div className="message-bubble assistant" style={{ maxWidth: "580px" }}>
            <div style={{ fontWeight: 700, color: "#0f172a", marginBottom: "4px" }}>
              {patientUser ? `Welcome back, ${patientUser.patient_name}!` : "Hello! Welcome to City Care Clinics"}
            </div>

            {patientUser ? (
              <div style={{ color: "#334155", fontSize: "0.88rem", lineHeight: "1.55" }}>
                I have retrieved your medical history from the database (Patient ID: <strong>{patientUser.patient_id}</strong>, MRN: <strong>{patientUser.mrn}</strong>).
                {patientUser.known_allergies && patientUser.known_allergies.length > 0 && (
                  <div style={{ marginTop: "4px", fontSize: "0.8rem", color: "#b91c1c" }}>
                    ⚠️ Recorded Allergies: {patientUser.known_allergies.join(", ")}
                  </div>
                )}
                <div style={{ marginTop: "4px" }}>
                  How are you feeling today? You can ask medical questions, book an appointment, or review past prescriptions.
                </div>
              </div>
            ) : (
              <div style={{ color: "#334155", fontSize: "0.88rem", lineHeight: "1.55" }}>
                {language === "Urdu" ? (
                  <>
                    <div>Main aapka City Care Assistant hoon. Main appointments, medical mashwaray, prescriptions aur lab results mein aapki madad kar sakta hoon.</div>
                    <div style={{ background: "#f0fdf9", border: "1px solid #ccfbf1", borderRadius: "10px", padding: "10px 12px", margin: "8px 0" }}>
                      <strong style={{ color: "#0f766e" }}>• Returning Patient?</strong> Apna Patient ID (maslan <code>p1</code>, <code>p2</code> ya MRN) likhein taake main aapka pichla medical record database se fetch kar sakoon.
                    </div>
                    <div>• <strong>New Patient?</strong> Seedha apna masla, alamaat ya sawal likhein!</div>
                  </>
                ) : (
                  <>
                    <div>I'm your City Care Assistant. I can help you with medical queries, appointments, prescriptions, and lab report explanations.</div>
                    <div style={{ background: "#f0fdf9", border: "1px solid #ccfbf1", borderRadius: "10px", padding: "10px 12px", margin: "8px 0" }}>
                      <strong style={{ color: "#0f766e" }}>• Returning Patient?</strong> Simply provide your Patient ID or MRN (e.g., <code>p1</code>, <code>p2</code>, or <code>CCC-PK-100001</code>) so I can fetch your previous medical record from the database.
                    </div>
                    <div>• <strong>New Patient?</strong> Simply type your symptoms or question below to begin!</div>
                  </>
                )}

                {/* Quick One-Click Demo Patient ID Chips */}
                <div style={{ marginTop: "10px", paddingTop: "8px", borderTop: "1px solid #f1f5f9" }}>
                  <div style={{ fontSize: "0.74rem", fontWeight: 700, color: "#64748b", marginBottom: "6px" }}>
                    ⚡ Returning Patient Demo Records (Click to Fetch):
                  </div>
                  <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                    <button
                      type="button"
                      onClick={() => onFetchPatientById("p1")}
                      style={{ background: "#ecfdf5", border: "1px solid #a7f3d0", color: "#047857", borderRadius: "8px", padding: "4px 8px", fontSize: "0.74rem", fontWeight: 600, cursor: "pointer" }}
                    >
                      p1 (Ahmed Raza)
                    </button>
                    <button
                      type="button"
                      onClick={() => onFetchPatientById("p2")}
                      style={{ background: "#eff6ff", border: "1px solid #bfdbfe", color: "#1d4ed8", borderRadius: "8px", padding: "4px 8px", fontSize: "0.74rem", fontWeight: 600, cursor: "pointer" }}
                    >
                      p2 (Fatima Bibi)
                    </button>
                    <button
                      type="button"
                      onClick={() => onFetchPatientById("p3")}
                      style={{ background: "#faf5ff", border: "1px solid #e9d5ff", color: "#7e22ce", borderRadius: "8px", padding: "4px 8px", fontSize: "0.74rem", fontWeight: 600, cursor: "pointer" }}
                    >
                      p3 (Hamza Abbasi)
                    </button>
                  </div>
                </div>
              </div>
            )}

            <div className="message-timestamp">10:24 AM</div>

            {/* 2x2 Quick Action Cards Grid (MATCHING SCREENSHOT) */}
            <div className="quick-action-grid">
              {/* Card 1: Book Appointment */}
              <div
                className="quick-action-card mint"
                onClick={onNavigateToSchedule}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <div style={{ width: "32px", height: "32px", borderRadius: "8px", background: "rgba(16, 185, 129, 0.2)", display: "flex", alignItems: "center", justifyContent: "center", color: "#059669" }}>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                      <line x1="16" y1="2" x2="16" y2="6" />
                      <line x1="8" y1="2" x2="8" y2="6" />
                      <line x1="3" y1="10" x2="21" y2="10" />
                    </svg>
                  </div>
                  <div>
                    <div style={{ fontSize: "0.84rem", fontWeight: 700, color: "#065f46" }}>Book Appointment</div>
                    <div style={{ fontSize: "0.72rem", color: "#047857" }}>Schedule a visit with a doctor</div>
                  </div>
                </div>
                <span style={{ color: "#059669", fontSize: "0.9rem" }}>›</span>
              </div>

              {/* Card 2: Find a Doctor */}
              <div
                className="quick-action-card peach"
                onClick={onNavigateToSchedule}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <div style={{ width: "32px", height: "32px", borderRadius: "8px", background: "rgba(234, 88, 12, 0.18)", display: "flex", alignItems: "center", justifyContent: "center", color: "#ea580c" }}>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
                      <circle cx="9" cy="7" r="4" />
                      <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
                      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
                    </svg>
                  </div>
                  <div>
                    <div style={{ fontSize: "0.84rem", fontWeight: 700, color: "#9a3412" }}>Find a Doctor</div>
                    <div style={{ fontSize: "0.72rem", color: "#c2410c" }}>Search by specialty or name</div>
                  </div>
                </div>
                <span style={{ color: "#ea580c", fontSize: "0.9rem" }}>›</span>
              </div>

              {/* Card 3: My Medical Records */}
              <div
                className="quick-action-card purple"
                onClick={onNavigateToRecords}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <div style={{ width: "32px", height: "32px", borderRadius: "8px", background: "rgba(126, 34, 206, 0.18)", display: "flex", alignItems: "center", justifyContent: "center", color: "#7e22ce" }}>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      <polyline points="14 2 14 8 20 8" />
                    </svg>
                  </div>
                  <div>
                    <div style={{ fontSize: "0.84rem", fontWeight: 700, color: "#6b21a8" }}>My Medical Records</div>
                    <div style={{ fontSize: "0.72rem", color: "#7e22ce" }}>View your health history</div>
                  </div>
                </div>
                <span style={{ color: "#7e22ce", fontSize: "0.9rem" }}>›</span>
              </div>

              {/* Card 4: Medication */}
              <div
                className="quick-action-card cyan"
                onClick={() => onSendMessage("I need information regarding my prescriptions and medications.")}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <div style={{ width: "32px", height: "32px", borderRadius: "8px", background: "rgba(2, 132, 199, 0.18)", display: "flex", alignItems: "center", justifyContent: "center", color: "#0284c7" }}>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z" />
                      <line x1="8.5" y1="8.5" x2="15.5" y2="15.5" />
                    </svg>
                  </div>
                  <div>
                    <div style={{ fontSize: "0.84rem", fontWeight: 700, color: "#0369a1" }}>Medication</div>
                    <div style={{ fontSize: "0.72rem", color: "#0284c7" }}>Check prescriptions & refills</div>
                  </div>
                </div>
                <span style={{ color: "#0284c7", fontSize: "0.9rem" }}>›</span>
              </div>
            </div>
          </div>
        </div>

        {/* Dynamic Chat Messages */}
        {messages.map((msg, index) => {
          const isUser = msg.role === "user";
          return (
            <div key={msg.id || index} className={`message-row ${isUser ? "user" : "assistant"}`}>
              {!isUser && (
                <div className="message-avatar">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" />
                  </svg>
                </div>
              )}
              <div className={`message-bubble ${isUser ? "user" : "assistant"}`}>
                {!isUser && (
                  <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "4px" }}>
                    <span style={{ fontSize: "0.76rem", fontWeight: 700, color: "#0f766e" }}>
                      City Care Assistant
                    </span>
                    {getAgentLabel(msg.agent)}
                  </div>
                )}
                <div style={{ fontSize: "0.88rem" }}>
                  {renderFormattedContent(msg.content)}
                </div>

                <div className="message-timestamp">
                  <span>{msg.timestamp || "10:26 AM"}</span>
                  {isUser && <span style={{ color: "#0284c7" }}>✓✓</span>}
                </div>
              </div>
            </div>
          );
        })}

        {/* Loading Indicator Pill */}
        {isLoading && (
          <div className="message-row assistant">
            <div className="message-avatar">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <polyline points="12 6 12 12 14 14" />
              </svg>
            </div>
            <div className="message-bubble assistant" style={{ display: "flex", alignItems: "center", gap: "8px", color: "#64748b" }}>
              <span className="online-dot" />
              <span>Analyzing clinical context & routing agents...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Floating Pill Input Bar */}
      <div className="chat-input-pill-container">
        {/* Session restore hint if needed */}
        {restoreInputRef !== undefined && (
          <div style={{ width: "100%", maxWidth: "820px", display: "flex", justifyContent: "flex-end", marginBottom: "6px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.74rem" }}>
              <input
                type="text"
                placeholder="Restore by Ref (e.g. APP-12345)"
                value={restoreInputRef}
                onChange={(e) => setRestoreInputRef(e.target.value)}
                style={{ border: "1px solid #e2e8f0", borderRadius: "10px", padding: "3px 8px", fontSize: "0.72rem", outline: "none", width: "170px" }}
              />
              <button
                onClick={() => onRestoreAppointment(restoreInputRef)}
                disabled={restoreLoading || !restoreInputRef.trim()}
                style={{ background: "#f1f5f9", border: "1px solid #cbd5e1", borderRadius: "10px", padding: "3px 8px", fontSize: "0.72rem", cursor: "pointer" }}
              >
                {restoreLoading ? "Restoring..." : "Restore"}
              </button>
            </div>
          </div>
        )}

        <div className="chat-input-pill">
          {/* File Upload Hidden Input */}
          <input
            type="file"
            ref={fileInputRef}
            style={{ display: "none" }}
            accept=".pdf,.png,.jpg,.jpeg,.webp"
            onChange={onFileUpload}
          />
          <button
            type="button"
            className="chat-attach-btn"
            title="Upload Lab Report"
            onClick={() => fileInputRef.current?.click()}
            disabled={labLoading}
          >
            {labLoading ? "⏳" : "+"}
          </button>

          <input
            type="text"
            className="chat-text-input"
            placeholder={language === "English" ? "Type your message or Patient ID (e.g. p1)..." : "Apna sawal ya Patient ID likhein (maslan p1)..."}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && onSendMessage()}
          />

          <button
            type="button"
            className="chat-send-btn"
            onClick={() => onSendMessage()}
            disabled={isLoading || !inputMessage.trim()}
            title="Send Message"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>

        <div style={{ textAlign: "center", fontSize: "0.72rem", color: "#94a3b8", marginTop: "8px" }}>
          City Care AI Assistant • For acute emergency chest pain, call Rescue 1122
        </div>
      </div>
    </div>
  );
};
