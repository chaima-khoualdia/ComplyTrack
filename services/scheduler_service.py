"""
Scheduler Service for Automated Compliance Reminder Emails
Uses APScheduler to check reminders daily and send email notifications.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import date, timedelta
from sqlmodel import Session, select
from db import get_session
from models import Reminder, Startup, StartupProcedure
from services.notification_service import (
    send_upcoming_reminder_email,
    send_overdue_reminder_email,
    test_email_connection
)
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None


def check_and_send_reminder_emails():
    """
    Check all pending reminders and send email notifications.
    - Upcoming: reminder_date - today <= 3 days
    - Overdue: reminder_date < today
    Updates reminder status after sending.
    """
    logger.info("=" * 60)
    logger.info("Starting daily reminder email check...")
    logger.info("=" * 60)
    
    today = date.today()
    upcoming_threshold = today + timedelta(days=3)
    
    sent_count = 0
    overdue_count = 0
    error_count = 0
    
    try:
        # Get database session
        session = next(get_session())
        
        # Query all pending reminders
        statement = select(Reminder).where(Reminder.status == "pending")
        pending_reminders = session.exec(statement).all()
        
        logger.info(f"Found {len(pending_reminders)} pending reminders to check")
        
        for reminder in pending_reminders:
            try:
                # Get associated startup
                startup = session.get(Startup, reminder.startup_id)
                if not startup:
                    logger.warning(f"Startup {reminder.startup_id} not found for reminder {reminder.id}")
                    continue
                
                # Get founder's email through the relationship
                # Startup has founder_id -> User has email
                from models.user import User
                founder = session.get(User, startup.founder_id)
                if not founder or not founder.email:
                    logger.warning(f"No founder or email found for startup {startup.name} (ID: {startup.id})")
                    continue
                
                to_email = founder.email
                
                # Extract procedure name from reminder message
                # Message format: "{procedure_name} due by {date}"
                procedure_name = reminder.message.split(" due by ")[0] if " due by " in reminder.message else "Compliance Procedure"
                
                # Determine if overdue or upcoming
                if reminder.reminder_date < today:
                    # Overdue
                    days_overdue = (today - reminder.reminder_date).days
                    logger.info(f"Sending OVERDUE email for {procedure_name} to {startup.name} ({days_overdue} days overdue)")
                    
                    success = send_overdue_reminder_email(
                        to_email=to_email,
                        startup_name=startup.name,
                        procedure_name=procedure_name,
                        due_date=reminder.reminder_date,
                        days_overdue=days_overdue
                    )
                    
                    if success:
                        # Update status to overdue
                        reminder.status = "overdue"
                        session.add(reminder)
                        overdue_count += 1
                    else:
                        error_count += 1
                        logger.error(f"Failed to send overdue email for reminder {reminder.id}")
                
                elif reminder.reminder_date <= upcoming_threshold:
                    # Upcoming (within 3 days)
                    days_remaining = (reminder.reminder_date - today).days
                    logger.info(f"Sending UPCOMING email for {procedure_name} to {startup.name} ({days_remaining} days remaining)")
                    
                    success = send_upcoming_reminder_email(
                        to_email=to_email,
                        startup_name=startup.name,
                        procedure_name=procedure_name,
                        due_date=reminder.reminder_date,
                        days_remaining=days_remaining
                    )
                    
                    if success:
                        # Update status to sent
                        reminder.status = "sent"
                        session.add(reminder)
                        sent_count += 1
                    else:
                        error_count += 1
                        logger.error(f"Failed to send upcoming email for reminder {reminder.id}")
                
                # If reminder is more than 3 days away, skip
                else:
                    logger.debug(f"Reminder {reminder.id} is {(reminder.reminder_date - today).days} days away - skipping")
            
            except Exception as e:
                logger.error(f"Error processing reminder {reminder.id}: {e}")
                error_count += 1
                continue
        
        # Commit all status updates
        session.commit()
        session.close()
        
        logger.info("=" * 60)
        logger.info(f"Reminder email check completed:")
        logger.info(f"  - Upcoming emails sent: {sent_count}")
        logger.info(f"  - Overdue emails sent: {overdue_count}")
        logger.info(f"  - Errors: {error_count}")
        logger.info("=" * 60)
    
    except Exception as e:
        logger.error(f"Fatal error in reminder email check: {e}")


def start_scheduler():
    """
    Start the APScheduler background scheduler.
    Runs check_and_send_reminder_emails() daily at 9:00 AM.
    """
    global scheduler
    
    if scheduler is not None:
        logger.warning("Scheduler already running")
        return
    
    # Test email connection first
    logger.info("Testing Gmail SMTP connection before starting scheduler...")
    if not test_email_connection():
        logger.error("Gmail SMTP connection test failed. Scheduler will start but emails may not send.")
        logger.error("Please check your EMAIL_USER and EMAIL_PASS in .env file")
    
    scheduler = BackgroundScheduler()
    
    # Schedule daily job at 9:00 AM
    scheduler.add_job(
        func=check_and_send_reminder_emails,
        trigger=CronTrigger(hour=9, minute=0),  # Daily at 9:00 AM
        id='daily_reminder_emails',
        name='Check and send compliance reminder emails',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("✓ Scheduler started - Daily reminder emails will be sent at 9:00 AM")
    logger.info("  Job ID: daily_reminder_emails")
    
    # Optional: Run immediately on startup for testing
    # Uncomment the next line to send emails immediately when app starts
    # check_and_send_reminder_emails()


def stop_scheduler():
    """
    Stop the APScheduler background scheduler.
    """
    global scheduler
    
    if scheduler is None:
        logger.warning("Scheduler not running")
        return
    
    scheduler.shutdown()
    scheduler = None
    logger.info("✓ Scheduler stopped")


def get_scheduler_status():
    """
    Get the current status of the scheduler and its jobs.
    
    Returns:
        dict: Scheduler status information
    """
    global scheduler
    
    if scheduler is None:
        return {
            "running": False,
            "jobs": []
        }
    
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        })
    
    return {
        "running": True,
        "jobs": jobs
    }


def run_reminder_check_now():
    """
    Manually trigger the reminder check immediately.
    Useful for testing or manual triggers.
    """
    logger.info("Manual reminder check triggered")
    check_and_send_reminder_emails()
