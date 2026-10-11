"use client";

import React from "react";
import { TelemetryStats } from "@/types";

interface TelemetryViewProps {
  stats: TelemetryStats | null;
}

export const TelemetryView: React.FC<TelemetryViewProps> = ({ stats }) => {
  return (
    <div style={{ padding: "24px", overflowY: "auto", height: "100%", display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Header Banner */}
      <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "20px", padding: "20px", boxShadow: "0 2px 8px rgba(0,0,0,0.03)" }}>
        <h2 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#0f172a", display: "flex", alignItems: "center", gap: "8px" }}>
          <span>📊</span> System Observability & LangSmith Telemetry
        </h2>
        <p style={{ fontSize: "0.82rem", color: "#64748b", marginTop: "4px" }}>
          Real-time latency metrics, token consumption, cost accounting, and multi-agent routing traces across LangGraph state machines.
        </p>
      </div>

      {/* KPI Stats Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "14px" }}>
        {/* Stat 1: Avg Latency */}
        <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "16px", padding: "18px", boxShadow: "0 2px 6px rgba(0,0,0,0.02)" }}>
          <div style={{ fontSize: "0.76rem", fontWeight: 600, color: "#64748b" }}>Avg Agent Latency</div>
          <div style={{ fontSize: "1.45rem", fontWeight: 800, color: "#0f766e", marginTop: "4px" }}>
            {stats ? `${stats.avg_latency_ms} ms` : "485 ms"}
          </div>
        </div>

        {/* Stat 2: Total Conversations */}
        <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "16px", padding: "18px", boxShadow: "0 2px 6px rgba(0,0,0,0.02)" }}>
          <div style={{ fontSize: "0.76rem", fontWeight: 600, color: "#64748b" }}>Total Conversations</div>
          <div style={{ fontSize: "1.45rem", fontWeight: 800, color: "#0284c7", marginTop: "4px" }}>
            {stats?.total_conversations || 1}
          </div>
        </div>

        {/* Stat 3: Total Tokens */}
        <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "16px", padding: "18px", boxShadow: "0 2px 6px rgba(0,0,0,0.02)" }}>
          <div style={{ fontSize: "0.76rem", fontWeight: 600, color: "#64748b" }}>Tokens Processed</div>
          <div style={{ fontSize: "1.45rem", fontWeight: 800, color: "#7e22ce", marginTop: "4px" }}>
            {stats ? stats.total_tokens.toLocaleString() : "2,450"}
          </div>
        </div>

        {/* Stat 4: Estimated Cost */}
        <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "16px", padding: "18px", boxShadow: "0 2px 6px rgba(0,0,0,0.02)" }}>
          <div style={{ fontSize: "0.76rem", fontWeight: 600, color: "#64748b" }}>Estimated Cost (USD)</div>
          <div style={{ fontSize: "1.45rem", fontWeight: 800, color: "#059669", marginTop: "4px" }}>
            ${stats ? stats.total_cost_usd.toFixed(4) : "0.0004"}
          </div>
        </div>

        {/* Stat 5: Doctor HITL Interventions */}
        <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "16px", padding: "18px", boxShadow: "0 2px 6px rgba(0,0,0,0.02)" }}>
          <div style={{ fontSize: "0.76rem", fontWeight: 600, color: "#64748b" }}>Doctor HITL Gates</div>
          <div style={{ fontSize: "1.45rem", fontWeight: 800, color: "#ea580c", marginTop: "4px" }}>
            {stats?.hitl_interventions || 0}
          </div>
        </div>
      </div>

      {/* Multi-Agent Architecture Graph Diagram */}
      <div style={{ background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "20px", padding: "20px", boxShadow: "0 2px 8px rgba(0,0,0,0.03)" }}>
        <h3 style={{ fontSize: "1rem", fontWeight: 700, color: "#0f766e", marginBottom: "6px" }}>
          Multi-Agent StateGraph Architecture
        </h3>
        <p style={{ fontSize: "0.8rem", color: "#64748b", marginBottom: "16px" }}>
          LangGraph conditional orchestration with parallel fan-out (Triage + Records) and checkpointer memory.
        </p>

        <div style={{ background: "#0f172a", padding: "18px", borderRadius: "12px", fontFamily: "var(--font-mono)", fontSize: "0.8rem", color: "#94a3b8", overflowX: "auto", lineHeight: 1.7 }}>
          <code>
            <span style={{ color: "#38bdf8" }}>[START]</span> ➔ <strong style={{ color: "#34d399" }}>supervisor (Router)</strong><br />
            &nbsp;&nbsp;├── [first_msg & returning] ➔ <span style={{ color: "#fef08a" }}>returning_greeting</span> ➔ [END]<br />
            &nbsp;&nbsp;├── [intake_active] ➔ <span style={{ color: "#a7f3d0" }}>intake</span> ➔ [END]<br />
            &nbsp;&nbsp;├── [intake_done] ➔ <strong style={{ color: "#38bdf8" }}>parallel_triage_records</strong> (Triage + Records Concurrently)<br />
            &nbsp;&nbsp;├── [routine_care] ➔ <span style={{ color: "#818cf8" }}>scheduling</span> ➔ [END]<br />
            &nbsp;&nbsp;├── [rx_check] ➔ <span style={{ color: "#f472b6" }}>prescription_safety</span> ➔ <strong style={{ color: "#fb923c" }}>hitl_gate (Doctor Approval Gate)</strong><br />
            &nbsp;&nbsp;├── [emergency_flag] ➔ <strong style={{ color: "#f87171" }}>emergency_escalation (1122 Notice)</strong> ➔ [END]<br />
            &nbsp;&nbsp;└── [followup] ➔ <span style={{ color: "#c084fc" }}>followup (Outreach Reminders)</span> ➔ [END]
          </code>
        </div>
      </div>
    </div>
  );
};
