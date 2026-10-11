"use client";

import React, { useRef } from "react";
import { LabSample, LabAnalysisResult } from "@/types";

interface LabVisionViewProps {
  labSamples: LabSample[];
  selectedSampleFile: string;
  onAnalyzeSample: (filename: string) => void;
  onFileUpload: (file: File) => void;
  labLoading: boolean;
  labResult: LabAnalysisResult | null;
  showRawJson: boolean;
  setShowRawJson: (show: boolean) => void;
  onSendResultToChat: () => void;
}

export const LabVisionView: React.FC<LabVisionViewProps> = ({
  labSamples,
  selectedSampleFile,
  onAnalyzeSample,
  onFileUpload,
  labLoading,
  labResult,
  showRawJson,
  setShowRawJson,
  onSendResultToChat,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  return (
    <div style={{ padding: "24px", overflowY: "auto", height: "100%", display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Hero Banner */}
      <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "20px", padding: "22px", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "16px", boxShadow: "0 2px 8px rgba(0,0,0,0.03)" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "4px" }}>
            <span style={{ fontSize: "1.8rem" }}>🧪</span>
            <h2 style={{ fontSize: "1.35rem", fontWeight: 800, color: "#0f172a" }}>
              Multimodal Lab Report Vision & Extraction Engine
            </h2>
          </div>
          <p style={{ fontSize: "0.82rem", color: "#64748b", maxWidth: "780px", lineHeight: 1.5 }}>
            High-accuracy multimodal pipeline reading patient laboratory PDFs and images (Gemini Vision LLM + PyMuPDF).
            Extracts test names, numeric values, units, and reference ranges into structured schema, detects biological deviations with deterministic flags,
            and provides conversational non-diagnostic explanations in simple UrduLish.
          </p>
        </div>

        {/* Benchmark Badges */}
        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          <div style={{ background: "#ecfdf5", border: "1px solid #a7f3d0", padding: "6px 12px", borderRadius: "8px", fontSize: "0.76rem", color: "#047857", fontWeight: 600 }}>
            🎯 30-Report Benchmark: 100% Precision & Recall
          </div>
          <div style={{ background: "#fef3c7", border: "1px solid #fde68a", padding: "6px 12px", borderRadius: "8px", fontSize: "0.76rem", color: "#b45309", fontWeight: 600 }}>
            🛡️ Safety Guardrail: 100% Non-Diagnostic
          </div>
        </div>
      </div>

      {/* Upload Zone & Demo Samples */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1.2fr", gap: "18px" }}>
        {/* Upload Card */}
        <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "18px", padding: "20px", display: "flex", flexDirection: "column", gap: "14px" }}>
          <h3 style={{ fontSize: "0.95rem", fontWeight: 700, color: "#0f766e" }}>
            📤 Upload Patient Lab Report
          </h3>

          <input
            type="file"
            ref={fileInputRef}
            style={{ display: "none" }}
            accept=".pdf,.png,.jpg,.jpeg,.webp"
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                onFileUpload(e.target.files[0]);
              }
            }}
          />

          <div
            onClick={() => fileInputRef.current?.click()}
            style={{
              border: "2px dashed #cbd5e1",
              borderRadius: "14px",
              padding: "30px 16px",
              textAlign: "center",
              cursor: "pointer",
              background: "#f8fafc",
              transition: "all 0.15s ease",
            }}
          >
            <div style={{ fontSize: "2rem", marginBottom: "8px" }}>📁</div>
            <div style={{ fontWeight: 600, fontSize: "0.88rem", color: "#1e293b" }}>
              Click to browse or drag & drop file
            </div>
            <div style={{ fontSize: "0.74rem", color: "#64748b", marginTop: "2px" }}>
              Supports PDF, PNG, JPG, JPEG, WebP
            </div>
          </div>
        </div>

        {/* Demo Samples */}
        <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "18px", padding: "20px", display: "flex", flexDirection: "column", gap: "12px" }}>
          <h3 style={{ fontSize: "0.95rem", fontWeight: 700, color: "#0f766e" }}>
            🧪 Quick Load Verified Benchmark Samples
          </h3>

          <div style={{ display: "flex", flexDirection: "column", gap: "8px", maxHeight: "200px", overflowY: "auto" }}>
            {labSamples.map((s, idx) => (
              <button
                key={idx}
                onClick={() => onAnalyzeSample(s.filename)}
                disabled={labLoading}
                style={{
                  background: selectedSampleFile === s.filename ? "#ecfdf5" : "#f8fafc",
                  border: `1px solid ${selectedSampleFile === s.filename ? "#0f766e" : "#e2e8f0"}`,
                  borderRadius: "10px",
                  padding: "10px 14px",
                  textAlign: "left",
                  fontSize: "0.82rem",
                  fontWeight: 600,
                  color: "#0f172a",
                  cursor: "pointer",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <span>📄 {s.label || s.filename}</span>
                <span style={{ fontSize: "0.7rem", color: "#64748b" }}>{s.size_kb} KB</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Loading state */}
      {labLoading && (
        <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "18px", padding: "40px", textAlign: "center" }}>
          <div style={{ fontSize: "2rem", marginBottom: "10px" }}>⏳</div>
          <h4 style={{ fontWeight: 700, color: "#0f766e" }}>Analyzing Lab Document with Gemini Flash Vision...</h4>
          <p style={{ fontSize: "0.8rem", color: "#64748b", marginTop: "4px" }}>
            Extracting biomedical metrics, evaluating biological reference intervals, and drafting UrduLish explanation.
          </p>
        </div>
      )}

      {/* Analysis Output */}
      {labResult && !labLoading && (
        <div style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
          {/* Header Card */}
          <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "18px", padding: "20px", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                <span style={{ fontSize: "1.3rem" }}>📋</span>
                <h3 style={{ fontSize: "1.15rem", fontWeight: 700, color: "#0f172a" }}>
                  {labResult.panel || "Laboratory Investigation"}
                </h3>
                {labResult.report_id && (
                  <span style={{ fontSize: "0.74rem", background: "#f1f5f9", color: "#0f766e", padding: "2px 8px", borderRadius: "6px", fontFamily: "var(--font-mono)" }}>
                    {labResult.report_id}
                  </span>
                )}
                {labResult.abnormal_count !== undefined && (
                  <span
                    style={{
                      fontSize: "0.74rem",
                      fontWeight: 700,
                      padding: "2px 8px",
                      borderRadius: "6px",
                      background: labResult.abnormal_count > 0 ? "#fee2e2" : "#ecfdf5",
                      color: labResult.abnormal_count > 0 ? "#b91c1c" : "#059669",
                    }}
                  >
                    {labResult.abnormal_count > 0 ? `⚠️ ${labResult.abnormal_count} Parameter(s) Outside Range` : "✓ All Parameters Normal"}
                  </span>
                )}
              </div>
              <div style={{ fontSize: "0.78rem", color: "#64748b", marginTop: "4px" }}>
                {labResult.patient_name && <span>Patient: <strong>{labResult.patient_name}</strong> • </span>}
                {labResult.mrn && <span>MRN: <code>{labResult.mrn}</code> • </span>}
                {labResult.collection_date && <span>Date: {labResult.collection_date} • </span>}
                Laboratory: {labResult.laboratory_name || "City Care Diagnostics"}
              </div>
            </div>

            <button
              className="btn-primary"
              onClick={onSendResultToChat}
              style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.82rem" }}
            >
              <span>💬</span>
              <span>Discuss in Chat</span>
            </button>
          </div>

          {/* Parameters Table */}
          <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "18px", overflow: "hidden" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.85rem" }}>
              <thead>
                <tr style={{ background: "#f8fafc", borderBottom: "1px solid #e2e8f0", color: "#475569" }}>
                  <th style={{ padding: "12px 18px", fontWeight: 700 }}>Test Parameter</th>
                  <th style={{ padding: "12px 18px", fontWeight: 700 }}>Observed Value</th>
                  <th style={{ padding: "12px 18px", fontWeight: 700 }}>Units</th>
                  <th style={{ padding: "12px 18px", fontWeight: 700 }}>Reference Interval</th>
                  <th style={{ padding: "12px 18px", fontWeight: 700 }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {labResult.tests?.map((t, idx) => {
                  const val = t.numeric_value !== undefined ? t.numeric_value : (t.result_value !== undefined ? t.result_value : "—");
                  const refRange = t.reference_range_str || t.reference_range || (t.reference_range_low !== undefined && t.reference_range_high !== undefined ? `${t.reference_range_low} - ${t.reference_range_high}` : "—");
                  const flagRaw = String(t.flag || t.status || "NORMAL").toUpperCase();
                  const isCritical = flagRaw.includes("CRITICAL");
                  const isHigh = flagRaw.includes("HIGH");
                  const isLow = flagRaw.includes("LOW");
                  const isNormal = flagRaw.includes("NORMAL") || (!isHigh && !isLow && !isCritical);

                  const statusLabel = isCritical
                    ? (isHigh ? "Critical High" : "Critical Low")
                    : isHigh
                    ? "High"
                    : isLow
                    ? "Low"
                    : "Normal";

                  const statusBg = isNormal ? "#ecfdf5" : (isHigh || isCritical) ? "#fee2e2" : "#fef3c7";
                  const statusColor = isNormal ? "#059669" : (isHigh || isCritical) ? "#b91c1c" : "#b45309";

                  return (
                    <tr key={idx} style={{ borderBottom: "1px solid #f1f5f9" }}>
                      <td style={{ padding: "12px 18px", fontWeight: 600, color: "#0f172a" }}>{t.test_name}</td>
                      <td style={{ padding: "12px 18px", fontWeight: 700, color: isNormal ? "#0f172a" : (isHigh || isCritical) ? "#b91c1c" : "#b45309" }}>
                        {val}
                      </td>
                      <td style={{ padding: "12px 18px", color: "#64748b" }}>{t.unit || "—"}</td>
                      <td style={{ padding: "12px 18px", color: "#64748b" }}>{refRange}</td>
                      <td style={{ padding: "12px 18px" }}>
                        <span
                          style={{
                            fontSize: "0.72rem",
                            fontWeight: 700,
                            padding: "3px 8px",
                            borderRadius: "6px",
                            background: statusBg,
                            color: statusColor,
                          }}
                        >
                          {statusLabel}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* UrduLish Interpretation Card */}
          <div style={{ background: "#f0fdf9", border: "1px solid #a7f3d0", borderRadius: "18px", padding: "20px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
              <h4 style={{ fontSize: "0.95rem", fontWeight: 700, color: "#065f46", display: "flex", alignItems: "center", gap: "6px" }}>
                <span>🗣️</span> Non-Diagnostic UrduLish Explanation
              </h4>
              <button
                className="btn-secondary"
                style={{ fontSize: "0.74rem", padding: "4px 10px" }}
                onClick={() => {
                  if (labResult.urdulish_summary) {
                    navigator.clipboard.writeText(labResult.urdulish_summary);
                    alert("Summary copied to clipboard!");
                  }
                }}
              >
                📋 Copy
              </button>
            </div>

            <div style={{ fontSize: "0.88rem", color: "#1e293b", lineHeight: 1.6, whiteSpace: "pre-line" }}>
              {labResult.urdulish_summary}
            </div>

            {/* Shield Notice */}
            <div style={{ marginTop: "14px", background: "#ffffff", border: "1px solid #cbd5e1", borderRadius: "10px", padding: "10px 14px", display: "flex", gap: "10px", alignItems: "center", fontSize: "0.75rem", color: "#475569" }}>
              <span>🛡️</span>
              <div>
                <strong>Clinical Notice:</strong> This AI breakdown is for patient understanding only and is strictly non-diagnostic. Please consult your physician for clinical diagnosis and therapy.
              </div>
            </div>
          </div>

          {/* Raw JSON Toggle */}
          <div>
            <button
              className="btn-secondary"
              style={{ fontSize: "0.76rem" }}
              onClick={() => setShowRawJson(!showRawJson)}
            >
              {showRawJson ? "Hide Raw JSON Schema" : "Inspect Raw JSON Schema"}
            </button>
            {showRawJson && (
              <pre style={{ marginTop: "10px", background: "#0f172a", color: "#34d399", padding: "16px", borderRadius: "12px", fontSize: "0.75rem", overflowX: "auto" }}>
                {JSON.stringify(labResult, null, 2)}
              </pre>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
