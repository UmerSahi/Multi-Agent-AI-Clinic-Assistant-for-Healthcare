"""
Intake Agent for City Care Clinics
Conducts multi-turn, empathetic UrduLish clinical intake.
Collects: Chief complaint, duration, severity (1-10), associated symptoms,
allergies, current medicines, medical history (diabetes, BP, pregnancy),
and patient relation (self, child, parent).
Asks ONE focused question at a time and outputs a validated Pydantic JSON form.
"""

import sys
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# Add parent directories to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from llm_factory import get_llm, get_structured_llm  # type: ignore

# =====================================================================
# Pydantic Schemas for Structured Intake
# =====================================================================
class ExtractedIntakeUpdate(BaseModel):
    """Schema used by Gemini 3.5 Flash Lite to extract clinical entities from a user utterance."""
    patient_relation: Optional[str] = Field(None, description="'self', 'child', 'parent', 'spouse', or 'other'")
    patient_age: Optional[int] = Field(None, description="Patient age in years if stated")
    chief_complaint: Optional[str] = Field(None, description="Primary symptom or reason for visit")
    duration: Optional[str] = Field(None, description="Duration of symptoms, e.g. '3 din', '2 weeks'")
    severity: Optional[int] = Field(None, description="Pain or symptom severity from 1 (mild) to 10 (unbearable)")
    associated_symptoms: List[str] = Field(default_factory=list, description="Other symptoms mentioned")
    allergies: List[str] = Field(default_factory=list, description="Reported allergies or 'None'")
    current_medications: List[str] = Field(default_factory=list, description="Medicines currently taking")
    medical_history: List[str] = Field(default_factory=list, description="Chronic conditions like diabetes, BP, asthma")
    is_pregnant: Optional[bool] = Field(None, description="True if patient mentions being pregnant")

class IntakeForm(BaseModel):
    """Full structured Intake Form produced by the Intake Agent."""
    patient_relation: str = "self"
    patient_age: Optional[int] = None
    chief_complaint: Optional[str] = None
    duration: Optional[str] = None
    severity: Optional[int] = None # 1-10
    associated_symptoms: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    current_medications: List[str] = Field(default_factory=list)
    medical_history: List[str] = Field(default_factory=list)
    is_pregnant: Optional[bool] = None
    is_complete: bool = False

# =====================================================================
# Intake Agent Implementation
# =====================================================================
class IntakeAgent:
    def __init__(self):
        self.llm = get_llm()
        self.extractor_llm = get_structured_llm(ExtractedIntakeUpdate)

    def extract_from_message(self, message: str, current_form: Dict[str, Any]) -> ExtractedIntakeUpdate:
        """Uses Gemini 3.5 Flash Lite to extract clinical details from the patient's message."""
        prompt = f"""You are an expert clinical intake entity extractor for Pakistani outpatient clinics.
The user is speaking in UrduLish (Roman Urdu + English).
Analyze the user's latest message and extract any clinical intake entities mentioned.

Current known information:
{json.dumps(current_form, indent=2)}

Latest user message:
"{message}"

Extract any mentioned patient relation (self/child/parent), age, chief complaint, duration, severity (1-10 scale), associated symptoms, allergies, current medications, chronic history (diabetes, BP, etc.), and pregnancy status.
If not mentioned in the message, leave the field as null/empty. Do NOT invent details."""
        try:
            extracted = self.extractor_llm.invoke(prompt)
            return extracted
        except Exception as e:
            # Fallback heuristic
            return ExtractedIntakeUpdate()

    def merge_update(self, form: IntakeForm, update: ExtractedIntakeUpdate):
        """Merges newly extracted data into the accumulated IntakeForm."""
        if update.patient_relation:
            form.patient_relation = update.patient_relation.lower()
        if update.patient_age is not None:
            form.patient_age = update.patient_age
        if update.chief_complaint and not form.chief_complaint:
            form.chief_complaint = update.chief_complaint
        elif update.chief_complaint and form.chief_complaint and update.chief_complaint not in form.chief_complaint:
            form.associated_symptoms.append(update.chief_complaint)
        if update.duration:
            form.duration = update.duration
        if update.severity is not None:
            form.severity = update.severity
        if update.associated_symptoms:
            for s in update.associated_symptoms:
                if s not in form.associated_symptoms:
                    form.associated_symptoms.append(s)
        if update.allergies:
            for a in update.allergies:
                if a not in form.allergies:
                    form.allergies.append(a)
        if update.current_medications:
            for m in update.current_medications:
                if m not in form.current_medications:
                    form.current_medications.append(m)
        if update.medical_history:
            for h in update.medical_history:
                if h not in form.medical_history:
                    form.medical_history.append(h)
        if update.is_pregnant is not None:
            form.is_pregnant = update.is_pregnant

    def determine_next_step(self, form: IntakeForm) -> tuple[bool, str]:
        """
        Determines if intake is complete, and if not, generates the single next question in natural UrduLish.
        Rules:
        - Asks ONE question at a time.
        - Warm, respectful, never a long form.
        """
        # 1. Chief complaint missing
        if not form.chief_complaint:
            return False, "Assalam o Alaikum! City Care Clinics mein khushamdeed. Aap ko aaj kya takleef ya masla darpesh hai?"

        # 2. Duration missing
        if not form.duration:
            target = "aap ko" if form.patient_relation == "self" else "mariz ko"
            return False, f"Yeh {form.chief_complaint} kab se hai? Kitne din ya ghante guzar chuke hain?"

        # 3. Severity (1-10) missing
        if form.severity is None:
            return False, "Takleef ki shiddat (severity) 1 se 10 ke scale par kitni hogi? Jahan 1 halki aur 10 shadeed tareen dard ho?"

        # 4. Associated symptoms missing
        if not form.associated_symptoms:
            return False, f"Kya is {form.chief_complaint} ke saath koi aur alamat bhi mehsoos ho rahi hai, jaise bukhar, ulti ya kamzori?"

        # 5. Allergies & current meds missing
        if not form.allergies and not form.current_medications:
            return False, "Kya aap pehle se koi dawa le rahe hain, ya kisi dawa (maslan Penicillin ya Sulfa) se koi allergy hai?"

        # 6. Medical history / Pregnancy / Chronic illnesses check
        if not form.medical_history and form.is_pregnant is None:
            return False, "Kya pehle se koi purani bemari hai, jaise Sugar (Diabetes), High Blood Pressure, ya hamal (pregnancy)?"

        # Everything essential collected!
        form.is_complete = True
        summary_msg = (
            f"Boht shukriya tafseelat faraham karne ka. Main ne aap ki alamaat ({form.chief_complaint}, "
            f"duration: {form.duration}, severity: {form.severity}/10) record kar li hain. "
            f"Ab hum foran aap ke liye munasib specialist aur appointment check karte hain."
        )
        return True, summary_msg

    def process_turn(self, user_message: str, session_form: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Processes a single conversational turn in the Intake workflow.
        Returns:
            {
                "reply": "Assistant response in UrduLish",
                "form": IntakeForm dict,
                "is_complete": bool
            }
        """
        if session_form:
            form = IntakeForm(**session_form)
        else:
            form = IntakeForm()

        # If user message is a greeting or empty initial trigger
        if not form.chief_complaint and any(g in user_message.lower() for g in ["salam", "hello", "hi", "aoa"]):
            # Check if symptoms also mentioned in the greeting
            update = self.extract_from_message(user_message, form.model_dump())
            self.merge_update(form, update)
            is_complete, next_q = self.determine_next_step(form)
            return {
                "reply": next_q,
                "form": form.model_dump(),
                "is_complete": is_complete
            }

        # Extract entities from user message
        update = self.extract_from_message(user_message, form.model_dump())
        self.merge_update(form, update)

        # Determine next question or complete
        is_complete, reply = self.determine_next_step(form)

        return {
            "reply": reply,
            "form": form.model_dump(),
            "is_complete": is_complete
        }


# Singleton instance
intake_agent = IntakeAgent()

if __name__ == "__main__":
    print("Testing Intake Agent multi-turn dialogue...")
    state = None
    turns = [
        "Salam, mere 5 saal ke bete ko bukhar aur khansi hai.",
        "Pichle 3 din se bukhar hai.",
        "Shiddat taqreeban 7/10 hai.",
        "Saath mein gala kharab hai aur thori ulti hui hai.",
        "Panadol syrup diya hai, kisi dawa se allergy nahi hai.",
        "Koi purani bemari nahi hai, bacha aam tor par theek rehta hai."
    ]

    for t in turns:
        print(f"\nUser: '{t}'")
        res = intake_agent.process_turn(t, state)
        state = res["form"]
        print(f"Agent: {res['reply']}")
        print(f"Complete: {res['is_complete']}")

    print("\nFinal Structured Intake Form:")
    print(json.dumps(state, indent=2, ensure_ascii=False))
