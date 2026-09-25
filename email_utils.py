"""Email delivery of the generated PDF report via SMTP."""

import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import streamlit as st


def send_email_with_pdf(
    recipient: str, subject: str, body: str, pdf_bytes: bytes, filename: str
) -> None:
  """Send the PDF report as an email attachment via SMTP.

  Requires SMTP credentials in .streamlit/secrets.toml, e.g.:

      SMTP_HOST = "smtp.gmail.com"
      SMTP_PORT = 587
      SMTP_USER = "your-address@gmail.com"
      SMTP_PASSWORD = "your-app-password"
      SENDER_EMAIL = "your-address@gmail.com"   # optional, defaults to SMTP_USER

  Never hardcode credentials directly in source files.
  """
  smtp_host = st.secrets.get("SMTP_HOST")
  smtp_port = int(st.secrets.get("SMTP_PORT", 587))
  smtp_user = st.secrets.get("SMTP_USER")
  smtp_password = st.secrets.get("SMTP_PASSWORD")
  sender_email = st.secrets.get("SENDER_EMAIL", smtp_user)

  if not all([smtp_host, smtp_user, smtp_password]):
    raise RuntimeError(
        "Email is not configured. Add SMTP_HOST, SMTP_USER, SMTP_PASSWORD"
        " (and optionally SMTP_PORT, SENDER_EMAIL) to"
        " .streamlit/secrets.toml."
    )

  msg = MIMEMultipart()
  msg["From"] = sender_email
  msg["To"] = recipient
  msg["Subject"] = subject
  msg.attach(MIMEText(body, "plain"))

  attachment = MIMEApplication(pdf_bytes, Name=filename)
  attachment["Content-Disposition"] = f'attachment; filename="{filename}"'
  msg.attach(attachment)

  with smtplib.SMTP(smtp_host, smtp_port) as server:
    server.starttls()
    server.login(smtp_user, smtp_password)
    server.sendmail(sender_email, [recipient], msg.as_string())
