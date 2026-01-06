# Gmail Email Notification System - Documentation

## Overview

Automated email notification system for compliance reminders using Gmail SMTP and APScheduler. Sends daily notifications to startup founders about upcoming and overdue compliance deadlines.

## Architecture

### Components

1. **notification_service.py** - Email sending via Gmail SMTP with TLS
2. **scheduler_service.py** - APScheduler daily job for automated checks
3. **app.py** - FastAPI integration with startup/shutdown events
4. **.env** - Gmail credentials and SMTP configuration
5. **API endpoints** - Manual control and monitoring

### Data Flow

```
Daily at 9:00 AM (APScheduler)
    ↓
check_and_send_reminder_emails()
    ↓
Query Reminder table (status="pending")
    ↓
For each reminder:
    - Get Startup → Get Founder → Get Email
    - Check if upcoming (≤3 days) or overdue (<today)
    - Send appropriate email
    - Update reminder status ("sent" or "overdue")
```

## Configuration

### .env File

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=chaima.khoualdiaa@gmail.com
EMAIL_PASS=lcrv hueq lxoo tlfd
EMAIL_FROM=chaima.khoualdiaa@gmail.com
```

**Gmail App Password Setup:**
1. Go to Google Account → Security
2. Enable 2-Step Verification
3. Go to App Passwords
4. Generate new app password for "Mail"
5. Use the 16-character password in EMAIL_PASS

**Important:** Never commit .env to version control. Add to .gitignore.

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

New packages added:
- `apscheduler==3.10.4` - Job scheduling
- `python-dotenv==1.0.1` - Environment variable management

### 2. Configure Gmail

Create `.env` file in project root with your Gmail credentials (see above).

### 3. Start Application

```bash
uvicorn app:app --reload
```

The scheduler starts automatically when the app launches.

## Usage

### Automatic Operation

The system runs automatically:

1. **App Startup:** Scheduler starts and schedules daily job at 9:00 AM
2. **Daily at 9:00 AM:** 
   - Queries all pending reminders
   - Sends upcoming emails (≤3 days until deadline)
   - Sends overdue emails (<deadline date)
   - Updates reminder statuses

### Manual Control via API

#### Get Scheduler Status
```bash
GET /reminders/scheduler/status
```

Response:
```json
{
  "running": true,
  "jobs": [
    {
      "id": "daily_reminder_emails",
      "name": "Check and send compliance reminder emails",
      "next_run": "2026-01-05T09:00:00",
      "trigger": "cron[hour='9', minute='0']"
    }
  ]
}
```

#### Run Check Immediately
```bash
POST /reminders/scheduler/run-now
```

Triggers the reminder check manually without waiting for scheduled time.

#### Start Scheduler
```bash
POST /reminders/scheduler/start
```

#### Stop Scheduler
```bash
POST /reminders/scheduler/stop
```

## Email Templates

### Upcoming Reminder (≤3 days)

**Subject:** ⚠️ Upcoming Compliance Deadline: {procedure_name}

**Content:**
- Startup name
- Procedure name
- Due date
- Days remaining (1-3)
- Call to action: Complete procedure or update status

**Color:** Orange/Yellow theme

### Overdue Reminder (<deadline)

**Subject:** 🔴 OVERDUE: {procedure_name} - Immediate Action Required

**Content:**
- Startup name
- Procedure name
- Original due date
- Days overdue
- Urgent call to action
- Contact compliance advisor

**Color:** Red theme

### HTML vs Plain Text

Both templates include:
- **Plain text version** - For email clients that don't support HTML
- **HTML version** - Styled with colors, boxes, and formatting

## Reminder Status Flow

```
pending → (upcoming email sent) → sent
pending → (overdue email sent) → overdue
```

**Status Values:**
- `pending` - Not yet processed
- `sent` - Upcoming email sent successfully
- `overdue` - Overdue email sent successfully

## Testing

### Test Script

Run comprehensive tests:

```bash
python test_email_notifications.py
```

Tests performed:
1. **SMTP Connection** - Verify Gmail credentials
2. **Simple Email** - Send basic test email
3. **Upcoming Reminder** - Test upcoming template
4. **Overdue Reminder** - Test overdue template
5. **Database Check** - Show pending reminders
6. **Scheduler Check** - Run manual check (optional)

### Manual Testing

1. **Create test reminder:**
   ```python
   from datetime import date, timedelta
   from models import Reminder
   
   reminder = Reminder(
       startup_id=1,
       reminder_date=date.today() + timedelta(days=2),
       message="Test Procedure due by 2026-01-06",
       status="pending"
   )
   session.add(reminder)
   session.commit()
   ```

2. **Trigger email check:**
   ```bash
   POST http://localhost:8000/reminders/scheduler/run-now
   ```

3. **Check your inbox** for test email

## Logging

The system logs all operations:

```
INFO - Starting daily reminder email check...
INFO - Found 5 pending reminders to check
INFO - Sending UPCOMING email for Register Tax Compliance to Startup ABC (2 days remaining)
INFO - ✓ Email sent successfully to founder@example.com
INFO - Reminder email check completed:
INFO -   - Upcoming emails sent: 3
INFO -   - Overdue emails sent: 2
INFO -   - Errors: 0
```

**Log Levels:**
- `INFO` - Normal operations
- `WARNING` - Missing data (startup, email)
- `ERROR` - Email sending failures, SMTP issues

## Troubleshooting

### SMTP Authentication Failed

**Problem:** "SMTP Authentication failed: (535, b'5.7.8 Username and Password not accepted')"

**Solution:**
1. Check EMAIL_USER matches your Gmail address
2. Verify EMAIL_PASS is the 16-character app password (not regular password)
3. Ensure 2-Step Verification is enabled
4. Generate a new app password if needed

### No Emails Received

**Checklist:**
1. Check spam/junk folder
2. Verify reminder.status is "pending" before check
3. Confirm reminder_date is within 3 days or past due
4. Check logs for "Email sent successfully"
5. Verify founder has valid email address

### Scheduler Not Running

**Diagnosis:**
```bash
GET /reminders/scheduler/status
```

If `running: false`:
```bash
POST /reminders/scheduler/start
```

### Database Issues

**Problem:** "No founder or email found for startup"

**Solution:** Ensure Startup has valid founder_id and User exists with email:
```python
startup = session.get(Startup, startup_id)
founder = session.get(User, startup.founder_id)
assert founder.email is not None
```

## Security Best Practices

1. **Never commit .env** - Add to .gitignore
2. **Use app passwords** - Not regular Gmail password
3. **Rotate credentials** - Change app password periodically
4. **Limit access** - Restrict who can access scheduler endpoints
5. **Monitor logs** - Watch for authentication failures

## Production Deployment

### Environment Variables

Set in production environment (not .env file):

```bash
export EMAIL_HOST=smtp.gmail.com
export EMAIL_PORT=587
export EMAIL_USER=your-email@gmail.com
export EMAIL_PASS=your-app-password
```

### Scheduler Configuration

Adjust schedule in `scheduler_service.py`:

```python
# Daily at 9:00 AM (default)
trigger=CronTrigger(hour=9, minute=0)

# Multiple times per day
trigger=CronTrigger(hour='9,15,21', minute=0)  # 9 AM, 3 PM, 9 PM

# Every 6 hours
trigger=CronTrigger(hour='*/6')
```

### Monitoring

Set up monitoring for:
- Email delivery failures
- Scheduler status
- Reminder processing errors
- SMTP connection issues

## API Endpoints Reference

### Reminder Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/reminders/by-startup/{id}` | List all reminders for startup |
| GET | `/reminders/upcoming/{id}?days_ahead=30` | Get upcoming reminders |
| GET | `/reminders/{id}` | Get specific reminder |
| POST | `/reminders/` | Create new reminder |
| PATCH | `/reminders/{id}/mark-sent` | Mark as sent |
| DELETE | `/reminders/{id}` | Delete reminder |

### Scheduler Control

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/reminders/scheduler/status` | Get scheduler status |
| POST | `/reminders/scheduler/run-now` | Trigger check immediately |
| POST | `/reminders/scheduler/start` | Start scheduler |
| POST | `/reminders/scheduler/stop` | Stop scheduler |

## Integration with Existing System

The email notification system integrates seamlessly:

### Reminder Creation

Reminders are created automatically by `reminder_service.py`:

1. **On startup registration** - `initialize_startup_procedures()` creates reminders for all applicable procedures
2. **On manual assignment** - `assign_procedures_to_startup()` creates reminders for new procedures

### Due Date Calculation

Uses the same formula as procedure due dates:
```python
due_days = procedure.get("due_days", 30)
reminder_date = startup.created_at + timedelta(days=due_days)
```

### Status Synchronization

- Reminder statuses updated after email sending
- Compliance dashboards show up-to-date reminder statuses
- Investors can see which reminders have been sent

## Future Enhancements

Potential improvements:

1. **Email Templates** - Customizable templates per procedure type
2. **Frequency Control** - Don't send duplicate emails within X days
3. **Escalation** - Notify compliance advisors for long-overdue items
4. **Digest Mode** - Combine multiple reminders in one email
5. **SMS Notifications** - Add SMS via Twilio for critical items
6. **Webhook Support** - Trigger external systems on overdue
7. **Analytics** - Track email open rates and response times

## Support

For issues or questions:
1. Check logs in console output
2. Run test script: `python test_email_notifications.py`
3. Verify .env configuration
4. Check Gmail app password settings
5. Review API documentation at `/docs`
