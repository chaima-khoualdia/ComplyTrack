# Project Prompt History

This document summarizes the prompts and requests made during the project, organized by phases. Entries are paraphrased and grouped to reflect the evolution of work across the frontend and backend.

## 1. Ideation
- Define user roles and flows: Admin, Startup Owner, Worker, Investor; outline their dashboards and permissions.
- Specify startup data model: fields for founder, legal form (SARL/SA), industry/field, size, location, identifiers (matricule fiscal, RNE).
- Describe "badge status" concept for investors: snapshot of a startup’s compliance across domains.
- Plan dashboards:
  - Owner/Worker: assigned procedures, steps, reminders, and progress.
  - Investor: portfolio overview with compliance pie/bar charts and badge status requests.
  - Admin: system overview, reminders scheduler status, recent activity.

### Evaluation (Ideation)
- Clarity: Strong framing of roles and desired outcomes; enough to map user journeys.
- Completeness: Good coverage of core entities (users, startups, procedures), but "badge status" scope and domain taxonomy benefited from later refinement.
- What you asked me to do: Enumerate roles, draft initial data schema assumptions, and describe target dashboards/features for each role.

## 2. Design
- API design prompts:
  - Auth endpoints with two-step login (login-step1, login-step2/OTP), refresh, current user (`/auth/me`).
  - Startup CRUD; auto-assign procedures on creation.
  - Procedures and steps: list/update/toggle step completion; attach files.
  - Reminders service: upcoming/by-startup, scheduler status endpoint.
  - Requests flow: worker access requests (approve/reject/resend invite).
  - Investor requests: create and list badge status requests; portfolio retrieval (`/investor-requests/by-investor/{id}`).
  - Stats endpoints for dashboards: startup/admin/investor summaries.
- Database/model design prompts:
  - Tables: User, Startup, StartupProcedure, ProcedureStep, Reminder, ComplianceStatus, Request/AccessRequest, InvestorRequest.
  - Procedures source: `procedures.json` defining domains, filters (legal_forms, industries, sizes, countries, locations), steps, due_days.
  - Auto-assignment logic mapping startup attributes to procedures; reminders generated from `due_days`.

### Evaluation (Design)
- Clarity: Endpoint intents were clear; exact shapes evolved during development. The two-step auth flow and assignment logic were well-motivated.
- Completeness: Covered most core contracts; later needed path/param alignment (e.g., investor portfolio route) and file-path resolution for `procedures.json`.
- What you asked me to do: Draft/align API contracts, confirm DB tables and relationships, and validate how procedures mapping and reminders should work.

## 3. Development
- Frontend prompts:
  - Fix navbar overlap and blank/white button styles.
  - Wire Reminders page to backend: upcoming timeline, recent notifications, scheduler status.
  - Build Investor dashboard: pie chart correctness, domain bar chart (switch to grouped bars), abbreviate labels, portfolio selector.
  - Implement Badge Status Request page: load portfolio from backend, submit request, handle loading/errors; fix JSX structure issues.
  - Add resend invite UI on request approval screen; hide owner "Send Invite" where not needed.
  - Post-OTP redirects by role; if owner without startup, guide to creation flow.
  - Ensure step toggles use template `procedure_id` via startup route.
- Backend prompts:
  - Implement `/investor-requests/` POST and `/investor-requests/by-investor/{id}` GET; capture `badge_status_at_request` via compliance summary.
  - On startup creation, call `initialize_startup_procedures()` and sync compliance status.
  - Load and flatten `procedures.json`; filter by legal_form, industry, size, country, and location.
  - Add reminder scheduler (APScheduler) with daily job; expose `/reminders/scheduler/status`.
- Data/seed prompts:
  - Seed multiple startups and investor portfolio to demonstrate charts.
  - Insert ComplianceStatus rows to visualize investor distributions.
  - Clean up and remove temporary seed scripts when finished.

### Evaluation (Development)
- Clarity: Tasks were concrete and actionable (UI tweaks, route fixes, new pages).
- Complexity: Moderate; required careful frontend-backend contract alignment and TypeScript/JSX fixes.
- What you asked me to do (highlights):
  - Resolve layout/UX issues (navbar, buttons, labels).
  - Implement investor charts and badge request flow end-to-end.
  - Wire reminders and scheduler status; show upcoming deadlines with startup names.
  - Seed portfolio and compliance data for realistic dashboards; later remove seed scripts.
  - Add resend invite and ensure procedure step toggles hit correct endpoints.

## 4. Testing & Debugging
- UI fixes and warnings:
  - Resolve navbar overlap and layout spacing.
  - Fix duplicate React keys in Badge Status dropdown by deduping portfolio and using stable keys.
  - Correct JSX closing tags and duplicated fragments in `BadgeStatusRequestPage`.
- Data and logic alignment:
  - Investor pie chart: switch from proportions to company counts.
  - Domain bar chart: render grouped bars and abbreviate long labels.
  - Filter pie slices to non-zero values; compute `overallRate` and `attentionCount` correctly.
  - Remove “General/undefined” domain labels using domain utilities.
- API wiring and errors:
  - Update frontend routes to match backend (`/investor-requests/by-investor/{id}`); ensure numeric IDs in payloads to avoid 403.
  - Fix procedure step toggles to use startup route and correct IDs.
  - Investigate 422 on owner step toggle; align to template `procedure_id`.
- Backend issues investigated:
  - 500 on `POST /auth/login-step1` (traceback requested; suspected server-side error path).
  - New startup missing assigned procedures: updated `procedures_service` to resolve `procedures.json` by absolute path; verified auto-assignment path.
- Reminders page improvements:
  - Show startup name on Upcoming Deadlines timeline for both admin (aggregated) and non-admin views.
  - Derive priorities by days remaining; display notified status.

### Evaluation (Testing & Debugging)
- Thoroughness: Iterative fixes closed compile/runtime issues and UI warnings quickly.
- Root-cause focus: Addressed underlying path resolution for `procedures.json` to restore auto-assignment.
- Remaining risks: Server-side 500 on login-step1 still needs traceback; confirm procedure assignment creates `StartupProcedure` rows on fresh startup creation.
- What you asked me to do: Reproduce UI/API errors, fix warnings, align payloads/routes, and verify dashboards/rendering post-fix.

## 5. Overall Prompt Quality
- Strengths: Clear goals, concrete asks, and quick iteration enabled steady progress across UI, API, and data.
- Gaps: Some endpoint names/shapes changed mid-stream; early capture of exact payload schemas and error formats would have reduced rework.
- Recommendations: When adding new flows, include a short example request/response and enumerated error cases; for data loaders, specify filesystem assumptions (cwd vs absolute paths).

## 6. Suggested Next Prompts
- Provide server traceback for `POST /auth/login-step1` to resolve the 500.
- After creating a startup via UI, dump counts of `StartupProcedure` and first few reminder rows to confirm auto-assignment.
- Add small E2E smoke checklist: create owner → create startup → verify procedures → toggle steps → verify reminders and compliance stats.

## 5. Deployment (Dockerization)
- Add backend Dockerfile (uvicorn, healthcheck with curl).
- Add frontend Dockerfile (Vite build → Nginx serve) and Nginx config proxying `/api` → backend.
- Make frontend API base URL configurable via `VITE_API_BASE_URL` (defaults to localhost in dev, `/api` in Docker).
- Compose setup with two services (frontend, backend); persist SQLite DB via bind mount `data/scos.db`.
- .dockerignore files for backend and frontend; health checks for both services.

---

Notes:
- This history is reconstructed from session logs, code updates, and observed issues; entries are paraphrased to reflect the substance of each prompt.
