# ComplyTrack

<div align="center">

**Master compliance. Protect investments.**

A comprehensive legal compliance management platform designed for startups and investors, streamlining regulatory tracking across Tax, Auditing, Legal, Licensing, Intellectual Property, and Special Economic Zones.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.127.0-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=flat&logo=typescript)](https://www.typescriptlang.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker)](https://www.docker.com/)

</div>

---

## 🎯 Overview

ComplyTrack provides an integrated compliance management solution that addresses the critical challenges startups face in maintaining regulatory compliance. The platform combines automated tracking, role-based dashboards, and intelligent reminders to reduce compliance risk and administrative burden.

### Key Benefits

- **For Startups**: Automated deadline tracking, procedure management, and compliance monitoring
- **For Investors**: Portfolio-wide visibility, risk assessment, and badge status requests
- **For Administrators**: System-wide oversight, user management, and analytics
- **For Workers**: Task assignment, step-by-step guidance, and progress tracking

---

## ✨ Features

### 🔐 Secure Authentication
- JWT-based authentication with HTTPBearer
- Two-factor authentication via email OTP
- Role-based access control (Admin, Investor, Owner, Worker)

### 📋 Procedure Management
- Template-based compliance procedures
- Automated assignment based on startup profile
- Step-by-step tracking with progress indicators
- Six compliance domains: Tax, Auditing, Legal, Licensing, IP, Special Zones

### ⏰ Automated Reminders
- Daily email notifications at 9:00 AM
- Automatic deadline calculation from registration date
- Scheduler control (start/stop/run-now)
- Startup-specific reminder context

### 📊 Real-Time Dashboards
- Role-specific interfaces with tailored data views
- Color-coded risk indicators (green/yellow/red)
- Live statistics and compliance status
- Portfolio-wide visibility for investors

### 🔄 Request Management
- Worker join requests with approval workflow
- Badge status requests for investor due diligence
- Email notifications for approvals/rejections
- Invitation code generation and confirmation

---

## 🏗️ Architecture

### Backend Stack
- **FastAPI** - High-performance async API framework
- **SQLModel** - Type-safe ORM combining SQLAlchemy + Pydantic
- **SQLite** - Embedded database (production-ready with PostgreSQL migration path)
- **APScheduler** - Job scheduling for automated reminders
- **JWT** - Secure token-based authentication
- **Passlib** - Password hashing with Argon2/Bcrypt

### Frontend Stack
- **React 18** - Component-based UI framework
- **TypeScript** - Type-safe JavaScript
- **Vite** - Fast build tool and dev server
- **React Router v6** - Client-side routing
- **Axios** - HTTP client for API calls
- **Tailwind CSS** - Utility-first styling
- **Lucide Icons** - Clean, consistent iconography

### Deployment
- **Docker** - Containerized deployment
- **docker-compose** - Multi-service orchestration
- **Nginx** - Reverse proxy for frontend
- **Health checks** - Built-in monitoring

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (for containerized deployment)

### Local Development

#### Backend Setup

```bash
# Clone repository
git clone <repository-url>
cd legal-compliance-os

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Unix/MacOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run development server
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Backend API: `http://localhost:8000`  
API Documentation: `http://localhost:8000/docs`

#### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Configure environment
# Update src/api.ts with backend URL if needed

# Run development server
npm run dev
```

Frontend: `http://localhost:5173`

---

## 🐳 Docker Deployment

### Build and Run

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Access Points

- **Frontend**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`
- **API Docs**: `http://localhost:8000/docs`

### Architecture

```
Frontend (React + Nginx)
    ↓ /api proxy
Backend (FastAPI)
    ↓
SQLite Database (persisted in ./data/)
```

---

## 📚 API Overview

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login-step1` - Email/password login (OTP sent)
- `POST /auth/login-step2` - OTP verification (JWT issued)

### Startups
- `GET /startups` - List all startups
- `POST /startups` - Create startup (auto-assigns procedures)
- `GET /startups/{id}` - Get startup details
- `PUT /startups/{id}` - Update startup
- `DELETE /startups/{id}` - Delete startup

### Procedures
- `GET /startups/{id}/procedures` - Get assigned procedures
- `PATCH /startups/{id}/procedures/{pid}/steps/{sid}` - Update step status
- `DELETE /startups/{id}/procedures/{pid}` - Remove procedure

### Reminders
- `GET /reminders/by-startup/{id}` - Get startup reminders
- `GET /reminders/upcoming/{id}` - Get upcoming deadlines
- `POST /reminders/scheduler/run-now` - Trigger scheduler
- `POST /reminders/scheduler/start` - Start automated reminders
- `POST /reminders/scheduler/stop` - Stop scheduler

### Requests
- `POST /requests/` - Worker creates join request
- `GET /requests/mine` - Get my requests
- `GET /requests/startup/{id}` - Get startup requests (owner)
- `PATCH /requests/{id}/approve` - Approve request
- `PATCH /requests/{id}/reject` - Reject request

Full API documentation: `http://localhost:8000/docs`

---

## 🗄️ Database Schema

### Core Entities

- **User** - Authentication and role management
- **Startup** - Company profiles and founder relationships
- **StartupProcedure** - Assigned procedures with status tracking
- **ProcedureStep** - Individual steps within procedures
- **Reminder** - Automated deadline notifications
- **Request** - Worker join requests with approval workflow
- **InvestorRequest** - Badge status requests from investors
- **ComplianceStatus** - Domain-specific compliance tracking
- **Source** - Regulatory authorities and data sources

### Database File

- **Development**: `./data/scos.db`
- **Docker**: Mounted to `/app/data/scos.db`

---

## 🎨 User Roles

### Admin
- Full system access
- User management
- System-wide statistics
- All startups and procedures

### Investor
- Portfolio view across multiple startups
- Badge status requests
- Compliance visibility
- Investment tracking

### Owner (Startup Founder)
- Manage startup profile
- Approve/reject worker requests
- View compliance status

### Worker
- View assigned procedures
- Update step completion
- Request to join startups
- Track personal tasks

---

## 🔧 Configuration

### Environment Variables

```env
# JWT Configuration
JWT_SECRET=your-super-secret-key-min-32-chars
JWT_ALGORITHM=HS256

# Email Configuration (SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-password
EMAIL_FROM=your-email@gmail.com

# OTP Configuration
OTP_EXPIRATION_MINUTES=5

# Database (optional, defaults to ./data/scos.db)
DATABASE_PATH=./data/scos.db
```

---

## 📖 Documentation

- **API Documentation**: Interactive Swagger UI at `/docs`
- **Project Report**: [`project_documentation.tex`](project_documentation.tex) (LaTeX)
- **Procedures Data**: [`procedures.json`](procedures.json)
- **Rules Configuration**: [`rules.json`](rules.json)

---

## 🧪 Testing

```bash
# Run backend tests
pytest

# Test authentication flow
curl -X POST http://localhost:8000/auth/login-step1 \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Health check
curl http://localhost:8000/ping
```

---

## 🔮 Future Enhancements

- [ ] Document attachment and storage
- [ ] Advanced analytics and trend reporting
- [ ] Mobile application (iOS/Android)
- [ ] PostgreSQL migration for scalability
- [ ] Multi-language support
- [ ] Integration with government regulatory APIs
- [ ] Automated compliance risk modeling (AI/ML)
- [ ] Audit trail and compliance history
- [ ] SMS and push notifications
- [ ] Webhook integrations

---



## 📄 License

To be determined.

---

## 👥 Authors

**Khoualdia chaima **  
Academic Year: 2025-2026

---

## 🙏 Acknowledgments

- FastAPI for the powerful backend framework
- React team for the excellent frontend library
- SQLModel for type-safe database operations
- The open-source community

---

<div align="center">

**Built with ❤️ for startup compliance management**

[Documentation](http://localhost:8000/docs) • [Report Issues](issues) • [Request Features](issues)

</div>