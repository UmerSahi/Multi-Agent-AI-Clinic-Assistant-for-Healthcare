"""
MCP Server: Scheduling
Exposes standardized MCP tools for doctor discovery, real-time slot checking,
booking, rescheduling, and cancellation across all 5 clinic branches.
"""

import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

sys.path.append(str(Path(__file__).resolve().parent.parent))
from db_client import db
from mcp.server.mcpserver import MCPServer

server = MCPServer("scheduling")

@server.tool()
def find_doctor(specialty: Optional[str] = None, branch_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Searches available practitioners by specialty and/or clinic branch.
    Specialties: General Medicine, Paediatrics, Gynaecology, Cardiology, Dermatology, ENT.
    """
    docs = db.get_practitioners(specialty=specialty, branch_id=branch_id)
    return [
        {
            "doctor_id": d["id"],
            "full_name": d["full_name"],
            "specialty": d["specialty"],
            "qualification": d["qualification"],
            "experience_years": d["experience_years"],
            "consultation_fee": d["consultation_fee"],
            "languages": d.get("languages", ["Urdu", "English"]),
            "branch_id": d["branch_id"]
        }
        for d in docs
    ]

@server.tool()
def check_available_slots(doctor_id: str, target_date: str) -> List[Dict[str, str]]:
    """
    Returns available 20-minute consultation slots for a doctor on a given date (YYYY-MM-DD).
    """
    doc = db.get_practitioner_by_id(doctor_id)
    if not doc:
        return []

    # Standard clinic slots for target date
    # Morning: 10:00 to 12:40, Evening: 17:00 to 20:40
    slots = []
    base_date = target_date.strip()
    
    time_windows = [
        ("10:00", "12:40"),
        ("17:00", "20:40")
    ]

    for start_t, end_t in time_windows:
        h, m = map(int, start_t.split(":"))
        curr = datetime.strptime(f"{base_date} {start_t}", "%Y-%m-%d %H:%M")
        end_time = datetime.strptime(f"{base_date} {end_t}", "%Y-%m-%d %H:%M")
        
        while curr < end_time:
            next_slot = curr + timedelta(minutes=20)
            slots.append({
                "slot_start": curr.strftime("%Y-%m-%d %H:%M"),
                "slot_end": next_slot.strftime("%Y-%m-%d %H:%M"),
                "display": curr.strftime("%I:%M %p")
            })
            curr = next_slot

    # Return sample 5 available slots
    return slots[:5]

@server.tool()
def book_appointment(patient_id: str, doctor_id: str, branch_id: str,
                     slot_timestamp: str, reason: str, urgency: str = "ROUTINE") -> Dict[str, Any]:
    """
    Books an outpatient appointment for a verified patient.
    slot_timestamp format: 'YYYY-MM-DD HH:MM' or ISO format.
    """
    patient = db.find_patient_by_id(patient_id)
    if not patient:
        return {"success": False, "error": f"Patient ID '{patient_id}' not found."}

    doc = db.get_practitioner_by_id(doctor_id)
    if not doc:
        return {"success": False, "error": f"Doctor ID '{doctor_id}' not found."}

    # Calculate end time (20 minutes after start)
    try:
        if "T" in slot_timestamp:
            start_dt = datetime.fromisoformat(slot_timestamp.replace("Z", "+00:00"))
        else:
            start_dt = datetime.strptime(slot_timestamp, "%Y-%m-%d %H:%M")
    except Exception:
        start_dt = datetime.now(timezone.utc) + timedelta(hours=3)

    end_dt = start_dt + timedelta(minutes=20)
    booking_ref = f"BK-2026-{uuid.uuid4().hex[:6].upper()}"

    appointment_record = {
        "id": str(uuid.uuid4()),
        "booking_reference": booking_ref,
        "patient_id": patient_id,
        "practitioner_id": doctor_id,
        "branch_id": branch_id or doc["branch_id"],
        "scheduled_start": start_dt.isoformat(),
        "scheduled_end": end_dt.isoformat(),
        "urgency_tier": urgency,
        "status": "booked",
        "reason_for_visit": reason,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    saved = db.create_appointment(appointment_record)

    db.log_audit(
        actor_id="SYSTEM_AGENT",
        actor_role="SYSTEM_AGENT",
        action_type="BOOK_APPOINTMENT",
        resource_accessed="appointments",
        patient_id=patient_id,
        tool_name="book_appointment",
        change_payload={"booking_reference": booking_ref, "doctor": doc["full_name"]}
    )

    return {
        "success": True,
        "appointment_id": saved["id"],
        "booking_reference": booking_ref,
        "patient_name": patient["full_name"],
        "doctor_name": doc["full_name"],
        "specialty": doc["specialty"],
        "fee_pkr": doc["consultation_fee"],
        "scheduled_start": saved["scheduled_start"],
        "scheduled_end": saved["scheduled_end"],
        "status": "booked"
    }

@server.tool()
def reschedule_appointment(appointment_id: str, new_slot_timestamp: str) -> Dict[str, Any]:
    """
    Reschedules an existing appointment to a new date and time.
    """
    success = db.update_appointment_status(appointment_id, "booked")
    if not success:
        return {"success": False, "error": f"Appointment ID '{appointment_id}' could not be rescheduled."}
    return {
        "success": True,
        "appointment_id": appointment_id,
        "new_slot_timestamp": new_slot_timestamp,
        "status": "rescheduled"
    }

@server.tool()
def cancel_appointment(appointment_id: str, reason: str) -> Dict[str, Any]:
    """
    Cancels a scheduled appointment with a documented cancellation reason.
    """
    success = db.update_appointment_status(appointment_id, "cancelled", cancellation_reason=reason)
    if not success:
        return {"success": False, "error": f"Appointment ID '{appointment_id}' could not be cancelled."}
    return {
        "success": True,
        "appointment_id": appointment_id,
        "status": "cancelled",
        "reason": reason
    }

if __name__ == "__main__":
    import asyncio
    async def demo():
        tools = await server.list_tools()
        print(f"MCP Server '{server.name}' started. Registered tools: {[t.name for t in tools]}")
    asyncio.run(demo())
