# Task 3: Patient Conversation Flows

This document details the conversational design, state transitions, and step-by-step UrduLish dialogues for the seven key patient journeys at City Care Clinics.

---

## Flow 1: New Patient with Fever and Cough (Routine / General Medicine)

### Mermaid Workflow
```mermaid
sequenceDiagram
    autonumber
    actor Patient
    participant Supervisor
    participant Intake as Intake Agent
    participant Triage as Triage Agent
    participant Sched as Scheduling Agent
    participant Summary as Clinical Summary Agent
    participant Doctor as Attending Doctor (HITL)

    Patient->>Supervisor: "Salam, mujhe 3 din se bukhar aur khansi hai."
    Supervisor->>Intake: Route to Intake
    Intake->>Patient: Asks severity, phlegm, difficulty breathing in UrduLish
    Patient->>Intake: "Halka balgham hai, saans theek hai, bukhar 101 F tak jata hai."
    Intake->>Triage: Send structured symptoms
    Triage->>Triage: Evaluate Red Flags (No dyspnea, normal vitals range)
    Note over Triage: Tier = ROUTINE (Specialty = General Medicine)
    Triage->>Supervisor: Triage Result: Routine -> General Medicine
    Supervisor->>Sched: Find available slots
    Sched->>Patient: Present branch & doctor options (Lahore Gulberg / Dr. Usman)
    Patient->>Sched: Selects Tuesday 5:00 PM
    Sched->>Patient: Confirm booking & send preparation instructions
    Sched->>Summary: Trigger pre-consultation SOAP draft
    Summary->>Doctor: Post SOAP note to Doctor Dashboard
```

### Turn-by-Turn Dialogue (UrduLish)
* **Patient:** *"Assalam o Alaikum, mujhe pichle 3 din se tez bukhar aur khansi hai. Doctor ko dikhana hai."*
* **Intake Agent:** *"Wa Alaikum Assalam! City Care Clinics mein khushamdeed. Main aap ki madad karta hoon. Yeh batayein ke bukhar kitna record kiya hai, aur kya saans lene mein koi takleef ya seene mein dard mehsoos ho raha hai?"*
* **Patient:** *"Bukhar taqreeban 101 F hai. Saans lene mein koi takleef nahi hai, bas gala kharab hai aur halka balgham hai."*
* **Intake Agent:** *"Shukriya tafseel batane ka. Kya aap pehle se koi dawa le rahe hain ya kisi dawa se koi allergy hai?"*
* **Patient:** *"Sirf Panadol li hai bukhar ke liye. Koi allergy nahi hai."*
* **Triage Agent (Internal):** Evaluates red-flags. Dyspnea absent, vitals stable, duration 3 days. **Classification: ROUTINE. Recommended Specialty: General Medicine.**
* **Scheduling Agent:** *"Theek hai. Aap ki alamaat ke mutabiq General Physician se check-up munasib rahega. Hamare paas Dr. Usman Tariq (MBBS, FCPS - General Medicine) City Care Gulberg Branch mein dastyab hain:*
  *1) Aaj shaam 6:00 PM*
  *2) Kal subah 11:30 AM*
  *Konsa waqt aap ke liye behtar hoga?"*
* **Patient:** *"Aaj shaam 6:00 PM theek hai."*
* **Scheduling Agent:** *"Aap ki appointment Dr. Usman Tariq ke saath aaj shaam 6:00 PM Gulberg branch mein confirm ho chuki hai (Booking ID: #CC-8421). Bara-e-meharbani waqt se 10 minute pehle tashreef layein. Allah aap ko sehat de!"*

---

## Flow 2: Patient with Chest Pain (Emergency Escalation Path)

### Mermaid Workflow
```mermaid
sequenceDiagram
    autonumber
    actor Patient
    participant Supervisor
    participant Triage as Triage Agent
    participant Safety as Emergency Intercept

    Patient->>Supervisor: "Mere seene mein bohot shadeed dard aur dabao hai..."
    Supervisor->>Triage: Instant Emergency Screening
    Triage->>Triage: RED FLAG TRIGGERED: Acute Chest Pain / Pressure
    Note over Triage: Urgency = EMERGENCY. Halt all booking!
    Triage->>Safety: Lock conversational thread to Emergency Directive
    Safety->>Patient: MANDATORY 1122 RESCUE ALERT (UrduLish + English)
    Safety->>Safety: Send push alert to City Care On-Call ER Officer
```

### Turn-by-Turn Dialogue (UrduLish)
* **Patient:** *"Salam, mere seene mein achanak bohot shadeed dard aur dabao shuru ho gaya hai, bayen baazu (left arm) mein bhi dard ja raha hai aur paseenay aa rahe hain..."*
* **Supervisor / Triage Agent (Instant Intercept):**
* **Triage Agent:**
  > 🚨 **EMERGENCY MEDICAL ALERT / FORI IMDAD**
  >
  > *"Aap ki batai hui alamaat (seene mein shadeed dard, baazu mein phailao, paseenay) nihayat sanjeeda aur EMERGENCY hain. Yeh heart attack ki alamat ho sakti hai.*
  >
  > 🛑 **Foran yeh iqdamat karein:**
  > 1. **Bila-takhir 1122 par call karein** ya qareebi hospital ke Emergency Room (ER) pohanchein.
  > 2. Khud drive mat karein, kisi ko gaari chalane ya sath chalne ka kahein.
  > 3. Seedha laitne ke bajaye aaramdeh posht laga kar baith jayein.
  >
  > ⚠️ *Hamari online appointment ka intizar hargiz na karein. Baraye meharbani foran 1122 rescue call milayein!"*
* **Patient:** *"Kya main koi Panadol ya Disprin le loon?"*
* **Triage Agent:** *"AI assistant dawai tajweez karne ka majaz nahi hai. Agar aap ko pehle doctor ne aisi soorat mein Disprin batayi ho toh alag baat hai, lekin is waqt sab se ahem qadam foran 1122 call karna ya Emergency ward pohanchana hai. Foran madad mangiye!"*

---

## Flow 3: Mother Booking for a Child (Pediatrics)

### Mermaid Workflow
```mermaid
sequenceDiagram
    autonumber
    actor Mother
    participant Supervisor
    participant Intake as Intake Agent
    participant Triage as Triage Agent
    participant Sched as Scheduling Agent

    Mother->>Supervisor: "Mere 4 saal ke bete ko vomiting aur dast hain."
    Supervisor->>Intake: Route to Pediatric Intake
    Intake->>Mother: Collect child age, hydration, lethargy check
    Mother->>Intake: "4 years age, 5 baar vomit hui, paani pee raha hai, hosh mein hai."
    Intake->>Triage: Evaluate pediatric dehydration red flags
    Note over Triage: Child alert, no sunken fontanelle/lethargy -> URGENT (Same day Paeds)
    Triage->>Sched: Route to Pediatric Specialist
    Sched->>Mother: Suggest Paediatrician at nearest branch (DHA Lahore)
    Mother->>Sched: Selects slot & confirms booking
```

### Turn-by-Turn Dialogue (UrduLish)
* **Mother:** *"Assalam o Alaikum, mere 4 saal ke bete Ahmed ko subah se ultiyan aur dast (vomiting & diarrhea) lagay hue hain. Bohot kamzor lag raha hai."*
* **Intake Agent:** *"Wa Alaikum Assalam. Hum samajh sakte hain aap pareshan hongi. Yeh batayein ke bachay ne aakhri dafa peshab (urine) kab kiya tha, aur kya bacha paani ya ORS pee raha hai ya bilkul bhi roak nahi pa raha?"*
* **Mother:** *"Subah 2 ghante pehle peshab kiya tha, ORS thora thora ghunt karke pee raha hai, ulti abhi thori ruki hai lekin thaka hua hai."*
* **Triage Agent (Internal):** Evaluates pediatric status. Age 4 years, not in hypovolemic shock, retaining small sips. **Tier: URGENT (Same Day Consultation with Child Specialist).**
* **Scheduling Agent:** *"Shukriya. Chotay bachon mein paani ki kami (dehydration) jaldi ho sakti hai, is liye aaj hi Paediatrician (Bachon ke doctor) ko dikhana zaroori hai.*
  *City Care DHA Branch mein hamari Paediatrician Dr. Ayesha Malik aaj dopehar 2:30 PM par dastyab hain.*
  *Kya yeh waqt aap ke liye theek hai?"*
* **Mother:** *"Jee bilkul theek hai, please book kar dein."*
* **Scheduling Agent:** *"Ahmed ke liye appointment Dr. Ayesha Malik ke paas aaj 2:30 PM confirm kar di gayi hai (ID: #PED-3091). Clinic aate hue raste mein bache ko chamach se thora thora ORS dete rahein. Agar bacha behosh ho ya peshab 6 ghante tak na kare toh foran Emergency jayein."*

---

## Flow 4: Returning Patient Asking About a Lab Report

### Mermaid Workflow
```mermaid
sequenceDiagram
    autonumber
    actor Patient
    participant Supervisor
    participant Records as Records Agent
    participant Summary as Clinical Summary Agent
    participant Doctor as Doctor (HITL Review)

    Patient->>Supervisor: "Mera kal ka CBC report aa gaya hai, zara batayein kaisa hai?"
    Supervisor->>Records: Retrieve Lab Record via MRN
    Records->>Records: Fetch Hb, WBC, Platelets
    Records->>Patient: Present values with normal reference ranges (Neutral summary)
    Patient->>Records: "WBC 14,000 kyun hai? Kya koi infection hai?"
    Records->>Supervisor: Trigger Doctor Consult Gate
    Note over Records: NEVER DIAGNOSE INFECTION AUTONOMOUSLY
    Supervisor->>Patient: Explain reference range & offer Dr. consult
    Supervisor->>Summary: Generate Lab Interpretation Request for Doctor
```

### Turn-by-Turn Dialogue (UrduLish)
* **Patient:** *"Salam, mera kal City Care lab se CBC ka test hua tha (MRN-90214). Kya aap report dekh kar bata sakte hain ke sab theek hai?"*
* **Records Agent:** *"Wa Alaikum Assalam! Main aap ki report check karta hoon...*
  *Aap ki CBC report (Dated: Kal Shaam) ke nataij yeh hain:*
  *• Haemoglobin (Hb): 13.5 g/dL (Normal Range: 13.0 - 17.0) — Normal*
  *• Platelets: 240,000 /mcL (Normal Range: 150,000 - 450,000) — Normal*
  *• Total Leukocyte Count (WBC): 14,200 /mcL (Normal Range: 4,000 - 11,000) — High"*
* **Patient:** *"WBC 14,200 itna zyada kyun hai? Kya mujhe koi khatarnak infection ya bemari ho gayi hai?"*
* **Records Agent (Safety Guardrail Active):**
  *"Main samajh sakta hoon ke high value dekh kar pareshani hoti hai, lekin aik AI assistant hone ke nate main bimari ki tashkhees (diagnosis) nahi kar sakta. WBC count mein izafa kisi aam gale ki kharash ya jismani stress se bhi ho sakta hai.*
  *Aap ke muallij (doctor) Dr. Tariq aap ki mukammal physical condition dekh kar hi sahi waja bata sakte hain. Kya main aap ke doctor se is report par 10 minute ka tele-consult ya clinic follow-up schedule kar doon?"*
* **Patient:** *"Haan theek hai, follow-up schedule kar dein."*

---

## Flow 5: Reschedule / Cancel Appointment

### Mermaid Workflow
```mermaid
sequenceDiagram
    autonumber
    actor Patient
    participant Supervisor
    participant Sched as Scheduling Agent

    Patient->>Supervisor: "Main kal 4 baje nahi aa sakta, appointment badal dein."
    Supervisor->>Sched: Lookup existing booking
    Sched->>Patient: Show current booking & alternative slots
    Patient->>Sched: Pick Wednesday 6 PM
    Sched->>Sched: Cancel old slot & Reserve new slot in Supabase
    Sched->>Patient: Dispatch updated booking slip
```

### Turn-by-Turn Dialogue (UrduLish)
* **Patient:** *"Salam, meri kal mangal ko 4 baje Dr. Nabila (Gynaecology) ke sath appointment hai. Kisi majboori ki waja se main kal nahi aa sakti, kya yeh badal sakti hai?"*
* **Scheduling Agent:** *"Wa Alaikum Assalam. Jee bilkul, main aap ki booking check kar rahi hoon. Aap ki appointment Dr. Nabila Rehman ke sath kal 4:00 PM City Care Islamabad (F-8 Branch) mein booked hai.*
  *Dr. Nabila ke paas aane wale dino mein yeh auqaat dastyab hain:*
  *1) Budh (Wednesday) shaam 5:30 PM*
  *2) Jumerat (Thursday) dopahar 12:00 PM*
  *Aap ke liye konsa waqt munasib rahega?"*
* **Patient:** *"Budh (Wednesday) shaam 5:30 PM best hai."*
* **Scheduling Agent:** *"Aap ki appointment kamyabi se reschedule kar di gayi hai:*
  *• Doctor: Dr. Nabila Rehman (Gynaecologist)*
  *• Naya Waqt: Budh (Wednesday), Shaam 5:30 PM*
  *• Branch: City Care F-8, Islamabad*
  *• New Booking ID: #RES-5512*
  *Aap ki purani mangal wali booking cancel kar di gayi hai. Shukriya!"*

---

## Flow 6: Patient Asking "Kya main yeh dawai le sakta hoon?" (Medication Safety)

### Mermaid Workflow
```mermaid
sequenceDiagram
    autonumber
    actor Patient
    participant Supervisor
    participant Safety as Prescription Safety Agent
    participant Doctor as Doctor (HITL Gate)

    Patient->>Supervisor: "Kya main Brufen aur Aspirin ek sath le sakta hoon?"
    Supervisor->>Safety: Evaluate Drug-Drug Interaction
    Safety->>Safety: Query Pakistani Drug DB: Ibuprofen + Aspirin
    Note over Safety: Severe GI Bleed Risk + Platelet Inhibition Clash
    Safety->>Supervisor: Flag CRITICAL INTERACTION
    Supervisor->>Patient: Strict Warning + Educational Reason + Refusal to authorize
    Supervisor->>Doctor: Queue medication inquiry on Doctor portal
```

### Turn-by-Turn Dialogue (UrduLish)
* **Patient:** *"Salam, mere sir mein bohot dard ho raha hai aur kamar mein bhi. Main pehle se Dil ki dawai Aspirin (Loprin 75mg) leta hoon. Kya main sath mein Brufen 400mg kha sakta hoon?"*
* **Prescription Safety Agent (Safety Intercept):**
  > ⚠️ **MEDICATION SAFETY WARNING / DAWAYI KI EHTIYAT**
  >
  > *"Nahi! Baraye meharbani Brufen (Ibuprofen) aur Loprin/Aspirin ko aik sath hargiz mat khayein.*
  >
  > **Waja (Clinical Reason):**
  > Yeh dono dawaayein mil kar maiday (stomach) mein shadeed jalan, ulcer aur khoon ke behne (bleeding risk) ko bohot barha deti hain, aur dil ke liye Aspirin ke asar ko bhi mutasir karti hain.
  >
  > 🛑 **Hidayat:**
  > AI assistant aap ko mutabadil (alternative) dawai shuru karne ki ijazat nahi de sakta. Dard ke liye aam tor par sadah Panadol (Paracetamol) istemal ki jati hai agar aap ko jigar (liver) ka masla na ho, lekin aap ko chahiye ke apne doctor se mashwara karein.*
* **Patient:** *"Acha shukriya, main Panadol le leta hoon aur doctor se check karwata hoon."*

---

## Flow 7: Follow-up After a Visit (Adherence & Recovery Check)

### Mermaid Workflow
```mermaid
sequenceDiagram
    autonumber
    participant FollowUp as Follow-up Agent
    actor Patient
    participant Triage as Triage Agent
    participant Doctor as Attending Doctor

    FollowUp->>Patient: Automated WhatsApp message (Day 3 Post-Visit)
    Patient->>FollowUp: "Bukhar toh utar gaya hai lekin pait mein shadeed dard hai."
    FollowUp->>Triage: Re-triage with new symptom (Severe abdominal pain)
    Triage->>Doctor: Urgent Alert: Patient developed new acute symptom
    FollowUp->>Patient: Express concern + Request immediate clinic review
```

### Turn-by-Turn Dialogue (UrduLish)
* **Follow-up Agent (Automated Outreach - Day 3):**
  *"Assalam o Alaikum Janab Tariq Sahab, umeed hai aap khariyat se honge. Yeh City Care Clinics ki taraf se follow-up message hai. 3 din pehle aap Dr. Usman ke paas check-up ke liye tashreef laye thay.*
  *1) Kya aap ne tajweez karda course (Augmentin) baqaidgi se mukammal kiya?*
  *2) Ab aap ki tabiyat kaisi hai aur bukhar kaisa hai?"*
* **Patient:** *"Walaikum Assalam. Bukhar toh bilkul theek ho gaya hai, lekin kal raat se pait ke nichlay hissay mein shadeed dard shuru ho gaya hai aur chakkar aa rahe hain."*
* **Follow-up Agent & Triage Agent (Re-Triage Trigger):**
  *"Yeh jaan kar afsos hua ke aap ko pait mein shadeed dard mehsoos ho raha hai. Chunke bukhar theek hone ke baad yeh aik nayi aur shadeed alamat (acute pain) samne aayi hai, is ko nazar-andaz nahi kiya ja sakta.*
  *Main ne foran Dr. Usman Tariq ko aap ki tabiyat ke bare mein alert bhej diya hai.*
  *Baraye meharbani aaj hi clinic mein check karwayein, ya agar dard bardasht se bahar ho ya behoshi mehsoos ho toh foran Emergency jayein. Kya main Dr. Usman ke sath aaj dopehar ka urgent review slot reserve kar doon?"*
* **Patient:** *"Jee meharbani hogi, jaldi slot book kar dein."*
