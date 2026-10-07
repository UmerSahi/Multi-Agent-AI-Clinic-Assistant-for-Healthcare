# Task 4: Safety & Triage Policy

This document defines the clinical safety policies, danger sign taxonomies, triage decision matrices, exact UrduLish escalation verbiage, and clinical boundary rules for the City Care Clinics AI Assistant.

---

## 1. Red-Flag Symptom Taxonomy (Immediate Escalation Triggers)

Any mention or semantic equivalence of the following conditions triggers an immediate **EMERGENCY TIER** classification and halts the standard conversational flow.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        CITY CARE CLINICS RED-FLAG TAXONOMY                             │
├─────────────────────┬─────────────────────────────────┬────────────────────────────────┤
│ Clinical Domain     │ English Clinical Indicators     │ UrduLish Triggers              │
├─────────────────────┼─────────────────────────────────┼────────────────────────────────┤
│ 1. Cardiovascular   │ Acute central chest pain, crushing│ "Seene mein shadeed dard/dabao",│
│                     │ pressure, pain radiating to jaw │ "bayen baazu mein dard",        │
│                     │ or left arm, diaphoresis.       │ "chhati pe wazan", "paseenay"  │
├─────────────────────┼─────────────────────────────────┼────────────────────────────────┤
│ 2. Respiratory      │ Severe dyspnea, gasping, stridor│ "Saans lene mein shadeed takleef",│
│                     │ inability to speak in sentences,│ "saans phool rahi hai",         │
│                     │ cyanosis (blue lips/fingers).   │ "neela rang parh raha hai"     │
├─────────────────────┼─────────────────────────────────┼────────────────────────────────┤
│ 3. Neurological     │ FAST criteria: Facial droop,    │ "Munh teda ho gaya hai",       │
│    (Stroke / Trauma)│ Arm weakness, Slurred speech,   │ "baazu sun/kamzor hai",         │
│                     │ sudden syncope, active seizures.│ "awaz ladkhada rahi hai", behoshi│
├─────────────────────┼─────────────────────────────────┼────────────────────────────────┤
│ 4. Hemorrhagic      │ Massive active bleeding, coughing│ "Bohot zyada khoon beh raha hai",│
│                     │ blood (hemoptysis), vomiting    │ "khoon ki ulti", "kala pakhana",│
│                     │ blood (hematemesis), melena.    │ "khoon ke qatray band nahi hote"│
├─────────────────────┼─────────────────────────────────┼────────────────────────────────┤
│ 5. Pediatric Alert  │ Age < 3 months with fever > 38°C│ "3 mahine se chota bacha aur    │
│                     │ (100.4°F), inconsolable crying, │ tez bukhar", "doodh nahi pee   │
│                     │ sunken eyes/fontanelle, lethargy│ raha", "gardana akad gayi hai" │
├─────────────────────┼─────────────────────────────────┼────────────────────────────────┤
│ 6. Obstetric        │ Vaginal bleeding in pregnancy,   │ "Hamal mein khoon aana",        │
│                     │ severe sudden pelvic pain,      │ "shadeed pait dard pregnancy mein"│
│                     │ convulsions (eclampsia).        │ "danday/jhatkay lagna"         │
├─────────────────────┼─────────────────────────────────┼────────────────────────────────┤
│ 7. Anaphylaxis      │ Swelling of lips, tongue, face, │ "Hont/zaban soojh gaye hain",   │
│                     │ sudden diffuse hives + wheezing.│ "dawa ke baad saans band hona" │
├─────────────────────┼─────────────────────────────────┼────────────────────────────────┤
│ 8. Psychiatric      │ Active suicidal ideation, intent│ "Apni jaan lene ka dil kar raha",│
│                     │ of self-harm, violent psychosis.│ "khudkushi ki sochain", "awaazein"│
└─────────────────────┴─────────────────────────────────┴────────────────────────────────┘
```

---

## 2. Urgency Tiers & SLA Matrix

The system classifies every incoming patient into one of three clinical urgency categories:

| Triage Level | Clinical Definition | Target SLA | System Routing Action |
| :--- | :--- | :--- | :--- |
| **Tier 1: EMERGENCY** | Life, limb, or organ-threatening conditions requiring resuscitation or immediate ER stabilization. | **< 0 Minutes (Instant)** | **Halt all booking.** Display 1122 alert, push notification to clinic ER doctor, suggest nearest physical hospital. |
| **Tier 2: URGENT** | Acute, distressing, or rapidly progressive symptoms without immediate danger of collapse (e.g., pediatric vomiting, high fever > 102°F, suspected fracture, severe eye trauma). | **Within 2–4 Hours (Same Day)** | Priority routing to same-day urgent slot at closest open branch. Notify triage nurse desk. |
| **Tier 3: ROUTINE** | Chronic condition follow-up, mild symptoms > 48h, routine dermatology, health checks, general inquiries. | **24–72 Hours** | Standard calendar booking across regular doctor consultation hours. |

---

## 3. Standard Escalation Messages (UrduLish)

### A. Primary Emergency Message (1122 Dispatch)
```
🚨 EMERGENCY ALERT / FORI IMDAD KI ZAROORAT:

Aap ki batai hui alamaat nihayat sanjeeda aur khatarnak ho sakti hain. 

Baraye meharbani foran 1122 par call karein ya apne qareebi hospital ke Emergency Ward jayein.

Khas Hidayat:
1. Khud drive na karein, kisi ko gaari chalane ka kahein ya 1122 ambulance ka intezar karein.
2. Aam clinic appointment ka intezar hargiz na karein; yeh waqt zaya karne ke mutaradif hoga.
3. Agar mariz behosh ho raha ho toh usay seedha lita kar gardan azaad rakhein.

City Care Clinics Helpline: 042-111-CARE-00 (Emergency Coordination)
```

### B. Urgent Same-Day Care Message
```
⚠️ URGENT MEDICAL ATTENTION REQUIRED / AAJ HI CHECK-UP ZAROORI HAI:

Aap ki alamaat ko dekhte hue behtar hai ke aap ko aaj hi doctor check karein taake tabiyat mazeed na bigray.

Hum ne aap ke liye City Care [Branch Name] mein aaj [Time] ka Urgent Review slot dastyab paya hai. 

Kya hum yeh slot aap ke liye book kar dein? Agar is dauran tabiyat achanak kharab ho ya saans mein dushwari aaye toh foran 1122 milayein.
```

### C. Psychiatric Crisis (Self-Harm Protocol)
```
🕊️ AAP TANHA NAHI HAIN / EMOTIONAL SUPPORT:

Agar aap ya aap ka koi pyara shadeed zehni dabao mein hai ya apni jaan ko nuqsan pohanchane ka soch raha hai, toh baraye meharbani foran madad lein:

• Pakistan Mental Health Helpline: 0800-44888
• Rescue 1122 Emergency Services
• Umang Pakistan Mental Health Helpline: 0311-7786264

City Care Clinics mein hamare Psychiatrists aur Counselors bhi dastyab hain. Baraye meharbani foran kisi pyare ya helpline se rabta karein.
```

---

## 4. Boundary Matrix: What the AI May Say vs. What Only a Doctor May Say

| Capability / Interaction | AI Clinic Assistant (Allowed) | Licensed Medical Doctor (Exclusive) |
| :--- | :---: | :---: |
| Greet patient and collect symptoms | ✅ Yes (Intake Agent) | ✅ Yes |
| Ask duration, severity, and onset | ✅ Yes | ✅ Yes |
| Explain standard lab reference ranges | ✅ Yes (Neutral context) | ✅ Yes |
| Confirm appointment dates & fees | ✅ Yes | ✅ Yes |
| **Diagnose a specific illness** (*"Aap ko typhoid hai"*) | ❌ **STRICTLY FORBIDDEN** | ✅ **Doctor Only** |
| **Prescribe medicine or dose** (*"Yeh goli 2 time khayein"*) | ❌ **STRICTLY FORBIDDEN** | ✅ **Doctor Only** |
| **Recommend stopping a prescription** | ❌ **STRICTLY FORBIDDEN** | ✅ **Doctor Only** |
| Flag known drug-drug clashes to doctor | ✅ Yes (Prescription Safety) | ✅ Yes |
| Order invasive diagnostic tests | ❌ **STRICTLY FORBIDDEN** | ✅ **Doctor Only** |
| Sign off on disability/fit-to-work certificates | ❌ **STRICTLY FORBIDDEN** | ✅ **Doctor Only** |

---

## 5. Mandatory Disclaimers

### Global Chat Disclaimer (Displayed at First Interaction)
> *"City Care Clinics AI Assistant aik automated sahulat hai jo appointments aur basic maloomat ke liye banayi gayi hai. Yeh kisi licensed doctor ka mutabadil nahi hai aur na hi khud bemari ki tashkhees ya dawai tajweez karta hai. Kisi bhi emergency ki soorat mein foran 1122 milayein."*

### Lab Report Disclaimer (Appended to all Lab Queries)
> *"Lab ke nataij sirf maloomati maqasid ke liye hain. Mukammal tashkhees aur ilaj ke liye doctor ka mushahida aur hidayat lazmi hai."*

### Prescription Verification Disclaimer (Appended to Doctor Briefs)
> *"Prescription Safety Agent checks are algorithmic screenings based on open pharmaceutical databases. Final prescribing responsibility rests solely with the registered treating physician."*
