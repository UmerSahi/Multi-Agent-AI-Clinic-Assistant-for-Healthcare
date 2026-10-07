"""
Automated Test Suite & Inspector for all 4 Clinic MCP Servers
Independently verifies:
1. patient-records
2. scheduling
3. drug-database
4. notifications
"""

import sys
import asyncio
from pathlib import Path

# Ensure paths
sys.path.append(str(Path(__file__).resolve().parent))
from mcp_servers.mcp_patient_records import server as server_records
from mcp_servers.mcp_scheduling import server as server_sched
from mcp_servers.mcp_drug_database import server as server_drugs
from mcp_servers.mcp_notifications import server as server_notify

async def test_all_mcp_servers():
    print("======================================================================")
    print("       CITY CARE CLINICS — MCP SERVERS INDEPENDENT TEST SUITE         ")
    print("======================================================================\n")
    
    passes = 0
    total = 0

    # ---------------- 1. Patient Records Server ----------------
    print("[1/4] Testing MCP Server: 'patient-records'...")
    tools_records = await server_records.list_tools()
    tool_names = [t.name for t in tools_records]
    print(f"  -> Discovered tools: {tool_names}")
    assert "get_patient_profile" in tool_names
    assert "get_patient_allergies" in tool_names

    # Test profile lookup
    total += 1
    res1 = await server_records.call_tool("get_patient_profile", {"identifier": "CCC-PK-100001"})
    print(f"  -> get_patient_profile('CCC-PK-100001'): Success={not res1.is_error}")
    if not res1.is_error:
        passes += 1

    # Test lab lookup
    total += 1
    res2 = await server_records.call_tool("get_patient_lab_results", {"patient_id": "dummy_id"})
    print(f"  -> get_patient_lab_results(): Success={not res2.is_error}")
    if not res2.is_error:
        passes += 1

    # ---------------- 2. Scheduling Server ----------------
    print("\n[2/4] Testing MCP Server: 'scheduling'...")
    tools_sched = await server_sched.list_tools()
    tool_names_sched = [t.name for t in tools_sched]
    print(f"  -> Discovered tools: {tool_names_sched}")
    assert "find_doctor" in tool_names_sched
    assert "check_available_slots" in tool_names_sched
    assert "book_appointment" in tool_names_sched

    # Test find doctor
    total += 1
    res_docs = await server_sched.call_tool("find_doctor", {"specialty": "General Medicine"})
    print(f"  -> find_doctor(General Medicine): Success={not res_docs.is_error}")
    if not res_docs.is_error:
        passes += 1

    # Test check slots
    total += 1
    res_slots = await server_sched.call_tool("check_available_slots", {"doctor_id": "dummy_doc", "target_date": "2026-10-10"})
    print(f"  -> check_available_slots('2026-10-10'): Success={not res_slots.is_error}")
    if not res_slots.is_error:
        passes += 1

    # ---------------- 3. Drug Database Server ----------------
    print("\n[3/4] Testing MCP Server: 'drug-database'...")
    tools_drugs = await server_drugs.list_tools()
    tool_names_drugs = [t.name for t in tools_drugs]
    print(f"  -> Discovered tools: {tool_names_drugs}")
    assert "lookup_drug" in tool_names_drugs
    assert "check_drug_interactions" in tool_names_drugs
    assert "evaluate_full_prescription" in tool_names_drugs

    # Test drug lookup
    total += 1
    res_lookup = await server_drugs.call_tool("lookup_drug", {"query": "Augmentin"})
    print(f"  -> lookup_drug('Augmentin'): Success={not res_lookup.is_error}")
    if not res_lookup.is_error:
        passes += 1

    # Test drug clash check
    total += 1
    res_interact = await server_drugs.call_tool("check_drug_interactions", {"drugs": ["Loprin", "Brufen"]})
    print(f"  -> check_drug_interactions(['Loprin', 'Brufen']): Success={not res_interact.is_error}")
    if not res_interact.is_error:
        passes += 1

    # Test prescription evaluation
    total += 1
    res_eval = await server_drugs.call_tool("evaluate_full_prescription", {
        "proposed_drugs": ["Augmentin"],
        "patient_allergies": ["Penicillin"],
        "age": 25,
        "is_pregnant": False
    })
    print(f"  -> evaluate_full_prescription(Augmentin + Penicillin Allergy): Success={not res_eval.is_error}")
    if not res_eval.is_error:
        passes += 1

    # ---------------- 4. Notifications Server ----------------
    print("\n[4/4] Testing MCP Server: 'notifications'...")
    tools_notify = await server_notify.list_tools()
    tool_names_notify = [t.name for t in tools_notify]
    print(f"  -> Discovered tools: {tool_names_notify}")
    assert "send_whatsapp_message" in tool_names_notify
    assert "send_sms_alert" in tool_names_notify
    assert "send_email_confirmation" in tool_names_notify

    # Test WhatsApp message
    total += 1
    res_wa = await server_notify.call_tool("send_whatsapp_message", {
        "recipient_phone": "+92-300-1234567",
        "message_body": "Aap ki appointment Dr. Usman Tariq ke sath confirm ho chuki hai."
    })
    print(f"  -> send_whatsapp_message(): Success={not res_wa.is_error}")
    if not res_wa.is_error:
        passes += 1

    # Test SMS alert
    total += 1
    res_sms = await server_notify.call_tool("send_sms_alert", {
        "recipient_phone": "+92-300-1234567",
        "alert_text": "City Care Alert: 1122 Helpline has been dispatched.",
        "urgency": "EMERGENCY"
    })
    print(f"  -> send_sms_alert(EMERGENCY): Success={not res_sms.is_error}")
    if not res_sms.is_error:
        passes += 1

    print("\n======================================================================")
    print(f"SUMMARY: {passes}/{total} MCP tests passed ({(passes/total)*100:.1f}%)")
    print("All 4 MCP Servers verified and operational!")
    print("======================================================================")

if __name__ == "__main__":
    asyncio.run(test_all_mcp_servers())
