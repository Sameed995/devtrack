import os
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone


def generate_otp(length: int = 6) -> str:
    """Generate a random OTP of specified length."""
    return ''.join(random.choices(string.digits, k=length))


def send_otp_email(
    recipient_email: str,
    otp_code: str,
    purpose: str = "Email Verification"
) -> bool:
    """
    Send OTP via email using SMTP.

    Environment variables required:
    - SMTP_SERVER
    - SMTP_PORT
    - SMTP_EMAIL
    - SMTP_PASSWORD

    Returns:
        True if email sent successfully, False otherwise.
    """

    try:
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = int(os.getenv("SMTP_PORT", 587))
        sender_email = os.getenv("SMTP_EMAIL")
        sender_password = os.getenv("SMTP_PASSWORD")

        if not all([smtp_server, sender_email, sender_password]):
            print("Warning: Email configuration not set.")
            print(
                "Set SMTP_SERVER, SMTP_EMAIL, "
                "and SMTP_PASSWORD environment variables."
            )
            return False

        # Create email message
        message = MIMEMultipart("alternative")

        message["Subject"] = f"DevTrack - {purpose} Code"
        message["From"] = sender_email
        message["To"] = recipient_email

        # Plain text version
        text = f"""
Hello,

Your DevTrack {purpose.lower()} code is:

{otp_code}

This code will expire in 10 minutes.

If you did not request this code,
please ignore this email.

Best regards,
DevTrack Team
"""

        # HTML version
        html = f"""
<html>
  <body>
    <p>Hello,</p>

    <p>
      Your DevTrack
      <strong>{purpose.lower()}</strong>
      code is:
    </p>

    <h2 style="color: #007bff; letter-spacing: 2px;">
      {otp_code}
    </h2>

    <p>
      This code will expire in 10 minutes.
    </p>

    <p>
      If you did not request this code,
      please ignore this email.
    </p>

    <p>
      Best regards,<br>
      DevTrack Team
    </p>
  </body>
</html>
"""

        # Attach both plain text and HTML
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")

        message.attach(part1)
        message.attach(part2)

        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)

            server.sendmail(
                sender_email,
                recipient_email,
                message.as_string()
            )

        print(f"OTP email sent successfully to {recipient_email}")

        return True

    except Exception as e:
        print(f"Error sending OTP email: {e}")
        return False


def get_otp_expiry_time() -> datetime:
    """Get OTP expiry time (10 minutes from now)."""

    return (
        datetime.now(timezone.utc)
        + timedelta(minutes=10)
    )