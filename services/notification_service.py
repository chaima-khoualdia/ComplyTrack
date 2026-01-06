"""
Notification Service for Compliance Reminder Emails
Sends automated email notifications to startup founders about compliance deadlines.
Uses Gmail SMTP with TLS encryption.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date
import os
from dotenv import load_dotenv
from typing import Optional
import logging

# Logger setup; do not override root if already configured
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = True
if not logging.getLogger().handlers:
  logging.basicConfig(level=logging.DEBUG)

# Load environment variables from .env
load_dotenv()

# Gmail SMTP Configuration
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_FROM = os.getenv("EMAIL_FROM", EMAIL_USER)


def send_email(
    to_email: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None
) -> bool:
    """
    Send an email via Gmail SMTP.
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        body: Plain text email body
        html_body: Optional HTML version of email body
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    if not EMAIL_USER or not EMAIL_PASS:
        logger.error("Email credentials not configured. Check .env file.")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_FROM
        msg['To'] = to_email
        msg['Subject'] = subject
        msg['Date'] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
        
        # Attach plain text body
        text_part = MIMEText(body, 'plain', 'utf-8')
        msg.attach(text_part)
        
        # Attach HTML body if provided
        if html_body:
            html_part = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(html_part)
        
        # Connect to Gmail SMTP server
        logger.info(f"Connecting to {EMAIL_HOST}:{EMAIL_PORT}...")
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.ehlo()  # Identify ourselves to the SMTP server
            server.starttls()  # Upgrade connection to TLS
            server.ehlo()  # Re-identify after TLS
            
            # Login with credentials
            logger.info(f"Logging in as {EMAIL_USER}...")
            server.login(EMAIL_USER, EMAIL_PASS)
            
            # Send email
            logger.info(f"Sending email to {to_email}...")
            server.send_message(msg)
            
        logger.info(f"✓ Email sent successfully to {to_email}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication failed: {e}")
        logger.error("Check your EMAIL_USER and EMAIL_PASS in .env file")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error occurred: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending email: {e}")
        return False


def send_upcoming_reminder_email(
    to_email: str,
    startup_name: str,
    procedure_name: str,
    due_date: date,
    days_remaining: int
) -> bool:
    """
    Send an upcoming compliance deadline reminder email.
    
    Args:
        to_email: Founder's email address
        startup_name: Name of the startup
        procedure_name: Name of the compliance procedure
        due_date: Deadline date for the procedure
        days_remaining: Number of days until deadline
    
    Returns:
        bool: True if email sent successfully
    """
    subject = f"⚠️ Upcoming Compliance Deadline: {procedure_name}"
    
    # Plain text body
    body = f"""Dear {startup_name} Team,

This is a reminder that your compliance procedure is due soon:

Procedure: {procedure_name}
Due Date: {due_date.strftime('%B %d, %Y')}
Days Remaining: {days_remaining} day{'s' if days_remaining != 1 else ''}

Please ensure all required documents and steps are completed before the deadline to maintain compliance.

If you have already completed this procedure, please update the status in your compliance dashboard.

Best regards,
Legal Compliance OS
"""
    
    # HTML body
    html_body = f"""
    <html>
      <head>
        <style>
          body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
          .header {{ background-color: #FFA500; color: white; padding: 20px; text-align: center; }}
          .content {{ padding: 20px; }}
          .procedure-box {{ background-color: #FFF3CD; border-left: 4px solid #FFA500; padding: 15px; margin: 20px 0; }}
          .footer {{ background-color: #f4f4f4; padding: 10px; text-align: center; font-size: 12px; color: #666; }}
          .button {{ background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 10px; }}
        </style>
      </head>
      <body>
        <div class="header">
          <h2>⚠️ Upcoming Compliance Deadline</h2>
        </div>
        <div class="content">
          <p>Dear {startup_name} Team,</p>
          <p>This is a reminder that your compliance procedure is due soon:</p>
          
          <div class="procedure-box">
            <strong>Procedure:</strong> {procedure_name}<br>
            <strong>Due Date:</strong> {due_date.strftime('%B %d, %Y')}<br>
            <strong>Days Remaining:</strong> <span style="color: #FFA500; font-weight: bold;">{days_remaining} day{'s' if days_remaining != 1 else ''}</span>
          </div>
          
          <p>Please ensure all required documents and steps are completed before the deadline to maintain compliance.</p>
          <p>If you have already completed this procedure, please update the status in your compliance dashboard.</p>
        </div>
        <div class="footer">
          <p>Legal Compliance OS - Automated Compliance Tracking</p>
        </div>
      </body>
    </html>
    """
    
    return send_email(to_email, subject, body, html_body)


def send_overdue_reminder_email(
    to_email: str,
    startup_name: str,
    procedure_name: str,
    due_date: date,
    days_overdue: int
) -> bool:
    """
    Send an overdue compliance deadline notification email.
    
    Args:
        to_email: Founder's email address
        startup_name: Name of the startup
        procedure_name: Name of the compliance procedure
        due_date: Original deadline date (now passed)
        days_overdue: Number of days past the deadline
    
    Returns:
        bool: True if email sent successfully
    """
    subject = f"🔴 OVERDUE: {procedure_name} - Immediate Action Required"
    
    # Plain text body
    body = f"""Dear {startup_name} Team,

URGENT: Your compliance procedure is now overdue:

Procedure: {procedure_name}
Original Due Date: {due_date.strftime('%B %d, %Y')}
Days Overdue: {days_overdue} day{'s' if days_overdue != 1 else ''}

This compliance requirement is now past its deadline. Please complete this procedure immediately to avoid potential penalties or legal issues.

If you have already completed this procedure, please update the status in your compliance dashboard as soon as possible.

For assistance, please contact your compliance advisor immediately.

Best regards,
Legal Compliance OS
"""
    
    # HTML body
    html_body = f"""
    <html>
      <head>
        <style>
          body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
          .header {{ background-color: #DC3545; color: white; padding: 20px; text-align: center; }}
          .content {{ padding: 20px; }}
          .procedure-box {{ background-color: #F8D7DA; border-left: 4px solid #DC3545; padding: 15px; margin: 20px 0; }}
          .footer {{ background-color: #f4f4f4; padding: 10px; text-align: center; font-size: 12px; color: #666; }}
          .urgent {{ color: #DC3545; font-weight: bold; font-size: 18px; }}
        </style>
      </head>
      <body>
        <div class="header">
          <h2>🔴 OVERDUE: Immediate Action Required</h2>
        </div>
        <div class="content">
          <p>Dear {startup_name} Team,</p>
          <p class="urgent">URGENT: Your compliance procedure is now overdue</p>
          
          <div class="procedure-box">
            <strong>Procedure:</strong> {procedure_name}<br>
            <strong>Original Due Date:</strong> {due_date.strftime('%B %d, %Y')}<br>
            <strong>Days Overdue:</strong> <span style="color: #DC3545; font-weight: bold;">{days_overdue} day{'s' if days_overdue != 1 else ''}</span>
          </div>
          
          <p>This compliance requirement is now past its deadline. Please complete this procedure <strong>immediately</strong> to avoid potential penalties or legal issues.</p>
          <p>If you have already completed this procedure, please update the status in your compliance dashboard as soon as possible.</p>
          <p>For assistance, please contact your compliance advisor immediately.</p>
        </div>
        <div class="footer">
          <p>Legal Compliance OS - Automated Compliance Tracking</p>
        </div>
      </body>
    </html>
    """
    
    return send_email(to_email, subject, body, html_body)


def test_email_connection() -> bool:
    """
    Test the Gmail SMTP connection and credentials.
    
    Returns:
        bool: True if connection successful
    """
    if not EMAIL_USER or not EMAIL_PASS:
        logger.error("Email credentials not configured")
        return False
    
    try:
        logger.info("Testing Gmail SMTP connection...")
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(EMAIL_USER, EMAIL_PASS)
        logger.info("✓ Gmail SMTP connection successful")
        return True
    except Exception as e:
        logger.error(f"✗ Gmail SMTP connection failed: {e}")
        return False
