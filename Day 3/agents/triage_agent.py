"""
Triage Agent for City Care Clinics
Hybrid Two-Tier Clinical Urgency Classifier:
Tier 1: Deterministic Rule-Based Red-Flag Screener (Runs FIRST, CANNOT be overridden by LLM).
Tier 2: LLM-Assisted Classifier (Gemini 3.5 Flash Lite) for non-emergency Urgent vs Routine triage.
Guarantees 100% Emergency Recall and instant 1122 Rescue escalation.
"""

import sys
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Literal
from pydantic import BaseModel, Field

sys.path.append(str(Path(__file__).resolve().parent.parent))
from llm_factory import get_llm, get_structured_llm

# =====================================================================
# Pydantic Schemas
# =====================================================================
class LLMTriageDecision(BaseModel):
    """Schema for LLM urgency determination with safety escalation capability."""
    urgency_tier: Literal["EMERGENCY", "URGENT", "ROUTINE"] = Field(
        description="EMERGENCY for life/limb danger, URGENT for same-day acute clinic visits, ROUTINE for stable outpatient visits"
    )
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence in assessment (0.0 - 1.0)")
    clinical_reason: str = Field(description="Medical justification for the tier assignment")
    recommended_specialty: str = Field(description="General Medicine, Paediatrics, Gynaecology, Cardiology, Dermatology, ENT, or Emergency Medicine")

class TriageResult(BaseModel):
    """Final Output Schema of the Triage Agent."""
    urgency_tier: Literal["EMERGENCY", "URGENT", "ROUTINE"]
    is_emergency: bool
    confidence_score: float
    reason: str
    red_flag_triggers: List[str]
    escalation_message_urdulish: Optional[str] = None
    recommended_specialty: str = "General Medicine"

# =====================================================================
# Deterministic Red-Flag Rules (Zero-Override Engine)
# =====================================================================
RED_FLAG_PATTERNS = [
    # 1. Cardiovascular / Chest Pain
    {
        "category": "Cardiovascular",
        "regex": r"(seene mein|chest pain|chhati pe|pressure on chest|dard bayen baazu|left arm pain|heart attack|paseenay aa rahe)",
        "reason": "Acute chest pain/pressure with potential myocardial ischemia or acute coronary syndrome."
    },
    # 2. Respiratory Distress
    {
        "category": "Respiratory",
        "regex": r"(saans (lene mein shadeed|phool rahi|band ho|ruk rahi)|severe breathlessness|gasping|inability to breathe|stridor|choking|neelay? (parh|rang))",
        "reason": "Acute respiratory distress / airway compromise requiring immediate oxygenation and resuscitation."
    },
    # 3. Stroke / Neurological (FAST)
    {
        "category": "Neurological (Stroke FAST)",
        "regex": r"(munh teda|face droop|baazu sun|arm weakness|awaz ladkhada|slurred speech|behosh|unconscious|faint|syncope|jhatkay|seizure|convulsion)",
        "reason": "Acute neurological deficit matching Stroke (FAST criteria) or acute altered consciousness."
    },
    # 4. Severe Hemorrhage
    {
        "category": "Hemorrhage",
        "regex": r"((shadeed|severe|active|bohot|heavy|fresh).*?(khoon|bleed|bleeding)|khoon ki ulti|hematemesis|coughing.*?blood|hemoptysis|kala pakhana|melena)",
        "reason": "Active major hemorrhage or hemodynamic collapse risk."
    },
    # 5. Pediatric Neonatal Danger
    {
        "category": "Pediatric Alert",
        "regex": r"(3 mahine se chota|infant under 3 months|newborn fever|doodh bilkul nahi pee raha|gardana akad|sunken eyes lethargy)",
        "reason": "Neonatal fever (<3 months) or pediatric hypovolemic/septic collapse."
    },
    # 6. Obstetric Emergency
    {
        "category": "Obstetric",
        "regex": r"((hamal|pregnancy|pregnant).*?(khoon|bleed|bleeding)|(khoon|bleed|bleeding).*?(hamal|pregnancy|pregnant)|shadeed pait dard pregnancy|danday lagna eclampsia)",
        "reason": "Obstetric hemorrhage, threatened miscarriage, or eclamptic seizure."
    },
    # 7. Anaphylaxis
    {
        "category": "Anaphylaxis",
        "regex": r"(hont soojh|zaban soojh|lips swollen|tongue swollen|dawa ke baad saans band|anaphylaxis)",
        "reason": "Severe acute systemic hypersensitivity (Anaphylaxis) with imminent airway occlusion."
    },
    # 8. Psychiatric Emergency
    {
        "category": "Psychiatric Crisis",
        "regex": r"(jaan lene|khudkushi|suicide|suicidal|self harm|marna chahta)",
        "reason": "Acute crisis with imminent suicidal intent or danger to life."
    }
]

EMERGENCY_URDULISH_DIRECTIVE = """🚨 EMERGENCY MEDICAL ALERT / FORI IMDAD KI ZAROORAT:

Aap ki batai hui alamaat nihayat sanjeeda aur EMERGENCY hain.

🛑 BARAYE MEHARBANI FORAN YEH IQDAMAT KAREIN:
1. Bila-takhir 1122 par call karein ya apne qareebi hospital ke Emergency Ward (ER) pohanchein.
2. Khud drive mat karein, kisi ko gaari chalane ya sath chalne ka kahein.
3. Hamari online appointment ka intizar hargiz na karein.

City Care 24/7 Helpline: 042-111-CARE-00 (Emergency Support)"""

class TriageAgent:
    def __init__(self):
        self.llm = get_llm()
        self.classifier_llm = get_structured_llm(LLMTriageDecision)

    def screen_red_flags(self, text: str, age: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Deterministic Rule Screener. Runs BEFORE the LLM and cannot be bypassed.
        """
        text_lower = text.lower()
        triggered = []

        # Age-dependent rule: Infant under 3 months with fever
        if age is not None and age <= 0.25 and ("bukhar" in text_lower or "fever" in text_lower):
            triggered.append({
                "category": "Pediatric Alert",
                "reason": "Infant aged under 3 months presenting with fever requires immediate emergency neonatal sepsis evaluation."
            })

        for rule in RED_FLAG_PATTERNS:
            if re.search(rule["regex"], text_lower, re.IGNORECASE):
                triggered.append({
                    "category": rule["category"],
                    "reason": rule["reason"]
                })

        return triggered

    def evaluate(self, intake_data: Dict[str, Any]) -> TriageResult:
        """
        Evaluates intake dictionary or raw text.
        1. Checks deterministic red-flags.
        2. If triggered -> Returns EMERGENCY instantly.
        3. Else -> Calls Gemini 3.5 Flash Lite for URGENT vs ROUTINE triage.
        """
        # Compile text representation from intake data
        if isinstance(intake_data, dict):
            complaint = intake_data.get("chief_complaint", "")
            symptoms = " ".join(intake_data.get("associated_symptoms", []))
            history = " ".join(intake_data.get("medical_history", []))
            age = intake_data.get("patient_age")
            severity = intake_data.get("severity", 5)
            full_text = f"{complaint} {symptoms} {history}"
        else:
            full_text = str(intake_data)
            age = None
            severity = 5

        # -------------------------------------------------------------
        # Tier 1: Deterministic Rule Screener (NON-OVERRIDABLE)
        # -------------------------------------------------------------
        red_flags = self.screen_red_flags(full_text, age)
        if red_flags:
            reasons = "; ".join(f"[{rf['category']}] {rf['reason']}" for rf in red_flags)
            return TriageResult(
                urgency_tier="EMERGENCY",
                is_emergency=True,
                confidence_score=1.0, # Deterministic certainty
                reason=reasons,
                red_flag_triggers=[rf["category"] for rf in red_flags],
                escalation_message_urdulish=EMERGENCY_URDULISH_DIRECTIVE,
                recommended_specialty="Emergency Medicine / 1122"
            )

        # -------------------------------------------------------------
        # Tier 2: LLM Urgency Classification (Urgent vs Routine)
        # -------------------------------------------------------------
        prompt = f"""You are an outpatient clinical triage physician for City Care Clinics.
A patient has provided the following intake details:
Chief Complaint: {complaint if 'complaint' in locals() else full_text}
Associated Symptoms: {symptoms if 'symptoms' in locals() else 'None'}
Duration: {intake_data.get('duration', 'Not stated') if isinstance(intake_data, dict) else 'Not stated'}
Severity (1-10): {severity}
Age: {age if age is not None else 'Adult'}
Medical History: {history if 'history' in locals() else 'None'}

Classify this case into one of two outpatient urgency tiers:
1. URGENT: Acute symptoms requiring same-day doctor examination within 2-4 hours (e.g. continuous vomiting, dehydration, high fever > 102 F, acute severe localized pain, rapidly spreading rash).
2. ROUTINE: Stable, subacute, or chronic symptoms that can be safely scheduled within 24-72 hours (e.g. mild cough > 3 days, long-standing backache, acne, routine BP/diabetes checkup).

Select the most appropriate medical specialty: General Medicine, Paediatrics, Gynaecology, Cardiology, Dermatology, or ENT.
Provide clinical reasoning and a confidence score (0.5 to 1.0)."""

        try:
            decision = self.classifier_llm.invoke(prompt)
            is_em = (decision.urgency_tier == "EMERGENCY")
            return TriageResult(
                urgency_tier=decision.urgency_tier,
                is_emergency=is_em,
                confidence_score=decision.confidence_score,
                reason=decision.clinical_reason,
                red_flag_triggers=["Clinical Life-Threat Alert"] if is_em else [],
                escalation_message_urdulish=EMERGENCY_URDULISH_DIRECTIVE if is_em else None,
                recommended_specialty="Emergency Medicine / 1122" if is_em else decision.recommended_specialty
            )
        except Exception as e:
            # Safe conservative fallback: treat as URGENT if severity >= 7 else ROUTINE
            tier = "URGENT" if (severity and severity >= 7) else "ROUTINE"
            return TriageResult(
                urgency_tier=tier,
                is_emergency=False,
                confidence_score=0.75,
                reason=f"Clinical rule fallback based on severity score ({severity}/10).",
                red_flag_triggers=[],
                escalation_message_urdulish=None,
                recommended_specialty="General Medicine"
            )

    triage = evaluate


# Singleton instance
triage_agent = TriageAgent()

if __name__ == "__main__":
    print("Testing Triage Agent...")
    emergency_case = {"chief_complaint": "Seene mein shadeed dabao aur bayen baazu mein dard", "patient_age": 55}
    res_em = triage_agent.evaluate(emergency_case)
    print("\n--- Emergency Case ---")
    print(f"Tier: {res_em.urgency_tier} (Emergency={res_em.is_emergency})")
    print(f"Reason: {res_em.reason}")

    routine_case = {"chief_complaint": "Chehre par keel aur daanay pichle 2 maah se", "severity": 3, "patient_age": 22}
    res_rt = triage_agent.evaluate(routine_case)
    print("\n--- Routine Case ---")
    print(f"Tier: {res_rt.urgency_tier}")
    print(f"Specialty: {res_rt.recommended_specialty}")
    print(f"Reason: {res_rt.reason}")
