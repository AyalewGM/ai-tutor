"""Role -> permission mapping for staff (internal) access.

Endpoints check a *permission*, never a role name, so new staff roles
(SUPPORT, ANALYST) can be introduced by editing ROLE_PERMISSIONS alone.
Family roles (PARENT/GUARDIAN) carry no staff permissions.
"""

from enum import StrEnum


class Permission(StrEnum):
    ADMIN_ACCESS = "admin.access"
    AUDIT_READ = "admin.audit.read"
    FAMILIES_READ = "admin.families.read"
    FAMILIES_APPROVE = "admin.families.approve"
    METRICS_READ = "admin.metrics.read"
    AI_USAGE_READ = "admin.ai_usage.read"
    PLANS_MANAGE = "admin.plans.manage"
    AI_BUDGETS_MANAGE = "admin.ai_budgets.manage"


ROLE_PERMISSIONS: dict[str, frozenset[Permission]] = {
    "ADMIN": frozenset(Permission),
    # Customer-facing staff: see and decide family approvals, nothing else.
    "SUPPORT": frozenset({
        Permission.ADMIN_ACCESS,
        Permission.FAMILIES_READ,
        Permission.FAMILIES_APPROVE,
    }),
    # Read-only reporting: metrics and AI spend, no write permissions.
    "ANALYST": frozenset({
        Permission.ADMIN_ACCESS,
        Permission.METRICS_READ,
        Permission.AI_USAGE_READ,
    }),
}

STAFF_ROLES = frozenset(ROLE_PERMISSIONS)


def permissions_for(role: str | None) -> frozenset[Permission]:
    return ROLE_PERMISSIONS.get((role or "").upper(), frozenset())


def has_permission(role: str | None, permission: Permission) -> bool:
    return permission in permissions_for(role)
