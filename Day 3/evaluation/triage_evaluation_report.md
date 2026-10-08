# 50-Scenario Clinical Triage Benchmark Report
**Date:** 2026-10-08  
**Triage Architecture:** Two-Tier Hybrid (Deterministic Rule Screener + Gemini 3.5 Flash Lite Urgency Classifier)

---

## 📊 Performance Summary

| Metric | Target Standard | Achieved Score | Evaluation Status |
| :--- | :---: | :---: | :---: |
| **Emergency Recall** | **100.0%** (Mandatory) | **100.0%** (20/20) | ✅ PASSED |
| **Under-Triage Rate** | **0.0%** (Zero False Negatives) | **0.0%** (0 Cases) | ✅ PASSED |
| **Over-Triage Rate** | ≤ 5.0% | **0.0%** (0 Cases) | ✅ PASSED |
| **Overall Triage Accuracy** | ≥ 92.0% | **100.0%** (50/50) | ✅ PASSED |

---

## 📋 Comprehensive 50-Scenario Result Breakdown

| ID | Clinical Scenario / Chief Complaint | Expected Tier | System Triage | Confidence | Match Status |
| :-: | :--- | :---: | :---: | :---: | :-: |
| 1 | Seene mein shadeed dard aur bayen baazu mein phailao, paseenay aa... | EMERGENCY | EMERGENCY | 1.00 | ✅ Match |
| 2 | Patient has crushing chest pain and acute shortness of breath... | EMERGENCY | EMERGENCY | 1.00 | ✅ Match |
| 3 | Chhati pe bohot shadeed wazan aur gasping ho rahi hai... | EMERGENCY | EMERGENCY | 1.00 | ✅ Match |
| 4 | Saans lene mein shadeed takleef aur hont neelay parh rahe hain... | EMERGENCY | EMERGENCY | 1.00 | ✅ Match |
| 5 | Inability to breathe, severe stridor and airway choking sensation... | EMERGENCY | EMERGENCY | 1.00 | ✅ Match |
| 6 | Achanak munh teda ho gaya hai aur bayen baazu mein taqat khatam h... | EMERGENCY | EMERGENCY | 1.00 | ✅ Match |
| 7 | Sudden facial droop and slurred speech over last 20 minutes... | EMERGENCY | EMERGENCY | 1.00 | ✅ Match |
| 8 | Mariz achanak behosh ho kar gir parha hai aur koi jawab nahi de r... | EMERGENCY | EMERGENCY | 1.00 | ✅ Match |
| 9 | Continuous epileptic convulsions / active seizures lasting 5 minu... | EMERGENCY | EMERGENCY | 1.00 | ✅ Match |
| 10 | Khoon ki ulti (hematemesis) achanak shuru ho gayi hai bohot zyada... | EMERGENCY | EMERGENCY | 1.00 | ✅ Match |
| 11 | Coughing large amounts of fresh red blood and severe breathlessne... | EMERGENCY | EMERGENCY | 1.00 | ✅ Match |
| 12 | Shadeed active bleeding from deep laceration wound that won't sto... | EMERGENCY | EMERGENCY | 1.00 | ✅ Match |
| 13 | 2 mahine ka bacha hai aur 101 F bukhar hai doodh bilkul nahi pee ... | EMERGENCY | EMERGENCY | 1.00 | ✅ Match |
| 14 | Infant under 3 months with high fever and extreme lethargy... | EMERGENCY | EMERGENCY | 1.00 | ✅ Match |
| 15 | Hamal (pregnancy) ke 7vein mahine mein shadeed vaginal bleeding s... | EMERGENCY | EMERGENCY | 1.00 | ✅ Match |
| 16 | Severe acute lower abdominal agony with pregnancy bleeding... | EMERGENCY | EMERGENCY | 1.00 | ✅ Match |
| 17 | Injection lagne ke baad achanak hont soojh gaye aur saans band ho... | EMERGENCY | EMERGENCY | 1.00 | ✅ Match |
| 18 | Acute anaphylaxis with diffuse hives and tongue swelling... | EMERGENCY | EMERGENCY | 1.00 | ✅ Match |
| 19 | Patient expressing active suicidal intent and planning to take li... | EMERGENCY | EMERGENCY | 1.00 | ✅ Match |
| 20 | Jaan lene ka irada kar raha hoon bohot hopeless hoon... | EMERGENCY | EMERGENCY | 1.00 | ✅ Match |
| 21 | 4 saal ke bachay ko subah se 6 dafa patlay dast aur ulti hai, kam... | URGENT | URGENT | 0.95 | ✅ Match |
| 22 | High continuous fever 103 F with severe chills for past 24 hours... | URGENT | URGENT | 0.95 | ✅ Match |
| 23 | Kaan mein achanak shadeed dard aur peeli peep beh rahi hai... | URGENT | URGENT | 0.95 | ✅ Match |
| 24 | Acute severe right lower quadrant abdominal pain starting 4 hours... | URGENT | URGENT | 0.95 | ✅ Match |
| 25 | Pao par wazan nahi daal sakta, girne se shadeed soojan aa gayi ha... | URGENT | URGENT | 0.85 | ✅ Match |
| 26 | Bacha saari raat rotay hue guzar raha hai aur kaan khench raha ha... | URGENT | URGENT | 0.95 | ✅ Match |
| 27 | Acute throbbing hemicranial migraine with severe nausea... | URGENT | URGENT | 0.85 | ✅ Match |
| 28 | Blood pressure reading is 170/105 mmHg with moderate occipital he... | URGENT | URGENT | 0.95 | ✅ Match |
| 29 | Severe burning upon urination with fever and flank discomfort... | URGENT | URGENT | 0.95 | ✅ Match |
| 30 | Rapidly spreading warm red skin rash on lower leg (suspected cell... | URGENT | URGENT | 0.95 | ✅ Match |
| 31 | Known asthmatic having moderate wheezing partially responding to ... | URGENT | URGENT | 0.90 | ✅ Match |
| 32 | Eye trauma from dust scratch with redness, photophobia and wateri... | URGENT | URGENT | 0.90 | ✅ Match |
| 33 | Shadeed gale mein soojan jis ki waja se thook nigalna mushkil ho ... | URGENT | URGENT | 0.95 | ✅ Match |
| 34 | Uncontrolled persistent vomiting in early pregnancy (hyperemesis)... | URGENT | URGENT | 0.90 | ✅ Match |
| 35 | High fever 102 F in a diabetic with foot blister swelling... | URGENT | URGENT | 0.95 | ✅ Match |
| 36 | Halka bukhar aur khansi 4 din se hai, saans bilkul theek hai... | ROUTINE | ROUTINE | 0.95 | ✅ Match |
| 37 | Dry tickly cough for 2 weeks after a mild common cold... | ROUTINE | ROUTINE | 0.75 | ✅ Match |
| 38 | Chehre par keel, daanay aur blackheads pichle 3 mahine se... | ROUTINE | ROUTINE | 0.99 | ✅ Match |
| 39 | Routine follow-up for stable Type 2 Diabetes blood sugar review... | ROUTINE | ROUTINE | 0.99 | ✅ Match |
| 40 | Kamar mein halka dard rehta hai daftar mein zyada baithne se... | ROUTINE | ROUTINE | 0.95 | ✅ Match |
| 41 | Chronic mild dandruff and itchy scalp on and off for 6 months... | ROUTINE | ROUTINE | 0.98 | ✅ Match |
| 42 | Routine prenatal 2nd trimester ultrasound and checkup booking... | ROUTINE | ROUTINE | 0.99 | ✅ Match |
| 43 | Ear wax blockage causing slightly reduced hearing in right ear... | ROUTINE | ROUTINE | 0.95 | ✅ Match |
| 44 | Gradual hair thinning and loss at the crown over past year... | ROUTINE | ROUTINE | 0.95 | ✅ Match |
| 45 | Fasting blood sugar 125 mg/dL, wants doctor advice on diet... | ROUTINE | ROUTINE | 0.95 | ✅ Match |
| 46 | Mild seasonal allergic sneezing in spring mornings... | ROUTINE | ROUTINE | 0.95 | ✅ Match |
| 47 | Routine child growth milestone checkup and vaccination counseling... | ROUTINE | ROUTINE | 1.00 | ✅ Match |
| 48 | Fungal ringworm rash on arm for past 2 weeks... | ROUTINE | ROUTINE | 0.95 | ✅ Match |
| 49 | Fatigue and generalized mild weakness after long work hours... | ROUTINE | ROUTINE | 0.95 | ✅ Match |
| 50 | Refill prescription inquiry for ongoing cholesterol medicine... | ROUTINE | ROUTINE | 1.00 | ✅ Match |

---

## 🛡️ Medical Safety & Rule-Based Guarantee
1. **Zero Overrides on Life-Threatening Conditions:** All 20 emergency presentations (chest pain, dyspnea, FAST stroke signs, active major bleeding, infant fever, anaphylaxis, and acute suicidal crisis) triggered the deterministic screener with 1.0 confidence and immediate 1122 dispatch.
2. **Zero Under-Triage:** Under-triage on life-threatening conditions is exactly 0.0%, satisfying the primary safety constraint of the Capstone project.
3. **Appropriate Outpatient Resource Utilization:** Urgent cases are routed to same-day slots without needlessly flooding tertiary hospital ERs.
