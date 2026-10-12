"""
Email Notification & Follow-up Channel Service for City Care Clinics
Dispatches HTML appointment confirmations, Google Calendar links,
and automated follow-up reminders via real SMTP (Gmail, Outlook, SendGrid, etc.)
with automatic fallback for local testing.
"""

import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class EmailNotifier:
    """Dispatches transactional healthcare emails via SMTP with rich HTML templates."""

    def __init__(self):
        self._sent_emails: List[Dict[str, Any]] = []
        self._load_config()

    def _load_config(self):
        """Loads or reloads SMTP configuration from environment variables."""
        self.smtp_host = os.getenv("SMTP_HOST", "").strip()
        try:
            self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        except ValueError:
            self.smtp_port = 587
        self.smtp_user = os.getenv("SMTP_USER", "").strip()
        self.smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
        self.smtp_from_email = os.getenv("SMTP_FROM_EMAIL", self.smtp_user).strip()
        self.smtp_from_name = os.getenv("SMTP_FROM_NAME", "City Care Clinics").strip()
        self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() in ("true", "1", "yes")

    @property
    def is_smtp_configured(self) -> bool:
        self._load_config()
        return bool(self.smtp_host and self.smtp_user and self.smtp_password and not self.smtp_user.startswith("your-"))

    def _send_smtp_email(self, to_email: str, subject: str, html_body: str) -> bool:
        """Sends an HTML email over SMTP connection using TLS or SSL."""
        if not to_email or "@example.com" in to_email or not self.is_smtp_configured:
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.smtp_from_name} <{self.smtp_from_email}>"
            msg["To"] = to_email

            part = MIMEText(html_body, "html")
            msg.attach(part)

            if self.smtp_port == 465:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context, timeout=15) as server:
                    server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(self.smtp_from_email, [to_email], msg.as_string())
            else:
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=15) as server:
                    if self.smtp_use_tls:
                        context = ssl.create_default_context()
                        server.starttls(context=context)
                    server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(self.smtp_from_email, [to_email], msg.as_string())

            print(f"[EmailNotifier] Successfully dispatched live SMTP email to: {to_email}")
            return True
        except Exception as e:
            print(f"[EmailNotifier SMTP Warning] Could not dispatch to {to_email}: {e}")
            return False

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
        """Creates and dispatches rich appointment confirmation email."""
        dt = datetime.fromisoformat(start_time_iso.replace("Z", "+00:00"))
        time_display = dt.strftime("%A, %d %B %Y at %I:%M %p")

        clean_ref = str(booking_ref).replace("#", "").strip()
        subject = f"Appointment Confirmed: Dr. {doctor_name} — City Care Clinics (#{clean_ref})"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Appointment Confirmation</title>
        </head>
        <body style="font-family: Arial, sans-serif; background-color: #f8fafc; padding: 20px; margin: 0;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                <div style="background: linear-gradient(135deg, #0f766e 0%, #0d9488 100%); color: white; padding: 25px 20px; text-align: center;">
                    <h1 style="margin: 0; font-size: 24px; font-weight: bold; letter-spacing: -0.5px;">City Care Clinics</h1>
                    <p style="margin: 6px 0 0 0; font-size: 14px; opacity: 0.9;">Outpatient Medical Appointment Confirmation</p>
                </div>
                <div style="padding: 24px;">
                    <p style="font-size: 16px; color: #1e293b; margin-top: 0;">Dear <strong>{patient_name}</strong>,</p>
                    <p style="font-size: 15px; color: #475569; line-height: 1.6;">
                        Your consultation has been successfully confirmed. Below are your appointment details:
                    </p>
                    
                    <div style="background-color: #f0fdfa; border: 1px solid #ccfbf1; border-radius: 8px; padding: 16px; margin: 20px 0;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; color: #64748b; font-size: 14px; width: 38%;"><strong>Doctor:</strong></td>
                                <td style="padding: 8px 0; color: #0f172a; font-size: 15px; font-weight: bold;">Dr. {doctor_name} ({specialty})</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #64748b; font-size: 14px;"><strong>Date & Time:</strong></td>
                                <td style="padding: 8px 0; color: #0f172a; font-size: 15px;">{time_display}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #64748b; font-size: 14px;"><strong>Branch Location:</strong></td>
                                <td style="padding: 8px 0; color: #0f172a; font-size: 15px;">{branch_name}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #64748b; font-size: 14px;"><strong>Consultation Fee:</strong></td>
                                <td style="padding: 8px 0; color: #0f172a; font-size: 15px;">PKR {consultation_fee:,}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #64748b; font-size: 14px;"><strong>Appointment ID:</strong></td>
                                <td style="padding: 8px 0; color: #0f766e; font-size: 15px; font-weight: bold;">#{clean_ref}</td>
                            </tr>
                        </table>
                    </div>

                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{calendar_url}" target="_blank" style="display: inline-block; background-color: #0284c7; color: white; padding: 12px 26px; text-decoration: none; border-radius: 8px; font-size: 15px; font-weight: bold; box-shadow: 0 2px 4px rgba(2, 132, 199, 0.3);">
                            📅 Add to Google Calendar
                        </a>
                    </div>

                    <div style="background-color: #fef2f2; border-left: 4px solid #ef4444; padding: 12px 16px; border-radius: 4px; margin: 20px 0;">
                        <p style="margin: 0; font-size: 13px; color: #991b1b; line-height: 1.5;">
                            <strong>Emergency Notice:</strong> If you experience severe chest pain, sudden shortness of breath, or stroke symptoms, please call <strong>Rescue 1122</strong> immediately or proceed to the nearest emergency ward.
                        </p>
                    </div>

                    <p style="font-size: 13px; color: #94a3b8; text-align: center; margin-top: 30px; border-top: 1px solid #e2e8f0; padding-top: 16px;">
                        City Care Clinics Healthcare System — Lahore & Islamabad<br>
                        Please arrive 10 minutes prior to your scheduled slot.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        recipient = patient_email or f"{patient_name.lower().replace(' ', '.')}@example.com"
        smtp_success = self._send_smtp_email(recipient, subject, html_body)

        record = {
            "recipient": recipient,
            "subject": subject,
            "html_body": html_body,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "status": "DELIVERED_VIA_SMTP" if smtp_success else "SENT_LOCAL_SIMULATION",
            "smtp_sent": smtp_success
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
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h3>City Care Clinics Follow-Up Care</h3>
            <p>Dear {patient_name},</p>
            <p>This is a reminder regarding your post-consultation care plan with Dr. {doctor_name}.</p>
            <p>Please ensure you are taking your {medication_count} prescribed medicines on time. If your symptoms worsen, please contact the clinic.</p>
        </div>
        """
        smtp_success = self._send_smtp_email(patient_email, subject, html_body)
        record = {
            "recipient": patient_email,
            "subject": subject,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "status": "DELIVERED_VIA_SMTP" if smtp_success else "SENT_LOCAL_SIMULATION",
            "smtp_sent": smtp_success
        }
        self._sent_emails.append(record)
        return record


# Singleton instance
email_notifier = EmailNotifier()
