from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from sqlalchemy import func

from db import get_session
from models import Startup, Request, User, InvestorRequest, ComplianceStatus
from services.auth_service import require_roles

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/startup/{startup_id}")
def get_startup_stats(
    startup_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("admin", "owner")),
):
    """Return request/compliance metrics for a startup."""
    startup = session.get(Startup, startup_id)
    if not startup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Startup not found")

    # Only admins or the startup owner can view
    if current_user.role.lower() != "admin" and startup.founder_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view stats for your own startup",
        )

    pending = session.exec(
        select(func.count(Request.id)).where(
            Request.startup_id == startup_id, Request.status == "pending"
        )
    ).one()

    active = session.exec(
        select(func.count(Request.id)).where(
            Request.startup_id == startup_id, Request.status == "active"
        )
    ).one()

    rejected = session.exec(
        select(func.count(Request.id)).where(
            Request.startup_id == startup_id, Request.status == "rejected"
        )
    ).one()

    total = pending + active + rejected
    compliance_score = float(active) / float(total) if total > 0 else 0.0

    return {
        "startup_id": startup_id,
        "pending_requests": pending,
        "active_workers": active,
        "rejected_requests": rejected,
        "compliance_score": compliance_score,
    }


@router.get("/investor/{investor_id}")
def get_investor_stats(
    investor_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("admin", "investor")),
):
    """Return compliance portfolio metrics for an investor."""
    # Admins can view any investor; investors can view only their own
    if current_user.role.lower() != "admin" and current_user.id != investor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own investor stats",
        )

    # Get portfolio startup ids
    startup_ids = session.exec(
        select(InvestorRequest.startup_id).where(InvestorRequest.investor_id == investor_id)
    ).all()
    portfolio_company_ids = sorted(set(startup_ids))

    if not portfolio_company_ids:
        return {
            "investor_id": investor_id,
            "portfolio_status": {"compliant": 0.0, "pending": 0.0, "at_risk": 0.0},
            "compliance_by_domain": [],
            "portfolio_companies": [],
            "overall_compliance_rate": 0.0,
            "companies_need_attention": 0,
        }

    # Fetch startups and their badge statuses
    startups = session.exec(
        select(Startup.id, Startup.badge_status).where(Startup.id.in_(portfolio_company_ids))
    ).all()

    total_companies = len(startups)
    compliant = sum(1 for _, badge in startups if (badge or "").lower() == "green")
    at_risk = sum(1 for _, badge in startups if (badge or "").lower() == "red")
    pending = total_companies - compliant - at_risk

    portfolio_status = {
        "compliant": compliant / total_companies if total_companies else 0.0,
        "pending": pending / total_companies if total_companies else 0.0,
        "at_risk": at_risk / total_companies if total_companies else 0.0,
    }

    # Compliance by domain for the portfolio
    statuses = session.exec(
        select(ComplianceStatus).where(ComplianceStatus.startup_id.in_(portfolio_company_ids))
    ).all()

    domain_totals: dict[str, int] = {}
    domain_completed: dict[str, int] = {}
    startup_completed: dict[int, int] = {}
    startup_totals: dict[int, int] = {}

    for status_row in statuses:
        domain = status_row.domain
        domain_totals[domain] = domain_totals.get(domain, 0) + 1
        if status_row.status in {"complete", "completed"}:
            domain_completed[domain] = domain_completed.get(domain, 0) + 1

        sid = status_row.startup_id
        startup_totals[sid] = startup_totals.get(sid, 0) + 1
        if status_row.status in {"complete", "completed"}:
            startup_completed[sid] = startup_completed.get(sid, 0) + 1

    compliance_by_domain = [
        {
            "domain": domain,
            "compliance_rate": (domain_completed.get(domain, 0) / total) if total else 0.0,
        }
        for domain, total in domain_totals.items()
    ]

    # Per-startup compliance rate
    per_startup_rates = []
    for sid in portfolio_company_ids:
        total = startup_totals.get(sid, 0)
        completed = startup_completed.get(sid, 0)
        rate = (completed / total) if total else 0.0
        per_startup_rates.append((sid, rate))

    overall_compliance_rate = (
        sum(rate for _, rate in per_startup_rates) / len(per_startup_rates)
        if per_startup_rates
        else 0.0
    )

    companies_need_attention = sum(1 for _, rate in per_startup_rates if rate < 0.7)

    return {
        "investor_id": investor_id,
        "portfolio_status": portfolio_status,
        "compliance_by_domain": compliance_by_domain,
        "portfolio_companies": portfolio_company_ids,
        "overall_compliance_rate": overall_compliance_rate,
        "companies_need_attention": companies_need_attention,
    }


@router.get("/admin")
def get_admin_stats(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("admin")),
):
    """Return aggregated metrics for admin dashboard."""
    total_users = session.exec(select(func.count(User.id))).one()
    total_startups = session.exec(select(func.count(Startup.id))).one()
    total_investors = session.exec(
        select(func.count(User.id)).where(func.lower(User.role) == "investor")
    ).one()
    nbr_admins = session.exec(
        select(func.count(User.id)).where(func.lower(User.role) == "admin")
    ).one()
    nbr_owners = session.exec(
        select(func.count(User.id)).where(func.lower(User.role) == "owner")
    ).one()
    nbr_workers = session.exec(
        select(func.count(User.id)).where(func.lower(User.role) == "worker")
    ).one()

    # Placeholder values since we don't persist jobs or email logs yet
    scheduled_jobs = 0
    email_success_rate = 0.0

    return {
        "total_users": total_users,
        "total_startups": total_startups,
        "total_investors": total_investors,
        "scheduled_jobs": scheduled_jobs,
        "nbr_admins": nbr_admins,
        "nbr_owners": nbr_owners,
        "nbr_workers": nbr_workers,
        "email_success_rate": email_success_rate,
    }
