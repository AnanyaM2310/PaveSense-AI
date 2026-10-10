
import os
import re
import smtplib
from email.message import EmailMessage


def send_registration_email(recipient, applicant_name, complaint_id):
    """Send a PaveSense AI complaint submission confirmation."""

    if not recipient or not recipient.strip():
        return False, "No reporting contact email was provided."

    recipient = recipient.strip()

    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", recipient):
        return False, "The reporting contact email address is invalid."

    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("SMTP_FROM_EMAIL") or smtp_username

    if not smtp_username or not smtp_password or not sender:
        return False, "Email settings are not configured."

    message = EmailMessage()
    message["Subject"] = (
        f"PaveSense AI: Complaint #{complaint_id} Submitted"
    )
    message["From"] = sender
    message["To"] = recipient

    message.set_content(
        f"""Hello {applicant_name or "there"},

Your road damage complaint has been successfully submitted
on PaveSense AI.

Complaint ID: {complaint_id}
Status: Submitted

Please keep your complaint ID for future reference.

This email confirms submission on PaveSense AI. It does not
necessarily mean that the complaint has been registered with
the relevant government authority.

Thank you for helping improve road safety.

Regards,
PaveSense AI Team
"""
    )

    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(
                smtp_host, smtp_port, timeout=15
            ) as server:
                server.login(smtp_username, smtp_password)
                server.send_message(message)
        else:
            with smtplib.SMTP(
                smtp_host, smtp_port, timeout=15
            ) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(smtp_username, smtp_password)
                server.send_message(message)

        return True, "Confirmation email sent successfully."

    except (smtplib.SMTPException, OSError, ValueError) as error:
        print(f"PaveSense AI email error: {error}")
        return False, "The complaint was submitted, but the email could not be sent."
