"""Admin delete-impact endpoints for cascading delete warnings."""

from collections import defaultdict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.schema import Table

from app.api.dependencies.role_filter import require_admin
from app.db.base import Base
from app.db.session import get_db
from app.schemas.delete_impact import (
    DeleteImpactDependency,
    DeleteImpactResource,
    DeleteImpactResponse,
)

router = APIRouter(prefix="/admin/delete-impact", tags=["admin-delete-impact"])

_RESOURCE_TABLES = {
    DeleteImpactResource.person: "people",
    DeleteImpactResource.rotation_template: "rotation_templates",
    DeleteImpactResource.block: "blocks",
    DeleteImpactResource.activity: "activities",
    DeleteImpactResource.academic_block: "academic_blocks",
}

_SKIP_TABLES = {"alembic_version"}


def _get_table(table_name: str) -> Table:
    table = Base.metadata.tables.get(table_name)
    if table is None:
        raise RuntimeError(f"Table '{table_name}' not found in metadata")
    return table


def _find_dependents(target_table: Table) -> dict[Table, list]:
    dependents: dict[Table, list] = defaultdict(list)
    for table in Base.metadata.tables.values():
        if table.name in _SKIP_TABLES or table.name.endswith("_version"):
            continue
        for column in table.c:
            if not column.foreign_keys:
                continue
            for fk in column.foreign_keys:
                if fk.column.table is target_table:
                    dependents[table].append(column)
                    break
    return dependents


def _count_dependents(
    db: Session, target_table: Table, resource_id: UUID
) -> list[DeleteImpactDependency]:
    dependents = _find_dependents(target_table)
    results: list[DeleteImpactDependency] = []

    for table, columns in dependents.items():
        if not columns:
            continue
        condition = or_(*[column == resource_id for column in columns])
        count = (
            db.execute(select(func.count()).select_from(table).where(condition))
            .scalar()
            or 0
        )
        if count:
            results.append(
                DeleteImpactDependency(
                    table=table.name,
                    count=int(count),
                    columns=[column.name for column in columns],
                )
            )

    results.sort(key=lambda item: (-item.count, item.table))
    return results


@router.get("", response_model=DeleteImpactResponse, dependencies=[Depends(require_admin())])
def get_delete_impact(
    resource_type: DeleteImpactResource = Query(
        ..., description="Resource type to analyze"
    ),
    resource_id: UUID = Query(..., description="Resource ID to analyze"),
    db: Session = Depends(get_db),
) -> DeleteImpactResponse:
    """Return dependent record counts for cascading delete warnings."""
    table_name = _RESOURCE_TABLES.get(resource_type)
    if not table_name:
        raise HTTPException(status_code=400, detail="Unsupported resource type")

    target_table = _get_table(table_name)
    exists = (
        db.execute(
            select(func.count())
            .select_from(target_table)
            .where(target_table.c.id == resource_id)
        ).scalar()
        or 0
    )
    if exists == 0:
        raise HTTPException(status_code=404, detail="Resource not found")

    dependencies = _count_dependents(db, target_table, resource_id)
    total_dependents = sum(dep.count for dep in dependencies)

    return DeleteImpactResponse(
        resource_type=resource_type,
        resource_id=resource_id,
        dependencies=dependencies,
        total_dependents=total_dependents,
    )
