"""
Audit Service — logs every action on authorization codes and claims.
"""

import logging

from sqlalchemy.orm import Session

from app.models.models import ClaimAuditLog

log = logging.getLogger(__name__)


def log_action(
    db: Session,
    *,
    entity_type: str,
    entity_id: str,
    action: str,
    actor_type: str,
    actor_id: str,
    details: dict | None = None,
    ip_address: str | None = None,
) -> ClaimAuditLog:
    """
    Record an audit entry.

    entity_type: 'authorization_code' | 'claim'
    actor_type:  'agent' | 'member' | 'system'
    """
    entry = ClaimAuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor_type=actor_type,
        actor_id=actor_id,
        details=details,
        ip_address=ip_address,
    )
    db.add(entry)
    db.commit()
    log.info(
        "AUDIT: %s %s on %s/%s by %s/%s",
        action,
        entity_type,
        entity_type,
        entity_id,
        actor_type,
        actor_id,
    )
    return entry


def get_audit_trail(
    db: Session,
    *,
    entity_type: str,
    entity_id: str,
) -> list[ClaimAuditLog]:
    """Get full audit trail for an entity, newest first."""
    return (
        db.query(ClaimAuditLog)
        .filter(
            ClaimAuditLog.entity_type == entity_type,
            ClaimAuditLog.entity_id == entity_id,
        )
        .order_by(ClaimAuditLog.created_at.desc())
        .all()
    )
