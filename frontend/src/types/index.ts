export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  agent?: string;
  timestamp: string;
  audio_url?: string;
  metadata?: {
    triage_level?: string;
    triage_reason?: string;
    requires_hitl?: boolean;
    hitl_task_id?: string;
    lab_report?: any;
    appointment_ref?: string;
    [key: string]: any;
  };
}

export interface Patient {
  id?: string;
  mrn?: string;
  patient_id?: string;
  patient_name: string;
  phone: string;
  age: number;
  gender: string;
  blood_group?: string;
  address?: string;
  allergies?: string[];
  known_allergies?: string[];
  chronic_conditions?: string[];
  created_at?: string;
}

export interface DoctorAccount {
  id?: string;
  doctor_id?: string;
  doctor_name: string;
  specialty: string;
  email: string;
  qualification?: string;
  experience?: string;
  consultation_fee?: number;
  available_days?: string[];
  timing?: string;
  pmdc_number?: string;
}

export interface DoctorDirectoryItem {
  id?: string;
  doctor_id?: string;
  full_name?: string;
  doctor_name?: string;
  specialty?: string;
  qualification?: string;
  experience?: string;
  experience_years?: number;
  consultation_fee?: number;
  available_days?: string[];
  timing?: string;
  rating?: number;
  image?: string;
  pmdc_number?: string;
  gender?: string;
  languages?: string[];
  branch_id?: string;
  branch_name?: string;
  branch_city?: string;
  branch_address?: string;
}

export interface DoctorScheduleSlot {
  slot_id: string;
  time: string;
  status: "available" | "booked" | "blocked";
  patient_name?: string;
  appointment_id?: string;
}

export interface DoctorScheduleData {
  doctor_id?: string;
  doctor_name?: string;
  specialty?: string;
  doctor?: DoctorDirectoryItem;
  date?: string;
  slots?: DoctorScheduleSlot[];
  available_slots?: any[];
  booked_appointments?: any[];
  total_booked?: number;
  total_available?: number;
  is_fully_booked?: boolean;
  suggested_alternatives?: any[];
}

export interface Appointment {
  appointment_id?: string;
  id?: string;
  booking_reference?: string;
  booking_ref?: string;
  doctor_id?: string;
  doctor_name?: string;
  specialty?: string;
  patient_id?: string;
  patient_name?: string;
  phone?: string;
  mrn?: string;
  date?: string;
  time_slot?: string;
  time?: string;
  reason?: string;
  status?: "confirmed" | "completed" | "cancelled" | string;
  created_at?: string;
  prescription?: any;
  prescription_id?: string;
}

export interface PatientFullHistory {
  patient?: Patient;
  patient_id?: string;
  patient_name?: string;
  mrn?: string;
  phone?: string;
  age?: number;
  gender?: string;
  preferred_doctor?: string;
  preferred_branch?: string;
  preferred_language?: string;
  known_allergies?: string[];
  chronic_conditions?: string[];
  past_complaints?: string[];
  last_visit_date?: string;
  encounters?: any[];
  observations?: any[];
  medications?: any[];
  soap_note?: any;
  appointments?: Appointment[];
  prescriptions?: any[];
  lab_reports?: any[];
  clinical_summary?: string;
}

export interface HITLTask {
  task_id: string;
  thread_id?: string;
  session_id?: string;
  patient_id?: string;
  patient_name?: string;
  reason?: string;
  task_type?: "LAB_EXPLANATION" | "PRESCRIPTION_REVIEW" | "LOW_CONFIDENCE_TRIAGE" | string;
  urgency_level?: string;
  proposed_message_urdulish?: string;
  patient_message?: string;
  proposed_response?: string;
  clinical_context?: any;
  agent_chain?: string[];
  status: "pending" | "approved" | "rejected" | "PENDING" | "APPROVED" | "EDITED" | "REJECTED";
  created_at: string;
  resolved_at?: string;
  doctor_action?: string;
  doctor_notes?: string;
  final_message_urdulish?: string;
}

export interface TelemetryStats {
  avg_latency_ms: number;
  total_conversations: number;
  total_tokens: number;
  total_cost_usd: number;
  hitl_interventions: number;
  emergency_escalations?: number;
  active_agents_count?: number;
}

export interface LabSample {
  filename: string;
  label: string;
  category?: string;
  size_kb: number;
}

export interface LabTestParam {
  test_name: string;
  result_value?: string | number;
  numeric_value?: string | number;
  unit: string;
  reference_range?: string;
  reference_range_str?: string;
  reference_range_low?: number;
  reference_range_high?: number;
  flag?: string;
  status?: "Normal" | "High" | "Low" | "Critical" | string;
  clinical_significance?: string;
}

export interface LabAnalysisResult {
  report_id?: string;
  patient_name?: string;
  patient_mrn?: string;
  mrn?: string;
  date?: string;
  collection_date?: string;
  panel?: string;
  laboratory_name?: string;
  tests: LabTestParam[];
  urdulish_summary: string;
  english_summary?: string;
  abnormal_count?: number;
  critical_deviations_count?: number;
  is_diagnostic_disclaimer_present?: boolean;
  total_tests_count?: number;
  raw_text?: string;
  extraction_method?: string;
}

export type ActiveTab = "patient" | "doctor" | "lab" | "telemetry";
export type PatientSubTab = "chat" | "schedule" | "my_appointments";
export type DoctorSubTab = "dossier" | "appointments" | "approvals";
