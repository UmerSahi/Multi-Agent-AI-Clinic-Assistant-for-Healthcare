"""
Human-in-the-Loop (HITL) Doctor Approval Engine for City Care Clinics
Manages interrupt-and-approve gates for:
1. Any lab result explanation dispatched to a patient
2. Any prescription-related advice or draft medicine list
3. Any triage decision with low confidence (< 0.85) or borderline presentation
Allows the attending physician to Approve, Edit, or Reject with clinical notes.
"""

import sys
import uuid
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Literal

DAY4_DIR = Path(__file__).resolve().parent
DATA_DIR = DAY4_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
HITL_QUEUE_FILE = DATA_DIR / "hitl_queue.json"


class HITLManager:
    """Coordinates doctor review tasks, interrupts, and approval states."""

    def __init__(self):
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._load_queue()

    def _load_queue(self):
        """Loads pending and historic HITL approval tasks."""
        if HITL_QUEUE_FILE.exists():
            try:
                with open(HITL_QUEUE_FILE, "r", encoding="utf-8") as f:
                    self._tasks = json.load(f)
                    return
            except Exception as e:
                print(f"[HITL Warning] Could not parse queue file: {e}")
        self._tasks = {}

    def _save_queue(self):
        """Persists HITL tasks to disk."""
        try:
            with open(HITL_QUEUE_FILE, "w", encoding="utf-8") as f:
                json.dump(self._tasks, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[HITL Error] Could not save queue: {e}")

    def create_pending_approval(
        self,
        thread_id: str,
        patient_id: Optional[str],
        patient_name: str,
        task_type: Literal["LAB_EXPLANATION", "PRESCRIPTION_REVIEW", "LOW_CONFIDENCE_TRIAGE"],
        proposed_message_urdulish: str,
        clinical_context: Dict[str, Any],
        urgency_level: str = "ROUTINE"
    ) -> Dict[str, Any]:
        """
        Creates a pending doctor approval task and puts the conversation thread on hold.
        """
        task_id = f"HITL-{uuid.uuid4().hex[:8].upper()}"
        task_record = {
            "task_id": task_id,
            "thread_id": thread_id,
            "patient_id": patient_id,
            "patient_name": patient_name,
            "task_type": task_type,
            "urgency_level": urgency_level,
            "proposed_message_urdulish": proposed_message_urdulish,
            "clinical_context": clinical_context,
            "status": "PENDING",  # PENDING, APPROVED, EDITED, REJECTED
            "created_at": datetime.now(timezone.utc).isoformat(),
            "resolved_at": None,
            "doctor_action": None,
            "doctor_notes": None,
            "final_message_urdulish": None
        }

        self._tasks[task_id] = task_record
        self._save_queue()
        return task_record

    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """Returns all unresolved approval tasks sorted by urgency and time."""
        pending = [t for t in self._tasks.values() if t["status"] == "PENDING"]
        # Prioritize emergency/urgent over routine
        priority_map = {"EMERGENCY": 0, "URGENT": 1, "ROUTINE": 2}
        pending.sort(key=lambda x: (priority_map.get(x.get("urgency_level", "ROUTINE"), 2), x["created_at"]))
        return pending

    def get_task_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Finds task by ID."""
        return self._tasks.get(task_id)

    def find_pending_task_by_thread(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Finds active pending task for a specific conversation thread."""
        for t in self._tasks.values():
            if t["thread_id"] == thread_id and t["status"] == "PENDING":
                return t
        return None

    def process_doctor_decision(
        self,
        task_id: str,
        decision: Literal["approved", "edited", "rejected"],
        doctor_notes: Optional[str] = None,
        edited_message: Optional[str] = None,
        doctor_name: str = "Dr. Maryam Naveed (Medical Director)"
    ) -> Dict[str, Any]:
        """
        Applies doctor's review decision and resolves the pending gate:
        - approved: Dispatches original proposed message
        - edited: Replaces with physician's edited message
        - rejected: Suppresses clinical message and returns physician guidance
        """
        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"HITL task {task_id} not found.")

        if task["status"] != "PENDING":
            return task  # Already resolved

        resolved_time = datetime.now(timezone.utc).isoformat()
        final_message = ""

        if decision == "approved":
            status = "APPROVED"
            final_message = task["proposed_message_urdulish"]
        elif decision == "edited":
            status = "EDITED"
            final_message = edited_message or task["proposed_message_urdulish"]
        elif decision == "rejected":
            status = "REJECTED"
            final_message = (
                f"Aap ka case hamaray senior doctor ({doctor_name}) ne review kiya hai. "
                f"Doctor ki hidayat ke mutabiq yeh maloomat clinic mein direct mashwaray ke baad di jaye gi. "
                f"Baraye meharbani clinic visit ke liye appointment schedule karein."
            )
            if doctor_notes:
                final_message += f"\n\nDoctor Note: {doctor_notes}"
        else:
            raise ValueError(f"Invalid decision '{decision}'. Must be 'approved', 'edited', or 'rejected'.")

        task["status"] = status
        task["doctor_action"] = decision
        task["doctor_name"] = doctor_name
        task["doctor_notes"] = doctor_notes
        task["final_message_urdulish"] = final_message
        task["resolved_at"] = resolved_time

        self._save_queue()
        return task


# Singleton instance
hitl_manager = HITLManager()

if __name__ == "__main__":
    print("Testing HITL Manager...")
    task = hitl_manager.create_pending_approval(
        thread_id="test_thread_01",
        patient_id="p1",
        patient_name="Ahmed Raza",
        task_type="PRESCRIPTION_REVIEW",
        proposed_message_urdulish="Aap ko Augmentin 625mg tajweez ki ja rahi hai din mein 2 dafa.",
        clinical_context={"allergies": ["Penicillin"], "warning": "Allergy cross-reactivity"},
        urgency_level="URGENT"
    )
    print("Created Task:", task["task_id"])
    print("Pending Count:", len(hitl_manager.get_pending_tasks()))

    # Resolve with edit
    resolved = hitl_manager.process_doctor_decision(
        task_id=task["task_id"],
        decision="edited",
        edited_message="⚠️ Penicillin allergy ki waja se Augmentin ke bajaye Azithromycin 500mg tajweez ki ja rahi hai.",
        doctor_notes="Substituted Augmentin with Macrolide due to documented Penicillin anaphylaxis risk."
    )
    print("Resolved Status:", resolved["status"])
    print("Final Message:", resolved["final_message_urdulish"])
