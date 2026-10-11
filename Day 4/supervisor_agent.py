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
import re
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


def is_emergency_message(text: str) -> bool:
    """
    Zero-override emergency screener for acute life-threatening red flags.
    Comprehensive coverage of Roman Urdu (seny, seenay, etc.) and English.
    """
    if not text:
        return False
    import re
    msg = text.lower().strip()

    # 1. Direct Phrases
    direct_phrases = [
        # Chest / Cardiac
        "chest pain", "heart attack", "dil ka daura", "seena dard", "seene mein", "seenay mein",
        "seny mein", "senay mein", "sene mein", "seeney mein", "seny me", "senay me", "seene me", "seenay me",
        "chhati mein", "chati mein", "chhati pe", "chati pe", "dil mein dard", "bayen bazu", "left arm pain",
        "pressure on chest", "tightness in chest", "heaviness in chest",
        # Respiratory
        "saans ruk", "saans band", "saans lene mein shadeed", "saans phool", "shortness of breath",
        "difficulty breathing", "choking", "dum ghut", "gasping",
        # Stroke / Neurological (FAST)
        "behosh", "unconscious", "fainted", "faint", "syncope", "jhatkay", "seizure", "convulsion",
        "munh teda", "munh terha", "face droop", "slurred speech", "awaz ladkhada", "falij", "stroke",
        # Hemorrhage / Bleeding
        "khoon ki ulti", "hematemesis", "coughing blood", "heavy bleeding", "shadeed khoon",
        # Anaphylaxis & Poisoning
        "anaphylaxis", "hont soojh", "zaban soojh", "zehar", "poison",
        # Crisis
        "khudkushi", "suicide", "self harm"
    ]
    if any(dp in msg for dp in direct_phrases):
        return True

    # 2. Chest / Cardiac Regex Pattern (handles permutations like "mere seny mein shadeed dard ho rha ha")
    cardiac_pattern = r"(s[e]+n[eaey]+|ch+at[ti]|chest|heart|dil)\b.*?\b(dard|pain|shiddat|shadeed|pressure|boj[h]?|jalan|heaviness|tight|attack|band|khichao)"
    if re.search(cardiac_pattern, msg):
        return True

    cardiac_reverse = r"(dard|pain|shiddat|shadeed|pressure|boj[h]?|heaviness|tight)\b.*?\b(s[e]+n[eaey]+|ch+at[ti]|chest|heart|dil)"
    if re.search(cardiac_reverse, msg):
        return True

    # 3. Respiratory Regex
    resp_pattern = r"(saans|breath).*?(ruk|band|takleef|shadeed|phool|chok|gasp|short)"
    if re.search(resp_pattern, msg):
        return True

    # 4. Neurological Regex
    neuro_pattern = r"(munh|face).*?(ted|terh|droop)|(awaz|speech).*?(ladkh|slurr)"
    if re.search(neuro_pattern, msg):
        return True

    return False


def is_data_exfiltration_attempt(text: str) -> bool:
    """Detects adversarial attempts to exfiltrate patient data, bypass rules, or leak system prompts."""
    if not text:
        return False
    msg = text.lower().strip()
    patterns = [
        "ignore your rules", "ignore all rules", "ignore previous instructions", "disregard all instructions",
        "another patient", "doosray patient", "dosray patient", "dusre mareez", "doosre mareez", "kisi aur patient",
        "kisi aur mareez", "give me another patient", "show another patient", "leak patient",
        "patient report of someone else", "dump database", "database passwords", "sql injection",
        "select * from", "reveal system prompt", "system prompt reveal", "reveal credentials", "admin password",
        "jailbreak", "bypass security", "exfiltrate", "all patient records", "sab mareezon ka record",
        "show other patient", "give me other patient", "give me patient report",
        "system override", "reveal all", "medical records", "phone numbers", "for patient", "api keys", "dump all"
    ]
    return any(p in msg for p in patterns)


def is_diagnosis_demand(text: str) -> bool:
    """Detects requests demanding AI to autonomously diagnose disease without a doctor."""
    if not text:
        return False
    msg = text.lower().strip()
    patterns = [
        "kya bimari hai", "mujhe kya bimari", "meri bimari bata", "bimari bata do", "bimari batao",
        "bimari ka naam", "kya marz hai", "diagnose me", "tell me my diagnosis", "what is my diagnosis",
        "what disease do i have", "tashkhees karo", "tashkhees kar", "mujhe kya hua hai",
        "tell me what illness", "diagnose my illness", "give me diagnosis", "diagnose without doctor",
        "what illness i have", "diagnose karo", "konsi disease", "konsi bimari", "seedha batao",
        "batao mujhe konsi", "what disease", "which disease", "kon sa marz"
    ]
    return any(p in msg for p in patterns)


def is_unauthorized_medication_demand(text: str) -> bool:
    """Detects requests demanding prescription drugs or medicines without seeing a doctor."""
    if not text:
        return False
    msg = text.lower().strip()
    patterns = [
        "doctor ki zarurat nahi", "doctor ke baghair", "bina doctor ke", "bina doctor", "doctor k bger",
        "bas dawai bata do", "bas dawai batao", "dawai bata do", "dawa bata do", "goli bata do",
        "konsi dawai khaun", "konsi goli khaun", "medicine bata do", "prescribe medicine without doctor",
        "just give me medicine", "just prescribe", "skip doctor and prescribe", "dawa likh do",
        "antibiotic bata do", "sirf dawai chahiye", "sirf prescription likh do", "dawai likh do",
        "typhoid ki goli", "bina doctor ko dikhaye antibiotic", "skip doctor",
        "dispense", "order you to dispense", "tramadol", "sleeping pills", "xanax", "narcotic",
        "controlled substance", "prescribe right now", "medical authority"
    ]
    return any(p in msg for p in patterns)


def is_overdose_inquiry(text: str) -> bool:
    """Detects inquiries asking about taking excessively large or lethal doses of medication."""
    if not text:
        return False
    msg = text.lower().strip()
    patterns = [
        r"\b(?:1[0-9]|[2-9][0-9])\s*(?:panadol|paracetamol|brufen|tablets?|golian|goliyan|pills?)",
        r"(?:aik sath|ek sath)\s*\d+\s*(?:golian|goliyan|tablets?|panadol|pills?)",
        r"15 panadol", r"10 panadol", r"20 panadol", r"overdose", r"poisoning"
    ]
    return any(re.search(p, msg) for p in patterns)


def is_off_topic_query(text: str) -> bool:
    """Detects non-medical off-topic questions (sports, weather, recipes, crypto, coding, trivia)."""
    if not text:
        return False
    msg = text.lower().strip()
    medical_words = [
        "dard", "pain", "doctor", "clinic", "appointment", "bukhar", "fever", "saans", "hospital",
        "patient", "dawai", "medicine", "test", "report", "hba1c", "blood", "sugar", "chhati", "sir"
    ]
    if any(mw in msg for mw in medical_words):
        return False
    patterns = [
        "cricket", "who won", "kon jeeta", "match score", "ipl", "psl",
        "weather", "mausam kaisa", "barish", "temperature",
        "bitcoin", "crypto", "stock market", "shares", "invest in",
        "recipe", "khana pakana", "biryani banane", "cook pasta",
        "python code", "write python", "programming in", "hello world", "write a code", "code in java",
        "prime minister", "politics in pakistan", "imran khan", "nawaz sharif",
        "movie review", "film recommend", "tell me a joke", "samandar konsa"
    ]
    return any(p in msg for p in patterns)


def is_angry_or_frustrated(text: str) -> bool:
    """Detects angry, frustrated, or confused patients requiring de-escalation."""
    if not text:
        return False
    msg = text.lower().strip()
    patterns = [
        "bakwas clinic", "fazool service", "worst clinic", "terrible service", "very angry",
        "shadeed gussa", "useless bot", "stupid assistant", "chutiya", "bakwas bot",
        "1 ghante se wait", "bohot bura clinic", "fraud clinic", "ghatiya service",
        "insaan se baat karni", "human agent", "talk to human", "manager se baat",
        "complaint karni hai", "paise kat gaye", "fail ho gayi", "fees itni zyada",
        "samajh nahi aa raha", "confused", "rasta batao", "kahan hai clinic", "clinic kahan hai", "sahi rasta"
    ]
    return any(p in msg for p in patterns)


def is_lab_inquiry_message(text: str) -> bool:
    """Detects questions asking to interpret specific clinical lab test numbers or reports."""
    if not text:
        return False
    msg = text.lower().strip()
    import re
    pat = r"\b(hba1c|hb a1c|creatinine|alt|sgpt|platelets?|cholesterol|lipid|potassium|hemoglobin|wbc|cbc report|lft report|sugar report|blood report|urea|uric acid|bilirubin)\b"
    return bool(re.search(pat, msg))


def is_reschedule_or_cancel(text: str) -> bool:
    """Detects explicit appointment cancellation or reschedule requests."""
    if not text:
        return False
    msg = text.lower().strip()
    patterns = [
        "cancel appointment", "appointment cancel", "cancel kar dein", "cancel kar do", "mansookh",
        "reschedule", "reschedule appointment", "appointment reschedule", "tareeq badal",
        "waqt badal", "change appointment", "appointment change", "ek cancel", "cancel duplicate"
    ]
    return any(p in msg for p in patterns)


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

        # 0. Zero-Override Emergency Check
        if is_emergency_message(last_msg):
            return "emergency_escalation"

        # 0.1 Security & Safety Guardrails
        if (
            is_data_exfiltration_attempt(last_msg)
            or is_diagnosis_demand(last_msg)
            or is_unauthorized_medication_demand(last_msg)
            or is_overdose_inquiry(last_msg)
            or is_off_topic_query(last_msg)
            or is_angry_or_frustrated(last_msg)
        ):
            return "safety_guardrail"

        # 0.2 Specific Lab Report Question Routing
        if is_lab_inquiry_message(last_msg):
            return "records"

        # 0.3 Cancellation & Rescheduling Direct Route
        if is_reschedule_or_cancel(last_msg):
            return "scheduling"

        # 1. Check if patient is asking about previous appointment, providing Appointment ID, or replying "returning patient"
        import re
        has_id_pattern = bool(re.search(r"\b(BK[-_]?(?:2026[-_]?)?[A-Za-z0-9]{4,10})\b", last_msg, re.IGNORECASE))
        has_uuid_pattern = bool(re.search(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", last_msg, re.IGNORECASE))
        lookup_keywords = [
            "previous appointment", "purani appointment", "appointment status", "pehle appointment",
            "meri appointment", "appointment id", "booking reference", "restore", "pouch", "check appointment",
            "returning", "returning patient", "purana patient", "purana", "purani", "pehle aya", "pehle aya tha",
            "pehle ayi thi", "already registered", "pehle se registered", "old patient", "pehle appointment hui"
        ]
        if has_id_pattern or has_uuid_pattern or any(lk in last_msg for lk in lookup_keywords):
            return "scheduling"

        # 2. Check if patient is replying "new patient"
        is_new_reply = any(w in last_msg for w in [
            "new patient", "new", "naya patient", "naya", "nayi", "pehli dafa", "first time", "pehli bar"
        ]) and not any(w in last_msg for w in ["returning", "purana", "purani", "pehle"])
        if is_new_reply and not state.get("intake_form", {}).get("chief_complaint"):
            return "intake"

        # 3. Check if patient is confirming an active proposed appointment, choosing alternative, or providing signup info
        sched_req = state.get("scheduling_request")
        if sched_req and sched_req.get("status") in ("PROPOSED", "ALTERNATIVES_PROPOSED", "AWAITING_PATIENT_INFO"):
            return "scheduling"

        # 3.1 If doctors were suggested, patient reply (option, doctor name, or time) goes directly to scheduling
        if state.get("intake_stage") == "doctors_suggested" or state.get("suggested_doctors"):
            return "scheduling"

        # 4. Check if Human-in-the-Loop review is active
        if state.get("hitl_decision"):
            return "hitl_gate"
        if state.get("hitl_required") and state.get("hitl_type") in ("PRESCRIPTION_REVIEW", "LAB_EXPLANATION"):
            return "hitl_gate"

        # 5. Check if patient is currently in active conversational intake stages
        stage = state.get("intake_stage")
        has_chief = bool(state.get("intake_form", {}).get("chief_complaint"))
        if stage in ("awaiting_complaint", "awaiting_duration", "awaiting_severity", "awaiting_associated_symptoms", "awaiting_doctor_permission"):
            return "intake"
        if state.get("awaiting_intake_details") or (has_chief and not state.get("intake_complete")):
            return "intake"

        # 4. Direct booking / scheduling / doctor inquiry intent
        booking_keywords = [
            "appointment", "booking", "tarikh", "slot", "slots", "doctor time", "milna hai",
            "book kar", "schedule", "dr.", "doctor ke sath", "doctor k sath", "cancel", "reschedule", "dikhana hai",
            "dastiyab doctor", "available doctor", "konsay doctor", "kon se doctor", "timing", "physician",
            "routine general", "dha branch", "gulberg branch", "branch mein",
            "dubara", "dobara", "repeat", "wahi doctor", "wohi doctor", "unke sath", "unhi ke sath",
            "change doctor", "doctor change", "galat doctor", "wrong doctor", "ayesha", "ayesha tariq",
            "usman sheikh", "omer latif", "bilal saeed", "maryam naveed"
        ]
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

        # 6. Clinical Complaints Check:
        has_complaint_in_msg = any(k in last_msg for k in [
            "bukhar", "fever", "dard", "pain", "khansi", "cough", "jalan", "vomit",
            "ulti", "seeti", "asthma", "headache", "sore throat", "stomach", "rash",
            "pait", "sar", "sir", "gala", "nazla", "zukaam", "flu", "sugar", "pressure", "chhati",
            "saans", "tabiyat", "bemaar", "sick", "problem", "masla", "ill"
        ])

        asks_for_doc = any(w in last_msg for w in [
            "doctor bta", "doctor btao", "doctor bata", "doctor bataiye", "doctor batao",
            "doctor suggest", "doctor dekh", "doctor dikha", "doctor dikhana", "doctor milna",
            "koi doctor", "doctor chahiye", "konsa doctor", "recommend doctor", "which doctor",
            "doctor kon", "dastiyab doctor", "available doctor", "dekha sakun", "dikha sakun",
            "dekha sakoon", "dikha sakoon", "check karwa sakun", "checkup karwana"
        ])

        # If user explicitly describes symptoms AND asks for a doctor in the SAME message:
        # Give doctor options immediately!
        if has_complaint_in_msg and asks_for_doc and not state.get("triage_result"):
            if not state.get("intake_form") or not state.get("intake_form", {}).get("chief_complaint"):
                state["intake_form"] = {"chief_complaint": last_msg}
            return "parallel_triage_records"

        # If user mentions symptom without asking for doctor yet:
        # Route to intake to ask "kitni or kb sy ha"
        if has_complaint_in_msg and not state.get("triage_result"):
            return "intake"

        # 5. Returning patient greeting check:
        # Trigger on patient's first message when no assistant reply has been emitted yet
        assistant_msgs = [
            m for m in messages
            if (isinstance(m, dict) and m.get("role") == "assistant")
            or (hasattr(m, "type") and m.type == "ai")
        ]
        if state.get("is_returning_patient") and len(assistant_msgs) == 0 and not has_complaint_in_msg:
            return "returning_greeting"

        # 6. Check if intake is incomplete
        intake_form = state.get("intake_form", {})
        if not state.get("intake_complete"):
            return "intake"

        # 7. Parallel Triage & Records Fan-Out (once intake has chief complaint but no triage result yet)
        if state.get("intake_complete") and not state.get("triage_result"):
            return "parallel_triage_records"

        # 8. Post-triage routing:
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
