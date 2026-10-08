"""
Email Notification & Follow-up Channel Service for City Care Clinics
Generates HTML appointment confirmations, Google/iCal event attachments,
and automated follow-up reminder messages.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone


class EmailNotifier:
    """Simulates/dispatches transactional healthcare emails with calendar events."""

    def __init__(self):
        self._sent_emails = []

    def send_appointment_confirmation(
        self,
        patient_name: str,
        patient_email: str,
        doctor_name: str,
        specialty: str,
        branch_name: str,
        start_time_iso: str,
        booking_ref: str,
        consultation_fee: int,
        calendar_url: str
    ) -> Dict[str, Any]:
        """Creates and records rich appointment confirmation email."""
        dt = datetime.fromisoformat(start_time_iso.replace("Z", "+00:00"))
        time_display = dt.strftime("%A, %d %B %Y at %I:%M %p")

        subject = f"Appointment Confirmed: Dr. {doctor_name} — City Care Clinics (#{booking_ref})"
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
            <div style="background-color: #0f766e; color: white; padding: 15px; border-radius: 6px; text-align: center;">
                <h2>City Care Clinics — Confirmation</h2>
            </div>
            <p>Dear {patient_name},</p>
            <p>Your outpatient appointment has been successfully scheduled:</p>
            <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                <tr><td style="padding: 8px; border-bottom: 1px solid #e2e8f0;"><strong>Doctor:</strong></td><td style="padding: 8px; border-bottom: 1px solid #e2e8f0;">Dr. {doctor_name} ({specialty})</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #e2e8f0;"><strong>Date & Time:</strong></td><td style="padding: 8px; border-bottom: 1px solid #e2e8f0;">{time_display}</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #e2e8f0;"><strong>Branch:</strong></td><td style="padding: 8px; border-bottom: 1px solid #e2e8f0;">{branch_name}</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #e2e8f0;"><strong>Consultation Fee:</strong></td><td style="padding: 8px; border-bottom: 1px solid #e2e8f0;">PKR {consultation_fee:,}</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #e2e8f0;"><strong>Booking Ref:</strong></td><td style="padding: 8px; border-bottom: 1px solid #e2e8f0;">#{booking_ref}</td></tr>
            </table>
            <div style="text-align: center; margin: 25px 0;">
                <a href="{calendar_url}" style="background-color: #0284c7; color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px; font-weight: bold;">Add to Google Calendar</a>
            </div>
            <p style="font-size: 13px; color: #64748b;">Please arrive 10 minutes prior to your scheduled consultation. If you experience emergency chest pain or breathing distress, immediately call 1122.</p>
        </div>
        """

        record = {
            "recipient": patient_email or f"{patient_name.lower().replace(' ', '.')}@example.com",
            "subject": subject,
            "html_body": html_body,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "status": "SENT"
        }
        self._sent_emails.append(record)
        return record

    def send_followup_reminder(
        self,
        patient_name: str,
        patient_email: str,
        doctor_name: str,
        scheduled_date_display: str,
        medication_count: int
    ) -> Dict[str, Any]:
        """Dispatches automated follow-up reminder."""
        subject = f"Follow-Up Reminder & Medicine Schedule — City Care Clinics"
        record = {
            "recipient": patient_email,
            "subject": subject,
            "patient_name": patient_name,
            "doctor_name": doctor_name,
            "date": scheduled_date_display,
            "med_count": medication_count,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "status": "SENT"
        }
        self._sent_emails.append(record)
        return record


# Singleton instance
email_notifier = EmailNotifier()
