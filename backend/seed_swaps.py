"""Seed swap tables with representative data using raw SQL."""

import asyncio
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.models.person import Person
from app.models.user import User


async def seed_swaps():
    settings = get_settings()
    engine = create_async_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    )
    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with AsyncSessionLocal() as db:
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)

        result = await db.execute(select(Person))
        people = result.scalars().all()
        if len(people) < 4:
            print("Need at least 4 people.")
            return

        result = await db.execute(select(User))
        users = result.scalars().all()
        admin_id = str(users[0].id) if users else None

        r = await db.execute(text("SELECT count(*) FROM swap_records"))
        if r.scalar() > 0:
            print("Swap records already exist, skipping.")
            return

        print("Seeding Swap Records...")

        # Swap 1: Approved one-to-one
        s1 = str(uuid.uuid4())
        await db.execute(
            text(
                """
            INSERT INTO swap_records
                (id, source_faculty_id, source_week,
                 target_faculty_id, target_week,
                 swap_type, status, requested_at,
                 requested_by_id, approved_at,
                 approved_by_id, reason, notes)
            VALUES (:id, :sfid, :sw, :tfid, :tw,
                    'one_to_one', 'approved', :req,
                    :admin, :appr, :admin2,
                    'Conference attendance',
                    'Approved by coordinator')
        """
            ),
            {
                "id": s1,
                "sfid": str(people[0].id),
                "sw": (now + timedelta(days=7)).date(),
                "tfid": str(people[1].id),
                "tw": (now + timedelta(days=14)).date(),
                "req": week_ago,
                "admin": admin_id,
                "appr": week_ago + timedelta(days=1),
                "admin2": admin_id,
            },
        )
        print(f"  - {people[0].name} <-> {people[1].name} (approved)")

        # Swap 2: Pending absorb
        s2 = str(uuid.uuid4())
        await db.execute(
            text(
                """
            INSERT INTO swap_records
                (id, source_faculty_id, source_week,
                 target_faculty_id,
                 swap_type, status, requested_at,
                 requested_by_id, reason)
            VALUES (:id, :sfid, :sw, :tfid,
                    'absorb', 'pending', :req,
                    :admin, 'Family emergency coverage')
        """
            ),
            {
                "id": s2,
                "sfid": str(people[2].id),
                "sw": (now + timedelta(days=21)).date(),
                "tfid": str(people[3].id),
                "req": now - timedelta(days=2),
                "admin": admin_id,
            },
        )
        print(f"  - {people[2].name} -> {people[3].name} (pending)")

        # Swap 3: Executed
        s3 = str(uuid.uuid4())
        p4 = people[4] if len(people) > 4 else people[0]
        p5 = people[5] if len(people) > 5 else people[1]
        await db.execute(
            text(
                """
            INSERT INTO swap_records
                (id, source_faculty_id, source_week,
                 target_faculty_id, target_week,
                 swap_type, status, requested_at,
                 requested_by_id, approved_at,
                 approved_by_id, executed_at,
                 executed_by_id, reason, notes)
            VALUES (:id, :sfid, :sw, :tfid, :tw,
                    'one_to_one', 'executed', :req,
                    :admin, :appr, :admin2,
                    :exec, :admin3,
                    'Training schedule conflict',
                    'Executed successfully')
        """
            ),
            {
                "id": s3,
                "sfid": str(p4.id),
                "sw": (now - timedelta(days=7)).date(),
                "tfid": str(p5.id),
                "tw": (now - timedelta(days=14)).date(),
                "req": now - timedelta(days=21),
                "admin": admin_id,
                "appr": now - timedelta(days=20),
                "admin2": admin_id,
                "exec": now - timedelta(days=14),
                "admin3": admin_id,
            },
        )
        print(f"  - {p4.name} <-> {p5.name} (executed)")

        # --- Swap Approvals ---
        print("\nSeeding Swap Approvals...")
        swaps_info = [
            (s1, people[0].id, people[1].id, True, week_ago),
            (s2, people[2].id, people[3].id, None, None),
            (s3, p4.id, p5.id, True, now - timedelta(days=20)),
        ]
        for sid, src_id, tgt_id, approved, resp_at in swaps_info:
            # Source approval
            await db.execute(
                text(
                    """
                INSERT INTO swap_approvals
                    (id, swap_id, faculty_id, role,
                     approved, responded_at)
                VALUES (:id, :sid, :fid, 'source',
                        true, :resp)
            """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "sid": sid,
                    "fid": str(src_id),
                    "resp": resp_at or now,
                },
            )
            # Target approval
            await db.execute(
                text(
                    """
                INSERT INTO swap_approvals
                    (id, swap_id, faculty_id, role,
                     approved, responded_at)
                VALUES (:id, :sid, :fid, 'target',
                        :appr, :resp)
            """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "sid": sid,
                    "fid": str(tgt_id),
                    "appr": approved,
                    "resp": resp_at,
                },
            )
            print(f"  - Approvals for swap {sid[:8]}...")

        await db.commit()
        print("\nSwap seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_swaps())
