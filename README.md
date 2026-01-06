# legal-compliance-os

A comprehensive legal compliance tracking system for Tunisian startups, providing automated procedure assignment, compliance monitoring, and deadline reminders based on actual regulatory requirements.

## ✨ Latest Feature: Automatic Reminder Generation

The system now automatically generates compliance deadline reminders when startups register or procedures are assigned. Reminders are calculated using Tunisian regulatory deadlines from procedures.json.

### Quick Start

```bash
# 1. Start the API
python -m uvicorn app:app --reload

# 2. Create a startup (reminders auto-generated)
curl -X POST http://localhost:8000/startups/ \
  -H "Content-Type: application/json" \
  -d '{
    "founder_id": 1,
    "name": "TechCorp Tunisia",
    "matricule_fiscal": "1234567890",
    "rne_number": "0987654321",
    "legal_form": "SARL",
    "field": "tech",
    "sector": "private",
    "size": "small",
    "location": "Tunis"
  }'

# 3. Check reminders created automatically
curl http://localhost:8000/reminders/by-startup/1

# 4. View upcoming deadlines (next 30 days)
curl http://localhost:8000/reminders/upcoming/1?days_ahead=30
```

## Key Features

### 🔄 Automatic Procedure Assignment
- Procedures automatically assigned when startup registers
- Based on legal form, field, size, and location
- Powered by procedures.json with Tunisian regulations

### ⏰ Automated Reminders
- Reminders created automatically for each procedure
- Due dates calculated from startup registration date + procedure deadline
- Tunisian compliance deadlines: 10 to 365 days
- Ready for email notifications (Step 2)

### 📊 Compliance Tracking
- Track procedure status across domains
- Monitor step-level completion
- Calculate accurate progress percentages
- Badge status (red/green) based on compliance

### 🎯 Startup Label Support
- Startup Label application (365-day deadline)
- Valid for 2920 days (8 years)
- Automatic tracking with full documentation requirements

## Core Components

### Services
- **procedures_service.py** - Load and filter Tunisian procedures
- **assignment_service.py** - Assign procedures and auto-init reminders
- **reminder_service.py** - Generate and manage reminders
- **compliance_service.py** - Track domain-level compliance
- **listing_service.py** - Build enriched API responses
- **progress_service.py** - Calculate procedure progress

### API Endpoints
- `POST /startups/` - Create startup (auto-assigns procedures + generates reminders)
- `GET /reminders/upcoming/{startup_id}` - Get upcoming deadlines
- `GET /reminders/by-startup/{startup_id}` - Get all reminders
- `PATCH /reminders/{id}/mark-sent` - Mark reminder as sent

## Data Files

### procedures.json
Contains all applicable compliance procedures with:
- `due_days`: Deadline in days from registration
- `authority`: Regulatory body responsible
- `required_documents`: Documents needed
- `steps`: Procedure breakdown

### Tunisian Compliance Deadlines
- **Tax Compliance**: 10 days (fastest)
- **Legal Registration** (SARL/SA): 15 days
- **Free Zone Compliance**: 30 days
- **Tech/IP Compliance**: 45 days
- **Healthcare Licensing**: 90 days
- **Large Company Reporting**: 90 days
- **Finance Sector Licensing**: 240 days
- **Startup Label Application**: 365 days (slowest)

## Documentation

- **COMPLETE_REPORT.md** - Full implementation report
- **REMINDER_IMPLEMENTATION.md** - Complete reminder system documentation
- **REMINDER_QUICK_REFERENCE.md** - Quick start and examples
- **SYSTEM_OVERVIEW.md** - Visual system architecture
- **IMPLEMENTATION_SUMMARY.md** - Summary of all changes

## Testing

```bash
# Run reminder system test
python test_reminder_generation.py

# Expected output: System creates 9 reminders with correct due dates
```

## Database Schema

Includes tables for:
- startups
- startup_procedures
- compliance_statuses
- reminders (NEW)
- steps
- sources
- users
- investor_requests

## Example Timeline

For a SARL tech startup registered on Jan 4, 2026:

| Deadline | Days | Task |
|----------|------|------|
| Jan 14 | 10 | Tax Compliance |
| Jan 19 | 15 | Register SARL |
| Feb 18 | 45 | Tech/IP Compliance |
| Jan 4, 2027 | 365 | Startup Label Application |

## Next Steps: Email Notifications

Reminders table is populated and ready for Step 2 email integration:
1. Query `/reminders/upcoming/{startup_id}?days_ahead=7`
2. Send email to founder
3. Update status with `PATCH /reminders/{id}/mark-sent`
4. Schedule daily background job

## Architecture

```
Startup Registration
  ↓
Auto-assign applicable procedures
  ↓
Generate reminders with Tunisian deadlines
  ↓
Reminders table populated
  ↓
Ready for email notifications
```

## Status

✅ Step 1 Complete: Automatic Reminder Generation
🔄 Step 2 Ready: Email Notification System (in planning)
🔄 Step 3 Ready: Dashboard Display (in planning)

## License

TBD