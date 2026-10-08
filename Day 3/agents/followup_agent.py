"""
Follow-up Agent for City Care Clinics
Automates post-consultation patient care:
1. Structured Medication Adherence Schedule (morning/noon/night with meal instructions in UrduLish)
2. Diagnostic Lab Test Reminders & Preparation Leaflets
3. Follow-up Visit Scheduling (e.g. Day 5/7 post-visit)
4. Empathetic WhatsApp/SMS Outreach Message Drafting
5. Recovery Feedback Analysis with Re-Triage Escalation
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from llm_factory import get_llm  # type: ignore

class MedicineScheduleItem(BaseModel):
    drug_name: str
    timing_display: str # e.g. "Subah (Morning) 9:00 AM"
    instructions_urdulish: str # e.g. "Nashtay ke baad 1 goli paani ke sath"

class FollowupPlan(BaseModel):
    patient_name: str
    consultation_doctor: str
    medication_schedule: List[MedicineScheduleItem]
    lab_test_reminders: List[Dict[str, str]]
    followup_visit_recommendation: str
    outreach_messages: Dict[str, str] # "day_1", "day_3", "day_7"

class FollowupAgent:
    def __init__(self):
        self.llm = get_llm()

    def generate_care_plan(self, patient_name: str, doctor_name: str,
                           prescribed_meds: List[Dict[str, Any]],
                           advised_labs: Optional[List[str]] = None,
                           followup_days: int = 5) -> FollowupPlan:
        """
        Creates structured medication schedule and automated outreach sequence.
        """
        schedule = []
        for m in prescribed_meds:
            d_name = m.get("drug_name", "Medicine")
            freq = m.get("frequency_per_day", 2)
            if freq == 1:
                schedule.append(MedicineScheduleItem(
                    drug_name=d_name,
                    timing_display="Raat (Night) 09:00 PM",
                    instructions_urdulish="Raat ke khane ke baad 1 goli paani ke sath lein."
                ))
            elif freq == 2:
                schedule.append(MedicineScheduleItem(
                    drug_name=d_name,
                    timing_display="Subah 09:00 AM aur Raat 09:00 PM",
                    instructions_urdulish="Subah nashtay aur raat ke khane ke baad 1 goli lein."
                ))
            elif freq >= 3:
                schedule.append(MedicineScheduleItem(
                    drug_name=d_name,
                    timing_display="Subah 09:00 AM, Dopehar 02:00 PM, Raat 09:00 PM",
                    instructions_urdulish="Khane ke baad din mein 3 martaba barabar waqfay se lein."
                ))

        lab_reminders = []
        if advised_labs:
            for lab in advised_labs:
                prep = "10-12 ghante bhookay reh kar (fasting) aana hai, sirf sadah paani pee sakte hain." if "fasting" in lab.lower() or "lipid" in lab.lower() or "sugar" in lab.lower() else "Koi khas fasting zaroori nahi hai."
                lab_reminders.append({
                    "test_name": lab,
                    "target_day": "Kal subah (Tomorrow morning 08:30 AM)",
                    "preparation_instruction": prep
                })

        # Outreach messages
        day_1_msg = (
            f"Assalam o Alaikum {patient_name} Sahab/Sahiba! Yeh City Care Clinics ki taraf se yaad-dihani hai. "
            f"Dr. {doctor_name} ki tajweez karda dawaayein baqaidgi se shuru kar lein. Kisi bhi mushkil ki soorat mein hum hazir hain."
        )
        day_3_msg = (
            f"Assalam o Alaikum {patient_name} Sahab/Sahiba! 3 din ho gaye hain. Ab aap ki tabiyat kaisi hai aur alamaat mein kitna aaram hai? "
            f"Baraye meharbani mukhtasir batayein taake doctor ko update kiya ja sakay."
        )
        day_7_msg = (
            f"Assalam o Alaikum {patient_name} Sahab/Sahiba! Aap ka {followup_days}-roza course mukammal hone ke qareeb hai. "
            f"Kya aap Dr. {doctor_name} ke sath follow-up review slot schedule karna chahenge? (City Care Clinics)"
        )

        return FollowupPlan(
            patient_name=patient_name,
            consultation_doctor=doctor_name,
            medication_schedule=schedule,
            lab_test_reminders=lab_reminders,
            followup_visit_recommendation=f"Dr. {doctor_name} ke sath {followup_days} din baad clinic follow-up zaroori hai.",
            outreach_messages={
                "day_1_adherence_check": day_1_msg,
                "day_3_symptom_review": day_3_msg,
                "day_7_followup_reminder": day_7_msg
            }
        )

    def process_patient_feedback(self, patient_feedback: str) -> Dict[str, Any]:
        """
        Evaluates patient response to 'How are you feeling?' check-in.
        Detects worsening symptoms and triggers urgent re-triage escalation.
        """
        text_lower = patient_feedback.lower()
        import re
        worsening_patterns = [
            r"kharab", r"barh (gaya|gayi|raha|rahi)", r"nahi (utra|kam|theek|behtar)",
            r"saans.*(phool|takleef|ruk)", r"ulti", r"chakkar", r"behosh",
            r"shadeed", r"worse", r"bleeding|khoon", r"seen(a|e).*(dard|dabao|pressure)",
            r"dawa.*reaction", r"allergy", r"emergency", r"pain|takleef"
        ]

        is_worsening = any(re.search(pat, text_lower) for pat in worsening_patterns)

        if is_worsening:
            return {
                "status": "ESCALATION_REQUIRED",
                "is_worsening": True,
                "reply_to_patient": (
                    "⚠️ Yeh jaan kar afsos hua ke tabiyat mein behtari nahi aayi balkay takleef barh rahi hai. "
                    "Chunke alamaat mein mazeed shiddat aayi hai, isay nazar-andaz nahi kiya ja sakta. "
                    "Hum ne aap ke muallij doctor ko foran alert bhej diya hai. Baraye meharbani aaj hi clinic review ke liye tashreef layein ya agar shadeed takleef ho toh foran Emergency jayein!"
                ),
                "action": "TRIGGER_RE_TRIAGE"
            }
        else:
            return {
                "status": "RECOVERY_PROGRESSING",
                "is_worsening": False,
                "reply_to_patient": (
                    "Alhamdulillah, yeh jaan kar bohot khushi hui ke tabiyat behtar hai! "
                    "Baraye meharbani doctor ki tajweez karda dawai ka course poora karein aur paani ka istemal zyada rakhein. Allah aap ko kamil sehat ata farmaye."
                ),
                "action": "LOG_SATISFACTION"
            }


# Singleton instance
followup_agent = FollowupAgent()

if __name__ == "__main__":
    print("Testing Follow-up Agent...")
    plan = followup_agent.generate_care_plan(
        patient_name="Ahmed Raza",
        doctor_name="Usman Tariq",
        prescribed_meds=[
            {"drug_name": "Augmentin 625mg", "frequency_per_day": 2},
            {"drug_name": "Panadol 500mg", "frequency_per_day": 3}
        ],
        advised_labs=["Fasting Blood Sugar", "CBC"],
        followup_days=5
    )
    print("\nMedication Schedule Items:", len(plan.medication_schedule))
    print("Day 3 Outreach Message:\n", plan.outreach_messages["day_3_symptom_review"])

    # Test feedback processing
    fb = followup_agent.process_patient_feedback("Bukhar theek ho gaya hai lekin pait mein shadeed dard shuru ho gaya hai")
    print("\nFeedback Evaluation Status:", fb["status"])
    print("Action:", fb["action"])
