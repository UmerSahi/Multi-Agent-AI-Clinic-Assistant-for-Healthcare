"""
MCP Server: Notifications & Messaging
Exposes standardized MCP tools for dispatching WhatsApp messages, SMS alerts,
and email confirmations to patients and clinic doctors.
"""

import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

sys.path.append(str(Path(__file__).resolve().parent.parent))
from db_client import db
from mcp.server.mcpserver import MCPServer

server = MCPServer("notifications")

@server.tool()
def send_whatsapp_message(recipient_phone: str, message_body: str, template_type: str = "appointment_confirmation") -> Dict[str, Any]:
    """
    Simulates sending an authenticated WhatsApp Cloud API message in UrduLish to the patient's phone.
    """
    msg_id = f"wamid.{uuid.uuid4().hex[:12]}"
    timestamp = datetime.now(timezone.utc).isoformat()

    # Audit log
    db.log_audit(
        actor_id="SYSTEM_AGENT",
        actor_role="SYSTEM_AGENT",
        action_type="SEND_WHATSAPP",
        resource_accessed="messaging",
        tool_name="send_whatsapp_message",
        change_payload={"recipient": recipient_phone, "template": template_type}
    )

    return {
        "status": "delivered",
        "message_id": msg_id,
        "recipient_phone": recipient_phone,
        "channel": "WhatsApp Cloud API",
        "template": template_type,
        "timestamp": timestamp,
        "preview": message_body[:100] + "..." if len(message_body) > 100 else message_body
    }

@server.tool()
def send_sms_alert(recipient_phone: str, alert_text: str, urgency: str = "ROUTINE") -> Dict[str, Any]:
    """
    Sends an urgent SMS alert (e.g. for emergency notices, slot reminders, or OTP verification).
    """
    sms_id = f"sms_{uuid.uuid4().hex[:8]}"
    is_emergency = urgency.upper() == "EMERGENCY"

    # Audit log with emergency flag
    db.log_audit(
        actor_id="SYSTEM_AGENT",
        actor_role="SYSTEM_AGENT",
        action_type="SEND_SMS_ALERT",
        resource_accessed="telephony",
        tool_name="send_sms_alert",
        change_payload={"recipient": recipient_phone, "urgency": urgency},
        emergency_flag=is_emergency
    )

    return {
        "status": "sent",
        "sms_id": sms_id,
        "recipient_phone": recipient_phone,
        "urgency": urgency,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@server.tool()
def send_email_confirmation(recipient_email: str, subject: str, html_body: str) -> Dict[str, Any]:
    """
    Dispatches a formal clinic appointment confirmation or lab report notification via email.
    """
    email_id = f"email_{uuid.uuid4().hex[:10]}"
    return {
        "status": "queued",
        "email_id": email_id,
        "recipient_email": recipient_email,
        "subject": subject,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

if __name__ == "__main__":
    import asyncio
    async def demo():
        tools = await server.list_tools()
        print(f"MCP Server '{server.name}' started. Registered tools: {[t.name for t in tools]}")
    asyncio.run(demo())
