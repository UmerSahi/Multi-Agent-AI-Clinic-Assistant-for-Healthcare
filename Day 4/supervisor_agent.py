"""
Supervisor Agent & Router for City Care Clinics
Orchestrates specialist agents using LangGraph:
- Analyzes patient state, intent, and conversational history
- Routes to Intake, Triage, Records, Scheduling, Clinical Summary, Prescription Safety, Follow-up
- Coordinates parallel fan-out (Triage + Records concurrently)
- Implements retry policies and graceful degradation fallbacks
- Logs all state and node transitions with latency tracking
"""

import sys
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

DAY4_DIR = Path(__file__).resolve().parent
ROOT_DIR = DAY4_DIR.parent
DAY3_DIR = ROOT_DIR / "Day 3"
DAY2_DIR = ROOT_DIR / "Day 2"

for p in [str(DAY4_DIR), str(DAY3_DIR), str(DAY3_DIR / "agents"), str(DAY2_DIR), str(ROOT_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from clinical_state import ClinicalState
from memory_manager import memory_manager
from hitl_manager import hitl_manager
from observability import observability

try:
    from intake_agent import intake_agent  # type: ignore
    from triage_agent import triage_agent  # type: ignore
    from scheduling_agent import scheduling_agent  # type: ignore
    from records_agent import records_agent  # type: ignore
    from clinical_summary_agent import clinical_summary_agent  # type: ignore
    from prescription_safety_agent import prescription_safety_agent  # type: ignore
    from followup_agent import followup_agent  # type: ignore
except ImportError:
    from agents.intake_agent import intake_agent  # type: ignore
    from agents.triage_agent import triage_agent  # type: ignore
    from agents.scheduling_agent import scheduling_agent  # type: ignore
    from agents.records_agent import records_agent  # type: ignore
    from agents.clinical_summary_agent import clinical_summary_agent  # type: ignore
    from agents.prescription_safety_agent import prescription_safety_agent  # type: ignore
    from agents.followup_agent import followup_agent  # type: ignore


class SupervisorAgent:
    """Intelligent router and resilience coordinator for the multi-agent clinic."""

    def __init__(self):
        pass

    def route_intent(self, state: ClinicalState) -> str:
        """
        Determines the next agent node based on state flags and conversation.
        """
        messages = state.get("messages", [])
        last_msg = ""
        if messages:
            m = messages[-1]
            last_msg = (m.get("content", "") if isinstance(m, dict) else getattr(m, "content", "")).lower()

        # Emergency check
        emergency_keywords = [
            "chest pain", "seene mein", "seenay mein", "seena dard", "heart attack",
            "saans ruk", "saans band", "saans lene mein shadeed", "behosh", "unconscious"
        ]
        if any(ek in last_msg for ek in emergency_keywords):
            return "emergency_escalation"

        # 1. Check if Human-in-the-Loop review is active
        if state.get("hitl_required"):
            return "hitl_gate"

        # 2. Direct booking / scheduling intent (runs first if patient explicitly asks for booking/appointment)
        booking_keywords = ["appointment", "booking", "tarikh", "slot", "doctor time", "milna hai", "book kar", "cancel", "reschedule"]
        if any(kw in last_msg for kw in booking_keywords):
            if not state.get("triage_result"):
                pref_spec = state.get("long_term_memory", {}).get("preferred_specialty", "General Medicine")
                state["triage_result"] = {
                    "urgency_tier": "ROUTINE",
                    "confidence_score": 1.0,
                    "reason": "Routine outpatient follow-up / preferred doctor consultation",
                    "recommended_specialty": pref_spec
                }
            return "scheduling"

        # 3. Returning patient greeting check:
        # Trigger on patient's first message when no assistant reply has been emitted yet
        assistant_msgs = [
            m for m in messages
            if (isinstance(m, dict) and m.get("role") == "assistant")
            or (hasattr(m, "type") and m.type == "ai")
        ]
        has_complaint_in_msg = any(k in last_msg for k in ["bukhar", "fever", "dard", "pain", "khansi", "cough", "jalan", "vomit", "ulti", "seeti", "asthma"])
        if state.get("is_returning_patient") and len(assistant_msgs) == 0 and not has_complaint_in_msg:
            return "returning_greeting"

        # 4. Check if intake is incomplete
        intake_form = state.get("intake_form", {})
        if not state.get("intake_complete"):
            # Check if user message indicates complaints
            return "intake"

        # 5. Parallel Triage & Records Fan-Out (once intake has chief complaint but no triage result yet)
        if state.get("intake_complete") and not state.get("triage_result"):
            return "parallel_triage_records"

        # 6. Post-triage routing:
        triage = state.get("triage_result", {})
        if triage.get("urgency_tier") == "EMERGENCY":
            return "emergency_escalation"

        # 7. Pre-visit clinical summary compilation (SOAP note for doctor)
        if state.get("appointment_result") and not state.get("clinical_soap_note"):
            return "clinical_summary"

        # 8. Follow-up intent
        followup_keywords = ["dawai ka waqt", "medicine time", "tabiyat behtar", "recovery", "check in"]
        if any(kw in last_msg for kw in followup_keywords):
            return "followup"

        # Default: scheduling or conversation response
        return "scheduling"

    def execute_with_retry(self, node_name: str, func, *args, max_retries: int = 2, **kwargs) -> Any:
        """
        Executes an agent action with exponential backoff and graceful error handling.
        """
        last_exception = None
        for attempt in range(max_retries + 1):
            try:
                start_t = time.time()
                result = func(*args, **kwargs)
                latency_ms = (time.time() - start_t) * 1000
                return result, latency_ms
            except Exception as e:
                last_exception = e
                time.sleep(0.3 * (2 ** attempt))

        print(f"[Supervisor Fallback] Node '{node_name}' failed after {max_retries} retries: {last_exception}")
        return None, 0.0


# Singleton instance
supervisor = SupervisorAgent()
