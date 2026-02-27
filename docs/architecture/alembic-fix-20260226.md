# Alembic Migration Fix — 2026-02-27T02:44:43Z

## Problem
DB alembic_version was stuck at orphaned revision 'a399bc3fb338' (deleted migration).
5 pending migrations were unapplied: blk12_act_reqs, fix_nf_combo_reqs, annual_batch, person_ay, drop_legacy_leave.

## Fix Applied
1. pg_dump backup created at backend/backup_20260226_pre_alembic.dump
2. Stamped DB to 20260219_add_gt_tables (last known-good, game_theory tables existed)
3. Fixed table ownership (aaronmontgomerymini → scheduler) for all public tables
4. Applied 5 pending migrations to head (8b9cea518229)

## Verification
- alembic current: 8b9cea518229 (head) — single head
- person_academic_years: 39 rows (seeded from Person.pgy_level)
- No multiple heads in migration chain
