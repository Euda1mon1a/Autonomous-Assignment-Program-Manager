-- ╔═══════════════════════════════════════════════════════════════╗
-- ║            LICH'S PHYLACTERY - Database Soul                  ║
-- ╚═══════════════════════════════════════════════════════════════╝
--
-- Generated: 2026-01-16T05:35:53Z
-- Branch: feat/mcp-exotic-dependencies
-- Commit: 591b2f12
--
-- Contains NO DATA - just structure. The soul, not the flesh.
-- Safe to commit. Sacred timeline preserved.

--
-- PostgreSQL database dump
--

\restrict mM7vwmAXeHpmDeA80fqHWI8IHi9NvkxcCL7etBmmg2ytpKkuag5Mw3D2CO6nG7K

-- Dumped from database version 15.15 (Debian 15.15-1.pgdg12+1)
-- Dumped by pg_dump version 15.15 (Debian 15.15-1.pgdg12+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner:
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


--
-- Name: conflictresolutionmode; Type: TYPE; Schema: public; Owner: scheduler
--

CREATE TYPE public.conflictresolutionmode AS ENUM (
    'replace',
    'merge',
    'upsert'
);


ALTER TYPE public.conflictresolutionmode OWNER TO scheduler;

--
-- Name: daytype; Type: TYPE; Schema: public; Owner: scheduler
--

CREATE TYPE public.daytype AS ENUM (
    'NORMAL',
    'FEDERAL_HOLIDAY',
    'TRAINING_HOLIDAY',
    'MINIMAL_MANNING',
    'EO_CLOSURE',
    'INAUGURATION_DAY'
);


ALTER TYPE public.daytype OWNER TO scheduler;

--
-- Name: draft_assignment_change_type; Type: TYPE; Schema: public; Owner: scheduler
--

CREATE TYPE public.draft_assignment_change_type AS ENUM (
    'add',
    'modify',
    'delete'
);


ALTER TYPE public.draft_assignment_change_type OWNER TO scheduler;

--
-- Name: draft_flag_severity; Type: TYPE; Schema: public; Owner: scheduler
--

CREATE TYPE public.draft_flag_severity AS ENUM (
    'error',
    'warning',
    'info'
);


ALTER TYPE public.draft_flag_severity OWNER TO scheduler;

--
-- Name: draft_flag_type; Type: TYPE; Schema: public; Owner: scheduler
--

CREATE TYPE public.draft_flag_type AS ENUM (
    'conflict',
    'acgme_violation',
    'coverage_gap',
    'manual_review'
);


ALTER TYPE public.draft_flag_type OWNER TO scheduler;

--
-- Name: draft_source_type; Type: TYPE; Schema: public; Owner: scheduler
--

CREATE TYPE public.draft_source_type AS ENUM (
    'solver',
    'manual',
    'swap',
    'import'
);


ALTER TYPE public.draft_source_type OWNER TO scheduler;

--
-- Name: emailstatus; Type: TYPE; Schema: public; Owner: scheduler
--

CREATE TYPE public.emailstatus AS ENUM (
    'queued',
    'sent',
    'failed',
    'bounced'
);


ALTER TYPE public.emailstatus OWNER TO scheduler;

--
-- Name: emailtemplatetype; Type: TYPE; Schema: public; Owner: scheduler
--

CREATE TYPE public.emailtemplatetype AS ENUM (
    'schedule_change',
    'swap_notification',
    'certification_expiry',
    'absence_reminder',
    'compliance_alert'
);


ALTER TYPE public.emailtemplatetype OWNER TO scheduler;

--
-- Name: importbatchstatus; Type: TYPE; Schema: public; Owner: scheduler
--

CREATE TYPE public.importbatchstatus AS ENUM (
    'staged',
    'approved',
    'rejected',
    'applied',
    'rolled_back',
    'failed'
);


ALTER TYPE public.importbatchstatus OWNER TO scheduler;

--
-- Name: operationalintent; Type: TYPE; Schema: public; Owner: scheduler
--

CREATE TYPE public.operationalintent AS ENUM (
    'NORMAL',
    'REDUCED_CAPACITY',
    'NON_OPERATIONAL'
);


ALTER TYPE public.operationalintent OWNER TO scheduler;

--
-- Name: overlaptype; Type: TYPE; Schema: public; Owner: scheduler
--

CREATE TYPE public.overlaptype AS ENUM (
    'none',
    'partial',
    'exact',
    'contained',
    'contains'
);


ALTER TYPE public.overlaptype OWNER TO scheduler;

--
-- Name: schedule_draft_status; Type: TYPE; Schema: public; Owner: scheduler
--

CREATE TYPE public.schedule_draft_status AS ENUM (
    'draft',
    'published',
    'rolled_back',
    'discarded'
);


ALTER TYPE public.schedule_draft_status OWNER TO scheduler;

--
-- Name: stagedabsencestatus; Type: TYPE; Schema: public; Owner: scheduler
--

CREATE TYPE public.stagedabsencestatus AS ENUM (
    'pending',
    'approved',
    'skipped',
    'applied',
    'failed'
);


ALTER TYPE public.stagedabsencestatus OWNER TO scheduler;

--
-- Name: stagedassignmentstatus; Type: TYPE; Schema: public; Owner: scheduler
--

CREATE TYPE public.stagedassignmentstatus AS ENUM (
    'pending',
    'approved',
    'skipped',
    'applied',
    'failed'
);


ALTER TYPE public.stagedassignmentstatus OWNER TO scheduler;

--
-- Name: update_rag_documents_updated_at(); Type: FUNCTION; Schema: public; Owner: scheduler
--

CREATE FUNCTION public.update_rag_documents_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$;


ALTER FUNCTION public.update_rag_documents_updated_at() OWNER TO scheduler;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: absence_version; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.absence_version (
    id uuid NOT NULL,
    person_id uuid,
    start_date date,
    end_date date,
    absence_type character varying(50),
    is_blocking boolean,
    deployment_orders boolean,
    tdy_location character varying(255),
    replacement_activity character varying(255),
    notes text,
    created_at timestamp without time zone,
    transaction_id bigint NOT NULL,
    operation_type smallint NOT NULL,
    end_transaction_id bigint
);


ALTER TABLE public.absence_version OWNER TO scheduler;

--
-- Name: absences; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.absences (
    id uuid NOT NULL,
    person_id uuid NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    absence_type character varying(50) NOT NULL,
    deployment_orders boolean,
    tdy_location character varying(255),
    replacement_activity character varying(255),
    notes text,
    created_at timestamp without time zone DEFAULT now(),
    is_blocking boolean DEFAULT false,
    return_date_tentative boolean DEFAULT false NOT NULL,
    created_by_id uuid,
    is_away_from_program boolean NOT NULL,
    is_tdy boolean DEFAULT false,
    CONSTRAINT check_absence_dates CHECK ((end_date >= start_date)),
    CONSTRAINT check_absence_type CHECK (((absence_type)::text = ANY ((ARRAY['vacation'::character varying, 'deployment'::character varying, 'medical'::character varying, 'family_emergency'::character varying, 'conference'::character varying, 'bereavement'::character varying, 'emergency_leave'::character varying, 'sick'::character varying, 'convalescent'::character varying, 'maternity_paternity'::character varying, 'training'::character varying, 'military_duty'::character varying])::text[])))
);


ALTER TABLE public.absences OWNER TO scheduler;

--
-- Name: absences_version; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.absences_version (
    id uuid NOT NULL,
    person_id uuid,
    start_date date,
    end_date date,
    absence_type character varying(50),
    is_blocking boolean,
    return_date_tentative boolean,
    created_by_id uuid,
    deployment_orders boolean,
    tdy_location character varying(255),
    replacement_activity character varying(255),
    notes text,
    created_at timestamp without time zone,
    transaction_id bigint NOT NULL,
    operation_type smallint NOT NULL,
    end_transaction_id bigint,
    person_id_mod boolean,
    start_date_mod boolean,
    end_date_mod boolean,
    absence_type_mod boolean,
    is_blocking_mod boolean,
    return_date_tentative_mod boolean,
    created_by_id_mod boolean,
    deployment_orders_mod boolean,
    tdy_location_mod boolean,
    replacement_activity_mod boolean,
    notes_mod boolean,
    created_at_mod boolean
);


ALTER TABLE public.absences_version OWNER TO scheduler;

--
-- Name: activities; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.activities (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    code character varying(50) NOT NULL,
    display_abbreviation character varying(20),
    activity_category character varying(20) NOT NULL,
    font_color character varying(50),
    background_color character varying(50),
    requires_supervision boolean DEFAULT true NOT NULL,
    is_protected boolean DEFAULT false NOT NULL,
    counts_toward_clinical_hours boolean DEFAULT true NOT NULL,
    display_order integer DEFAULT 0 NOT NULL,
    is_archived boolean DEFAULT false NOT NULL,
    archived_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    provides_supervision boolean DEFAULT false NOT NULL,
    counts_toward_physical_capacity boolean DEFAULT false NOT NULL,
    capacity_units integer DEFAULT 1 NOT NULL
);


ALTER TABLE public.activities OWNER TO scheduler;

--
-- Name: COLUMN activities.provides_supervision; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.activities.provides_supervision IS 'True for supervision activities (AT, PCAT, DO) that count toward supervision ratios';


--
-- Name: activity_log; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.activity_log (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid,
    action_type character varying(50) NOT NULL,
    target_entity character varying(100),
    target_id character varying(100),
    details jsonb DEFAULT '{}'::jsonb,
    ip_address character varying(45),
    user_agent character varying(500),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.activity_log OWNER TO scheduler;

--
-- Name: agent_embeddings; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.agent_embeddings (
    agent_name character varying NOT NULL,
    embedding public.vector(384) NOT NULL,
    spec_hash character varying NOT NULL,
    capabilities text,
    updated_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.agent_embeddings OWNER TO scheduler;

--
-- Name: COLUMN agent_embeddings.embedding; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.agent_embeddings.embedding IS '384-dim sentence-transformers embedding';


--
-- Name: COLUMN agent_embeddings.spec_hash; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.agent_embeddings.spec_hash IS 'Hash of agent specification for versioning';


--
-- Name: COLUMN agent_embeddings.capabilities; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.agent_embeddings.capabilities IS 'Comma-separated list of agent capabilities';


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.alembic_version (
    version_num character varying(128) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO scheduler;

--
-- Name: allostasis_records; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.allostasis_records (
    id uuid NOT NULL,
    entity_id uuid NOT NULL,
    entity_type character varying(20) NOT NULL,
    calculated_at timestamp without time zone DEFAULT now() NOT NULL,
    consecutive_weekend_calls integer,
    nights_past_month integer,
    schedule_changes_absorbed integer,
    holidays_worked_this_year integer,
    overtime_hours_month double precision,
    coverage_gap_responses integer,
    cross_coverage_events integer,
    acute_stress_score double precision,
    chronic_stress_score double precision,
    total_allostatic_load double precision,
    allostasis_state character varying(30),
    risk_level character varying(20),
    CONSTRAINT check_allostasis_state CHECK (((allostasis_state IS NULL) OR ((allostasis_state)::text = ANY (ARRAY[('homeostasis'::character varying)::text, ('allostasis'::character varying)::text, ('allostatic_load'::character varying)::text, ('allostatic_overload'::character varying)::text])))),
    CONSTRAINT check_entity_type CHECK (((entity_type)::text = ANY (ARRAY[('faculty'::character varying)::text, ('system'::character varying)::text])))
);


ALTER TABLE public.allostasis_records OWNER TO scheduler;

--
-- Name: api_keys; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.api_keys (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    key_hash character varying(255) NOT NULL,
    key_prefix character varying(16) NOT NULL,
    owner_id uuid,
    scopes text,
    allowed_ips text,
    rate_limit_per_minute integer DEFAULT 100,
    rate_limit_per_hour integer DEFAULT 5000,
    is_active boolean DEFAULT true NOT NULL,
    expires_at timestamp without time zone,
    revoked_at timestamp without time zone,
    revoked_by_id uuid,
    revoked_reason character varying(500),
    rotated_from_id uuid,
    rotated_to_id uuid,
    last_used_at timestamp without time zone,
    last_used_ip character varying(45),
    total_requests integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.api_keys OWNER TO scheduler;

--
-- Name: application_settings; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.application_settings (
    id uuid NOT NULL,
    scheduling_algorithm character varying(50) DEFAULT 'greedy'::character varying NOT NULL,
    work_hours_per_week integer DEFAULT 80 NOT NULL,
    max_consecutive_days integer DEFAULT 6 NOT NULL,
    min_days_off_per_week integer DEFAULT 1 NOT NULL,
    pgy1_supervision_ratio character varying(10) DEFAULT '''1:2'''::character varying NOT NULL,
    pgy2_supervision_ratio character varying(10) DEFAULT '''1:4'''::character varying NOT NULL,
    pgy3_supervision_ratio character varying(10) DEFAULT '''1:4'''::character varying NOT NULL,
    enable_weekend_scheduling boolean DEFAULT true NOT NULL,
    enable_holiday_scheduling boolean DEFAULT false NOT NULL,
    default_block_duration_hours integer DEFAULT 4 NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    freeze_horizon_days integer DEFAULT 7 NOT NULL,
    freeze_scope character varying(50) DEFAULT 'none'::character varying NOT NULL,
    alembic_version character varying(255),
    schema_timestamp timestamp without time zone,
    CONSTRAINT check_block_duration CHECK (((default_block_duration_hours >= 1) AND (default_block_duration_hours <= 12))),
    CONSTRAINT check_consecutive_days CHECK (((max_consecutive_days >= 1) AND (max_consecutive_days <= 7))),
    CONSTRAINT check_days_off CHECK (((min_days_off_per_week >= 1) AND (min_days_off_per_week <= 3))),
    CONSTRAINT check_freeze_horizon CHECK (((freeze_horizon_days >= 0) AND (freeze_horizon_days <= 30))),
    CONSTRAINT check_freeze_scope CHECK (((freeze_scope)::text = ANY (ARRAY[('none'::character varying)::text, ('non_emergency_only'::character varying)::text, ('all_changes_require_override'::character varying)::text]))),
    CONSTRAINT check_scheduling_algorithm CHECK (((scheduling_algorithm)::text = ANY (ARRAY[('greedy'::character varying)::text, ('min_conflicts'::character varying)::text, ('cp_sat'::character varying)::text, ('pulp'::character varying)::text, ('hybrid'::character varying)::text]))),
    CONSTRAINT check_work_hours CHECK (((work_hours_per_week >= 40) AND (work_hours_per_week <= 100)))
);


ALTER TABLE public.application_settings OWNER TO scheduler;

--
-- Name: approval_record; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.approval_record (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    chain_id character varying(100) NOT NULL,
    sequence_num integer NOT NULL,
    prev_record_id uuid,
    prev_hash character varying(64),
    record_hash character varying(64) NOT NULL,
    action character varying(50) NOT NULL,
    payload jsonb DEFAULT '{}'::jsonb NOT NULL,
    actor_id uuid,
    actor_type character varying(20) DEFAULT 'human'::character varying NOT NULL,
    reason text,
    target_entity_type character varying(50),
    target_entity_id character varying(100),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    ip_address character varying(45),
    user_agent character varying(500)
);


ALTER TABLE public.approval_record OWNER TO scheduler;

--
-- Name: assignments; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.assignments (
    id uuid NOT NULL,
    block_id uuid NOT NULL,
    person_id uuid NOT NULL,
    rotation_template_id uuid,
    role character varying(50) NOT NULL,
    activity_override character varying(255),
    notes text,
    created_by character varying(255),
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    override_reason text,
    override_acknowledged_at timestamp without time zone,
    explain_json jsonb,
    confidence double precision,
    score double precision,
    alternatives_json jsonb,
    audit_hash character varying(64),
    schedule_run_id uuid,
    CONSTRAINT check_role CHECK (((role)::text = ANY (ARRAY[('primary'::character varying)::text, ('supervising'::character varying)::text, ('backup'::character varying)::text])))
);


ALTER TABLE public.assignments OWNER TO scheduler;

--
-- Name: assignments_version; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.assignments_version (
    id uuid NOT NULL,
    block_id uuid,
    person_id uuid,
    rotation_template_id uuid,
    role character varying(50),
    activity_override character varying(255),
    notes text,
    override_reason text,
    override_acknowledged_at timestamp without time zone,
    explain_json jsonb,
    confidence double precision,
    score double precision,
    alternatives_json jsonb,
    audit_hash character varying(64),
    created_by character varying(255),
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    transaction_id bigint NOT NULL,
    operation_type smallint NOT NULL,
    end_transaction_id bigint,
    block_id_mod boolean,
    person_id_mod boolean,
    rotation_template_id_mod boolean,
    role_mod boolean,
    activity_override_mod boolean,
    notes_mod boolean,
    override_reason_mod boolean,
    override_acknowledged_at_mod boolean,
    explain_json_mod boolean,
    confidence_mod boolean,
    score_mod boolean,
    alternatives_json_mod boolean,
    audit_hash_mod boolean,
    created_by_mod boolean,
    created_at_mod boolean,
    updated_at_mod boolean,
    schedule_run_id uuid,
    schedule_run_id_mod boolean
);


ALTER TABLE public.assignments_version OWNER TO scheduler;

--
-- Name: block_assignments; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.block_assignments (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    block_number integer NOT NULL,
    academic_year integer NOT NULL,
    resident_id uuid NOT NULL,
    rotation_template_id uuid,
    has_leave boolean DEFAULT false NOT NULL,
    leave_days integer DEFAULT 0 NOT NULL,
    assignment_reason character varying(50) DEFAULT 'balanced'::character varying NOT NULL,
    notes text,
    created_by character varying(255),
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    secondary_rotation_template_id uuid,
    CONSTRAINT check_assignment_reason CHECK (((assignment_reason)::text = ANY (ARRAY[('leave_eligible_match'::character varying)::text, ('coverage_priority'::character varying)::text, ('balanced'::character varying)::text, ('manual'::character varying)::text, ('specialty_match'::character varying)::text]))),
    CONSTRAINT check_block_number_range CHECK (((block_number >= 0) AND (block_number <= 13))),
    CONSTRAINT check_leave_days_positive CHECK ((leave_days >= 0))
);


ALTER TABLE public.block_assignments OWNER TO scheduler;

--
-- Name: COLUMN block_assignments.block_number; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.block_assignments.block_number IS 'Academic block number (0-13, where 0 is orientation)';


--
-- Name: COLUMN block_assignments.academic_year; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.block_assignments.academic_year IS 'Academic year starting July 1 (e.g., 2025)';


--
-- Name: COLUMN block_assignments.has_leave; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.block_assignments.has_leave IS 'Does resident have approved leave during this block?';


--
-- Name: COLUMN block_assignments.leave_days; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.block_assignments.leave_days IS 'Number of leave days in this block';


--
-- Name: COLUMN block_assignments.assignment_reason; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.block_assignments.assignment_reason IS 'leave_eligible_match, coverage_priority, balanced, manual, specialty_match';


--
-- Name: blocks; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.blocks (
    id uuid NOT NULL,
    date date NOT NULL,
    time_of_day character varying(2) NOT NULL,
    block_number integer NOT NULL,
    is_weekend boolean,
    is_holiday boolean,
    holiday_name character varying(255),
    day_type character varying(50),
    operational_intent public.operationalintent DEFAULT 'NORMAL'::public.operationalintent,
    actual_date date,
    CONSTRAINT check_time_of_day CHECK (((time_of_day)::text = ANY (ARRAY[('AM'::character varying)::text, ('PM'::character varying)::text])))
);


ALTER TABLE public.blocks OWNER TO scheduler;

--
-- Name: call_assignments; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.call_assignments (
    id uuid NOT NULL,
    date date NOT NULL,
    person_id uuid NOT NULL,
    call_type character varying(50) NOT NULL,
    is_weekend boolean,
    is_holiday boolean,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT check_call_type CHECK (((call_type)::text = ANY (ARRAY[('overnight'::character varying)::text, ('weekend'::character varying)::text, ('backup'::character varying)::text])))
);


ALTER TABLE public.call_assignments OWNER TO scheduler;

--
-- Name: certification_types; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.certification_types (
    id uuid NOT NULL,
    name character varying(100) NOT NULL,
    full_name character varying(255),
    description text,
    renewal_period_months integer DEFAULT 24,
    required_for_residents boolean DEFAULT true,
    required_for_faculty boolean DEFAULT true,
    required_for_specialties character varying(500),
    reminder_days_180 boolean DEFAULT true,
    reminder_days_90 boolean DEFAULT true,
    reminder_days_30 boolean DEFAULT true,
    reminder_days_14 boolean DEFAULT true,
    reminder_days_7 boolean DEFAULT true,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.certification_types OWNER TO scheduler;

--
-- Name: chaos_experiments; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.chaos_experiments (
    id uuid NOT NULL,
    name character varying(200) NOT NULL,
    description character varying(1000),
    injector_type character varying(50) NOT NULL,
    blast_radius double precision DEFAULT '0.1'::double precision NOT NULL,
    blast_radius_scope character varying(50) NOT NULL,
    target_component character varying(200),
    target_zone_id uuid,
    target_user_id uuid,
    status character varying(50) DEFAULT 'pending'::character varying NOT NULL,
    scheduled_at timestamp without time zone DEFAULT now() NOT NULL,
    started_at timestamp without time zone,
    ended_at timestamp without time zone,
    max_duration_minutes integer DEFAULT 15 NOT NULL,
    auto_rollback boolean DEFAULT true NOT NULL,
    slo_thresholds jsonb,
    total_injections integer DEFAULT 0 NOT NULL,
    successful_injections integer DEFAULT 0 NOT NULL,
    failed_injections integer DEFAULT 0 NOT NULL,
    slo_breaches jsonb,
    rollback_reason character varying(500),
    injector_params jsonb,
    observations jsonb,
    metrics_snapshot jsonb,
    metadata jsonb,
    created_by character varying(100),
    approved_by character varying(100)
);


ALTER TABLE public.chaos_experiments OWNER TO scheduler;

--
-- Name: clinic_sessions; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.clinic_sessions (
    id character varying(36) NOT NULL,
    date date NOT NULL,
    session_type character varying(2) NOT NULL,
    clinic_type character varying(50) NOT NULL,
    physician_count integer DEFAULT 0 NOT NULL,
    screener_count integer DEFAULT 0 NOT NULL,
    screener_ratio double precision,
    staffing_status character varying(20) NOT NULL,
    rn_fallback_used boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_clinic_type CHECK (((clinic_type)::text = ANY (ARRAY[('family_medicine'::character varying)::text, ('sports_medicine'::character varying)::text, ('pediatrics'::character varying)::text, ('procedures'::character varying)::text]))),
    CONSTRAINT check_physician_count CHECK ((physician_count >= 0)),
    CONSTRAINT check_screener_count CHECK ((screener_count >= 0)),
    CONSTRAINT check_screener_ratio CHECK (((screener_ratio IS NULL) OR (screener_ratio >= (0)::double precision))),
    CONSTRAINT check_session_type CHECK (((session_type)::text = ANY (ARRAY[('am'::character varying)::text, ('pm'::character varying)::text]))),
    CONSTRAINT check_staffing_status CHECK (((staffing_status)::text = ANY (ARRAY[('optimal'::character varying)::text, ('adequate'::character varying)::text, ('suboptimal'::character varying)::text, ('inadequate'::character varying)::text, ('unstaffed'::character varying)::text])))
);


ALTER TABLE public.clinic_sessions OWNER TO scheduler;

--
-- Name: cognitive_decisions; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.cognitive_decisions (
    id uuid NOT NULL,
    session_id uuid,
    category character varying(50) NOT NULL,
    complexity character varying(50) NOT NULL,
    description text NOT NULL,
    options jsonb,
    recommended_option character varying(255),
    safe_default character varying(255),
    has_safe_default boolean,
    is_urgent boolean,
    can_defer boolean,
    deadline timestamp with time zone,
    context jsonb,
    created_at timestamp with time zone DEFAULT now(),
    outcome character varying(50),
    chosen_option character varying(255),
    decided_at timestamp with time zone,
    decided_by character varying(255),
    estimated_cognitive_cost double precision NOT NULL,
    actual_time_seconds double precision
);


ALTER TABLE public.cognitive_decisions OWNER TO scheduler;

--
-- Name: cognitive_sessions; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.cognitive_sessions (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    started_at timestamp with time zone NOT NULL,
    ended_at timestamp with time zone,
    max_decisions_before_break integer NOT NULL,
    total_cognitive_cost double precision NOT NULL,
    decisions_count integer NOT NULL,
    breaks_taken integer NOT NULL,
    final_state character varying(50),
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.cognitive_sessions OWNER TO scheduler;

--
-- Name: compensation_records; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.compensation_records (
    id uuid NOT NULL,
    stress_id uuid NOT NULL,
    compensation_type character varying(50) NOT NULL,
    description character varying(500),
    initiated_at timestamp without time zone DEFAULT now() NOT NULL,
    compensation_magnitude double precision NOT NULL,
    effectiveness double precision,
    immediate_cost double precision,
    hidden_cost double precision,
    sustainability_days integer,
    is_active boolean,
    ended_at timestamp without time zone,
    end_reason character varying(200),
    CONSTRAINT check_compensation_type CHECK (((compensation_type)::text = ANY (ARRAY[('overtime'::character varying)::text, ('cross_coverage'::character varying)::text, ('deferred_leave'::character varying)::text, ('service_reduction'::character varying)::text, ('efficiency_gain'::character varying)::text, ('backup_activation'::character varying)::text, ('quality_trade'::character varying)::text])))
);


ALTER TABLE public.compensation_records OWNER TO scheduler;

--
-- Name: conflict_alerts; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.conflict_alerts (
    id uuid NOT NULL,
    faculty_id uuid NOT NULL,
    conflict_type character varying(50) NOT NULL,
    severity character varying(20) DEFAULT 'warning'::character varying NOT NULL,
    fmit_week date NOT NULL,
    leave_id uuid,
    swap_id uuid,
    status character varying(20) DEFAULT 'new'::character varying NOT NULL,
    description text NOT NULL,
    resolution_notes text,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    acknowledged_at timestamp without time zone,
    acknowledged_by_id uuid,
    resolved_at timestamp without time zone,
    resolved_by_id uuid
);


ALTER TABLE public.conflict_alerts OWNER TO scheduler;

--
-- Name: cross_training_recommendations; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.cross_training_recommendations (
    id uuid NOT NULL,
    skill character varying(255) NOT NULL,
    current_holders uuid[],
    recommended_trainees uuid[],
    priority character varying(50) NOT NULL,
    reason text NOT NULL,
    estimated_training_hours integer NOT NULL,
    risk_reduction double precision NOT NULL,
    status character varying(50) NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    approved_by character varying(255)
);


ALTER TABLE public.cross_training_recommendations OWNER TO scheduler;

--
-- Name: email_logs; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.email_logs (
    id uuid NOT NULL,
    notification_id uuid,
    recipient_email character varying(255) NOT NULL,
    subject character varying(500) NOT NULL,
    body_html text,
    body_text text,
    status public.emailstatus DEFAULT 'queued'::public.emailstatus NOT NULL,
    error_message text,
    sent_at timestamp without time zone,
    retry_count integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    template_id uuid
);


ALTER TABLE public.email_logs OWNER TO scheduler;

--
-- Name: email_templates; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.email_templates (
    id uuid NOT NULL,
    name character varying(100) NOT NULL,
    template_type public.emailtemplatetype NOT NULL,
    subject_template character varying(500) NOT NULL,
    body_html_template text NOT NULL,
    body_text_template text NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_by_id uuid,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.email_templates OWNER TO scheduler;

--
-- Name: equilibrium_shifts; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.equilibrium_shifts (
    id uuid NOT NULL,
    calculated_at timestamp without time zone DEFAULT now() NOT NULL,
    original_capacity double precision NOT NULL,
    original_demand double precision NOT NULL,
    original_coverage_rate double precision NOT NULL,
    stress_types character varying[],
    total_capacity_impact double precision,
    total_demand_impact double precision,
    compensation_types character varying[],
    total_compensation double precision,
    compensation_efficiency double precision,
    new_capacity double precision NOT NULL,
    new_demand double precision NOT NULL,
    new_coverage_rate double precision NOT NULL,
    sustainable_capacity double precision,
    compensation_debt double precision,
    daily_debt_rate double precision,
    burnout_risk double precision,
    days_until_exhaustion integer,
    equilibrium_state character varying(30),
    is_sustainable boolean,
    CONSTRAINT check_equilibrium_state CHECK (((equilibrium_state IS NULL) OR ((equilibrium_state)::text = ANY (ARRAY[('stable'::character varying)::text, ('compensating'::character varying)::text, ('stressed'::character varying)::text, ('unsustainable'::character varying)::text, ('critical'::character varying)::text]))))
);


ALTER TABLE public.equilibrium_shifts OWNER TO scheduler;

--
-- Name: faculty_activity_permissions; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.faculty_activity_permissions (
    id uuid NOT NULL,
    faculty_role character varying(20) NOT NULL,
    activity_id uuid NOT NULL,
    is_default boolean DEFAULT false NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.faculty_activity_permissions OWNER TO scheduler;

--
-- Name: COLUMN faculty_activity_permissions.faculty_role; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.faculty_activity_permissions.faculty_role IS 'FacultyRole enum value (pd, apd, oic, dept_chief, sports_med, core, adjunct)';


--
-- Name: COLUMN faculty_activity_permissions.is_default; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.faculty_activity_permissions.is_default IS 'Auto-assign this activity to new templates for this role';


--
-- Name: faculty_centrality; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.faculty_centrality (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    faculty_id uuid NOT NULL,
    faculty_name character varying(255) NOT NULL,
    calculated_at timestamp with time zone DEFAULT now(),
    degree_centrality double precision NOT NULL,
    betweenness_centrality double precision NOT NULL,
    eigenvector_centrality double precision NOT NULL,
    pagerank double precision NOT NULL,
    composite_score double precision NOT NULL,
    services_covered integer NOT NULL,
    unique_services integer NOT NULL,
    total_assignments integer NOT NULL,
    replacement_difficulty double precision NOT NULL,
    risk_level character varying(50) NOT NULL,
    is_hub boolean NOT NULL
);


ALTER TABLE public.faculty_centrality OWNER TO scheduler;

--
-- Name: faculty_preferences; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.faculty_preferences (
    id uuid NOT NULL,
    faculty_id uuid NOT NULL,
    preferred_weeks json,
    blocked_weeks json,
    max_weeks_per_month integer DEFAULT 2,
    max_consecutive_weeks integer DEFAULT 1,
    min_gap_between_weeks integer DEFAULT 2,
    target_weeks_per_year integer DEFAULT 6,
    notify_swap_requests boolean DEFAULT true,
    notify_schedule_changes boolean DEFAULT true,
    notify_conflict_alerts boolean DEFAULT true,
    notify_reminder_days integer DEFAULT 7,
    preferred_contact_method text DEFAULT '''email'''::text,
    notes text,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.faculty_preferences OWNER TO scheduler;

--
-- Name: faculty_weekly_overrides; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.faculty_weekly_overrides (
    id uuid NOT NULL,
    person_id uuid NOT NULL,
    effective_date date NOT NULL,
    day_of_week integer NOT NULL,
    time_of_day character varying(2) NOT NULL,
    activity_id uuid,
    is_locked boolean DEFAULT false NOT NULL,
    override_reason text,
    created_by uuid,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.faculty_weekly_overrides OWNER TO scheduler;

--
-- Name: COLUMN faculty_weekly_overrides.effective_date; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.faculty_weekly_overrides.effective_date IS 'Week start date (Monday) for this override';


--
-- Name: COLUMN faculty_weekly_overrides.day_of_week; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.faculty_weekly_overrides.day_of_week IS '0=Sunday, 6=Saturday';


--
-- Name: COLUMN faculty_weekly_overrides.time_of_day; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.faculty_weekly_overrides.time_of_day IS 'AM or PM';


--
-- Name: COLUMN faculty_weekly_overrides.activity_id; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.faculty_weekly_overrides.activity_id IS 'Activity for this override (NULL = clear slot)';


--
-- Name: COLUMN faculty_weekly_overrides.is_locked; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.faculty_weekly_overrides.is_locked IS 'HARD constraint for this specific week';


--
-- Name: COLUMN faculty_weekly_overrides.override_reason; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.faculty_weekly_overrides.override_reason IS 'Why this override was created';


--
-- Name: COLUMN faculty_weekly_overrides.created_by; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.faculty_weekly_overrides.created_by IS 'Who created this override';


--
-- Name: faculty_weekly_templates; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.faculty_weekly_templates (
    id uuid NOT NULL,
    person_id uuid NOT NULL,
    day_of_week integer NOT NULL,
    time_of_day character varying(2) NOT NULL,
    week_number integer,
    activity_id uuid,
    is_locked boolean DEFAULT false NOT NULL,
    priority integer DEFAULT 50 NOT NULL,
    notes text,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.faculty_weekly_templates OWNER TO scheduler;

--
-- Name: COLUMN faculty_weekly_templates.day_of_week; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.faculty_weekly_templates.day_of_week IS '0=Sunday, 6=Saturday';


--
-- Name: COLUMN faculty_weekly_templates.time_of_day; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.faculty_weekly_templates.time_of_day IS 'AM or PM';


--
-- Name: COLUMN faculty_weekly_templates.week_number; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.faculty_weekly_templates.week_number IS 'Week 1-4 within block. NULL = same pattern all weeks';


--
-- Name: COLUMN faculty_weekly_templates.activity_id; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.faculty_weekly_templates.activity_id IS 'Activity assigned to this slot (NULL = unassigned)';


--
-- Name: COLUMN faculty_weekly_templates.is_locked; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.faculty_weekly_templates.is_locked IS 'HARD constraint - solver cannot change';


--
-- Name: COLUMN faculty_weekly_templates.priority; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.faculty_weekly_templates.priority IS 'Soft preference 0-100 (higher = more important)';


--
-- Name: fallback_activations; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.fallback_activations (
    id uuid NOT NULL,
    activated_at timestamp without time zone DEFAULT now() NOT NULL,
    scenario character varying(50) NOT NULL,
    scenario_description character varying(500),
    activated_by character varying(100),
    activation_reason character varying(500),
    assignments_count integer,
    coverage_rate double precision,
    services_reduced character varying[],
    assumptions character varying[],
    deactivated_at timestamp without time zone,
    deactivated_by character varying(100),
    deactivation_reason character varying(500),
    related_event_id uuid,
    CONSTRAINT check_fallback_scenario CHECK (((scenario)::text = ANY (ARRAY[('single_faculty_loss'::character varying)::text, ('double_faculty_loss'::character varying)::text, ('pcs_season_50_percent'::character varying)::text, ('holiday_skeleton'::character varying)::text, ('pandemic_essential'::character varying)::text, ('mass_casualty'::character varying)::text, ('weather_emergency'::character varying)::text])))
);


ALTER TABLE public.fallback_activations OWNER TO scheduler;

--
-- Name: feature_flag_audit; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.feature_flag_audit (
    id uuid NOT NULL,
    flag_id uuid NOT NULL,
    user_id uuid,
    username character varying(100),
    action character varying(50) NOT NULL,
    changes json,
    reason text,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT check_audit_action CHECK (((action)::text = ANY ((ARRAY['created'::character varying, 'updated'::character varying, 'deleted'::character varying, 'enabled'::character varying, 'disabled'::character varying])::text[])))
);


ALTER TABLE public.feature_flag_audit OWNER TO scheduler;

--
-- Name: feature_flag_evaluations; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.feature_flag_evaluations (
    id uuid NOT NULL,
    flag_id uuid NOT NULL,
    user_id uuid,
    user_role character varying(50),
    enabled boolean NOT NULL,
    variant character varying(50),
    environment character varying(50),
    rollout_percentage double precision,
    context json,
    evaluated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.feature_flag_evaluations OWNER TO scheduler;

--
-- Name: feature_flags; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.feature_flags (
    id uuid NOT NULL,
    key character varying(100) NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    flag_type character varying(20) DEFAULT 'boolean'::character varying NOT NULL,
    enabled boolean DEFAULT false NOT NULL,
    rollout_percentage double precision,
    environments json,
    target_user_ids json,
    target_roles json,
    variants json,
    dependencies json,
    custom_attributes json,
    created_by uuid,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT check_flag_type CHECK (((flag_type)::text = ANY ((ARRAY['boolean'::character varying, 'percentage'::character varying, 'variant'::character varying])::text[]))),
    CONSTRAINT check_rollout_percentage_range CHECK (((rollout_percentage IS NULL) OR ((rollout_percentage >= (0.0)::double precision) AND (rollout_percentage <= (1.0)::double precision))))
);


ALTER TABLE public.feature_flags OWNER TO scheduler;

--
-- Name: feedback_loop_states; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.feedback_loop_states (
    id uuid NOT NULL,
    loop_name character varying(100) NOT NULL,
    setpoint_name character varying(100) NOT NULL,
    "timestamp" timestamp without time zone DEFAULT now() NOT NULL,
    target_value double precision NOT NULL,
    tolerance double precision NOT NULL,
    is_critical boolean,
    current_value double precision,
    deviation double precision,
    deviation_severity character varying(20),
    consecutive_deviations integer,
    trend_direction character varying(20),
    is_improving boolean,
    correction_triggered boolean,
    correction_type character varying(50),
    correction_effective boolean,
    CONSTRAINT check_deviation_severity CHECK (((deviation_severity IS NULL) OR ((deviation_severity)::text = ANY (ARRAY[('none'::character varying)::text, ('minor'::character varying)::text, ('moderate'::character varying)::text, ('major'::character varying)::text, ('critical'::character varying)::text]))))
);


ALTER TABLE public.feedback_loop_states OWNER TO scheduler;

--
-- Name: half_day_assignments; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.half_day_assignments (
    id uuid NOT NULL,
    person_id uuid NOT NULL,
    date date NOT NULL,
    time_of_day character varying(2) NOT NULL,
    activity_id uuid,
    source character varying(20) NOT NULL,
    block_assignment_id uuid,
    is_override boolean NOT NULL,
    override_reason text,
    overridden_by uuid,
    overridden_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT check_half_day_source CHECK (((source)::text = ANY ((ARRAY['preload'::character varying, 'manual'::character varying, 'solver'::character varying, 'template'::character varying])::text[]))),
    CONSTRAINT check_half_day_time_of_day CHECK (((time_of_day)::text = ANY ((ARRAY['AM'::character varying, 'PM'::character varying])::text[])))
);


ALTER TABLE public.half_day_assignments OWNER TO scheduler;

--
-- Name: hub_protection_plans; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.hub_protection_plans (
    id uuid NOT NULL,
    hub_faculty_id uuid NOT NULL,
    hub_faculty_name character varying(255) NOT NULL,
    period_start date NOT NULL,
    period_end date NOT NULL,
    reason text NOT NULL,
    workload_reduction double precision NOT NULL,
    backup_assigned boolean NOT NULL,
    backup_faculty_ids uuid[],
    critical_only boolean NOT NULL,
    status character varying(50) NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    activated_at timestamp with time zone,
    deactivated_at timestamp with time zone,
    created_by character varying(255)
);


ALTER TABLE public.hub_protection_plans OWNER TO scheduler;

--
-- Name: idempotency_requests; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.idempotency_requests (
    id uuid NOT NULL,
    idempotency_key character varying(255) NOT NULL,
    body_hash character varying(64) NOT NULL,
    request_params jsonb,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    result_ref uuid,
    error_message text,
    response_body jsonb,
    response_status_code character varying(3),
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    completed_at timestamp without time zone,
    expires_at timestamp without time zone NOT NULL
);


ALTER TABLE public.idempotency_requests OWNER TO scheduler;

--
-- Name: import_batches; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.import_batches (
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    created_by_id uuid,
    filename character varying(255),
    file_hash character varying(64),
    file_size_bytes integer,
    status public.importbatchstatus DEFAULT 'staged'::public.importbatchstatus NOT NULL,
    conflict_resolution public.conflictresolutionmode DEFAULT 'upsert'::public.conflictresolutionmode NOT NULL,
    target_block integer,
    target_start_date date,
    target_end_date date,
    notes text,
    row_count integer,
    error_count integer DEFAULT 0,
    warning_count integer DEFAULT 0,
    applied_at timestamp without time zone,
    applied_by_id uuid,
    rollback_available boolean DEFAULT true,
    rollback_expires_at timestamp without time zone,
    rolled_back_at timestamp without time zone,
    rolled_back_by_id uuid
);


ALTER TABLE public.import_batches OWNER TO scheduler;

--
-- Name: import_staged_absences; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.import_staged_absences (
    id uuid NOT NULL,
    batch_id uuid NOT NULL,
    row_number integer,
    sheet_name character varying(100),
    person_name character varying(255) NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    absence_type character varying(50) NOT NULL,
    raw_cell_value character varying(500),
    notes text,
    is_blocking boolean,
    return_date_tentative boolean DEFAULT false,
    tdy_location character varying(255),
    replacement_activity character varying(255),
    matched_person_id uuid,
    person_match_confidence integer,
    overlap_type public.overlaptype DEFAULT 'none'::public.overlaptype NOT NULL,
    overlapping_absence_ids jsonb,
    overlap_details jsonb,
    status public.stagedabsencestatus DEFAULT 'pending'::public.stagedabsencestatus NOT NULL,
    validation_errors jsonb,
    validation_warnings jsonb,
    created_absence_id uuid,
    merged_into_absence_id uuid,
    CONSTRAINT check_staged_absence_dates CHECK ((end_date >= start_date)),
    CONSTRAINT check_staged_absence_type CHECK (((absence_type)::text = ANY (ARRAY[('vacation'::character varying)::text, ('deployment'::character varying)::text, ('tdy'::character varying)::text, ('medical'::character varying)::text, ('family_emergency'::character varying)::text, ('conference'::character varying)::text, ('bereavement'::character varying)::text, ('emergency_leave'::character varying)::text, ('sick'::character varying)::text, ('convalescent'::character varying)::text, ('maternity_paternity'::character varying)::text])))
);


ALTER TABLE public.import_staged_absences OWNER TO scheduler;

--
-- Name: import_staged_absences_version; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.import_staged_absences_version (
    id uuid NOT NULL,
    batch_id uuid,
    row_number integer,
    sheet_name character varying(100),
    person_name character varying(255),
    start_date date,
    end_date date,
    absence_type character varying(50),
    raw_cell_value character varying(500),
    notes text,
    is_blocking boolean,
    return_date_tentative boolean,
    tdy_location character varying(255),
    replacement_activity character varying(255),
    matched_person_id uuid,
    person_match_confidence integer,
    overlap_type character varying(20),
    overlapping_absence_ids jsonb,
    overlap_details jsonb,
    status character varying(20),
    validation_errors jsonb,
    validation_warnings jsonb,
    created_absence_id uuid,
    merged_into_absence_id uuid,
    transaction_id bigint NOT NULL,
    operation_type smallint NOT NULL,
    end_transaction_id bigint
);


ALTER TABLE public.import_staged_absences_version OWNER TO scheduler;

--
-- Name: import_staged_assignments; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.import_staged_assignments (
    id uuid NOT NULL,
    batch_id uuid NOT NULL,
    row_number integer,
    sheet_name character varying(100),
    person_name character varying(255) NOT NULL,
    assignment_date date NOT NULL,
    slot character varying(10),
    rotation_name character varying(255),
    raw_cell_value character varying(500),
    matched_person_id uuid,
    person_match_confidence integer,
    matched_rotation_id uuid,
    rotation_match_confidence integer,
    conflict_type character varying(50),
    existing_assignment_id uuid,
    status public.stagedassignmentstatus DEFAULT 'pending'::public.stagedassignmentstatus NOT NULL,
    validation_errors jsonb,
    validation_warnings jsonb,
    created_assignment_id uuid
);


ALTER TABLE public.import_staged_assignments OWNER TO scheduler;

--
-- Name: inpatient_preloads; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.inpatient_preloads (
    id uuid NOT NULL,
    person_id uuid NOT NULL,
    rotation_type character varying(20) NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    fmit_week_number integer,
    includes_post_call boolean NOT NULL,
    assigned_by character varying(20),
    notes character varying(500),
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    is_tdy boolean DEFAULT false,
    tdy_location character varying(100),
    CONSTRAINT check_fmit_week_number CHECK (((fmit_week_number IS NULL) OR ((fmit_week_number >= 1) AND (fmit_week_number <= 4)))),
    CONSTRAINT check_inpatient_rotation_type CHECK (((rotation_type)::text = ANY ((ARRAY['FMIT'::character varying, 'NF'::character varying, 'PedW'::character varying, 'PedNF'::character varying, 'KAP'::character varying, 'IM'::character varying, 'LDNF'::character varying, 'FMC'::character varying, 'HILO'::character varying, 'OKIN'::character varying])::text[]))),
    CONSTRAINT check_preload_assigned_by CHECK (((assigned_by IS NULL) OR ((assigned_by)::text = ANY ((ARRAY['chief'::character varying, 'scheduler'::character varying, 'coordinator'::character varying, 'manual'::character varying])::text[])))),
    CONSTRAINT check_preload_dates CHECK ((end_date >= start_date))
);


ALTER TABLE public.inpatient_preloads OWNER TO scheduler;

--
-- Name: intern_stagger_patterns; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.intern_stagger_patterns (
    id character varying(36) NOT NULL,
    name character varying(255) NOT NULL,
    intern_a_start time without time zone NOT NULL,
    intern_b_start time without time zone NOT NULL,
    overlap_duration_minutes integer NOT NULL,
    overlap_efficiency integer DEFAULT 85 NOT NULL,
    min_intern_a_experience_weeks integer DEFAULT 2 NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_min_experience CHECK ((min_intern_a_experience_weeks >= 0)),
    CONSTRAINT check_overlap_duration CHECK ((overlap_duration_minutes > 0)),
    CONSTRAINT check_overlap_efficiency CHECK (((overlap_efficiency >= 0) AND (overlap_efficiency <= 100)))
);


ALTER TABLE public.intern_stagger_patterns OWNER TO scheduler;

--
-- Name: ip_blacklists; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.ip_blacklists (
    id uuid NOT NULL,
    ip_address character varying(45) NOT NULL,
    reason character varying(500) NOT NULL,
    added_by_id uuid,
    detection_method character varying(100),
    incident_count integer DEFAULT 1 NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    expires_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    last_hit_at timestamp without time zone
);


ALTER TABLE public.ip_blacklists OWNER TO scheduler;

--
-- Name: ip_whitelists; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.ip_whitelists (
    id uuid NOT NULL,
    ip_address character varying(45) NOT NULL,
    description character varying(500),
    owner_id uuid,
    applies_to character varying(50) DEFAULT 'all'::character varying NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    expires_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.ip_whitelists OWNER TO scheduler;

--
-- Name: job_executions; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.job_executions (
    id uuid NOT NULL,
    job_id uuid NOT NULL,
    job_name character varying(255) NOT NULL,
    started_at timestamp without time zone NOT NULL,
    finished_at timestamp without time zone,
    status character varying(50) NOT NULL,
    result jsonb,
    error text,
    traceback text,
    runtime_seconds integer,
    scheduled_run_time timestamp without time zone NOT NULL
);


ALTER TABLE public.job_executions OWNER TO scheduler;

--
-- Name: metric_snapshots; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.metric_snapshots (
    id uuid NOT NULL,
    schedule_version_id uuid NOT NULL,
    category character varying(20) NOT NULL,
    metric_name character varying(50) NOT NULL,
    value double precision NOT NULL,
    computed_at timestamp without time zone DEFAULT now(),
    methodology_version character varying(20) DEFAULT '''1.0'''::character varying,
    CONSTRAINT check_metric_category CHECK (((category)::text = ANY (ARRAY[('fairness'::character varying)::text, ('satisfaction'::character varying)::text, ('stability'::character varying)::text, ('compliance'::character varying)::text, ('resilience'::character varying)::text])))
);


ALTER TABLE public.metric_snapshots OWNER TO scheduler;

--
-- Name: model_tiers; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.model_tiers (
    agent_name character varying NOT NULL,
    default_model character varying NOT NULL,
    updated_at timestamp without time zone DEFAULT now(),
    notes text
);


ALTER TABLE public.model_tiers OWNER TO scheduler;

--
-- Name: COLUMN model_tiers.default_model; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.model_tiers.default_model IS 'Model tier: haiku, sonnet, opus';


--
-- Name: COLUMN model_tiers.notes; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.model_tiers.notes IS 'Optional notes about tier selection';


--
-- Name: notification_preferences; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.notification_preferences (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    enabled_channels character varying(200) DEFAULT '''in_app,email'''::character varying,
    notification_types jsonb DEFAULT '{}'::jsonb,
    quiet_hours_start integer,
    quiet_hours_end integer,
    email_digest_enabled boolean DEFAULT false,
    email_digest_frequency character varying(20) DEFAULT '''daily'''::character varying,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT check_digest_frequency CHECK (((email_digest_frequency)::text = ANY (ARRAY[('daily'::character varying)::text, ('weekly'::character varying)::text]))),
    CONSTRAINT check_quiet_end CHECK (((quiet_hours_end IS NULL) OR ((quiet_hours_end >= 0) AND (quiet_hours_end <= 23)))),
    CONSTRAINT check_quiet_start CHECK (((quiet_hours_start IS NULL) OR ((quiet_hours_start >= 0) AND (quiet_hours_start <= 23))))
);


ALTER TABLE public.notification_preferences OWNER TO scheduler;

--
-- Name: notifications; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.notifications (
    id uuid NOT NULL,
    recipient_id uuid NOT NULL,
    notification_type character varying(50) NOT NULL,
    subject character varying(500) NOT NULL,
    body text NOT NULL,
    data jsonb DEFAULT '{}'::jsonb,
    priority character varying(20) DEFAULT '''normal'''::character varying,
    channels_delivered character varying(200),
    is_read boolean DEFAULT false,
    read_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT check_notification_priority CHECK (((priority)::text = ANY (ARRAY[('high'::character varying)::text, ('normal'::character varying)::text, ('low'::character varying)::text])))
);


ALTER TABLE public.notifications OWNER TO scheduler;

--
-- Name: oauth2_clients; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.oauth2_clients (
    id uuid NOT NULL,
    client_id character varying(255) NOT NULL,
    client_secret_hash character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    scopes text DEFAULT 'read'::text NOT NULL,
    grant_types character varying(255) DEFAULT 'client_credentials'::character varying NOT NULL,
    owner_id uuid,
    is_active boolean DEFAULT true NOT NULL,
    is_confidential boolean DEFAULT true NOT NULL,
    rate_limit_per_minute integer DEFAULT 100,
    rate_limit_per_hour integer DEFAULT 5000,
    access_token_lifetime_seconds integer DEFAULT 3600 NOT NULL,
    last_used_at timestamp without time zone,
    total_tokens_issued integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.oauth2_clients OWNER TO scheduler;

--
-- Name: people; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.people (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    type character varying(50) NOT NULL,
    email character varying(255),
    pgy_level integer,
    performs_procedures boolean,
    specialties character varying[],
    primary_duty character varying(255),
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    target_clinical_blocks integer,
    faculty_role character varying(50),
    sunday_call_count integer DEFAULT 0,
    weekday_call_count integer DEFAULT 0,
    fmit_weeks_count integer DEFAULT 0,
    screener_role character varying(50),
    can_screen boolean DEFAULT false,
    screening_efficiency integer DEFAULT 100,
    clinic_min integer,
    clinic_max integer,
    at_min integer,
    at_max integer,
    gme_min integer,
    gme_max integer,
    dfm_min integer,
    dfm_max integer,
    admin_type character varying(10),
    is_sm_faculty boolean DEFAULT false,
    has_split_admin boolean DEFAULT false,
    sm_min integer,
    sm_max integer,
    min_clinic_halfdays_per_week integer,
    max_clinic_halfdays_per_week integer,
    CONSTRAINT check_faculty_role CHECK (((faculty_role IS NULL) OR ((faculty_role)::text = ANY ((ARRAY['pd'::character varying, 'apd'::character varying, 'oic'::character varying, 'dept_chief'::character varying, 'sports_med'::character varying, 'core'::character varying, 'adjunct'::character varying])::text[])))),
    CONSTRAINT check_person_type CHECK (((type)::text = ANY (ARRAY[('resident'::character varying)::text, ('faculty'::character varying)::text]))),
    CONSTRAINT check_pgy_level CHECK (((pgy_level IS NULL) OR ((pgy_level >= 1) AND (pgy_level <= 3)))),
    CONSTRAINT check_screener_role CHECK (((screener_role IS NULL) OR ((screener_role)::text = ANY (ARRAY[('dedicated'::character varying)::text, ('rn'::character varying)::text, ('emt'::character varying)::text, ('resident'::character varying)::text])))),
    CONSTRAINT check_screening_efficiency CHECK (((screening_efficiency IS NULL) OR ((screening_efficiency >= 0) AND (screening_efficiency <= 100))))
);


ALTER TABLE public.people OWNER TO scheduler;

--
-- Name: person_certifications; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.person_certifications (
    id uuid NOT NULL,
    person_id uuid NOT NULL,
    certification_type_id uuid NOT NULL,
    certification_number character varying(100),
    issued_date date NOT NULL,
    expiration_date date NOT NULL,
    status character varying(50) DEFAULT '''current'''::character varying,
    verified_by character varying(255),
    verified_date date,
    document_url character varying(500),
    reminder_180_sent timestamp without time zone,
    reminder_90_sent timestamp without time zone,
    reminder_30_sent timestamp without time zone,
    reminder_14_sent timestamp without time zone,
    reminder_7_sent timestamp without time zone,
    notes text,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT check_cert_status CHECK (((status)::text = ANY (ARRAY[('current'::character varying)::text, ('expiring_soon'::character varying)::text, ('expired'::character varying)::text, ('pending'::character varying)::text])))
);


ALTER TABLE public.person_certifications OWNER TO scheduler;

--
-- Name: positive_feedback_alerts; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.positive_feedback_alerts (
    id uuid NOT NULL,
    name character varying(100) NOT NULL,
    description character varying(500),
    detected_at timestamp without time zone DEFAULT now() NOT NULL,
    trigger character varying(200),
    amplification character varying(200),
    consequence character varying(200),
    evidence jsonb,
    confidence double precision,
    severity character varying(20),
    intervention_recommended character varying(500),
    urgency character varying(20),
    resolved_at timestamp without time zone,
    resolution_notes character varying(500),
    intervention_effective boolean,
    CONSTRAINT check_urgency CHECK (((urgency IS NULL) OR ((urgency)::text = ANY (ARRAY[('immediate'::character varying)::text, ('soon'::character varying)::text, ('monitor'::character varying)::text]))))
);


ALTER TABLE public.positive_feedback_alerts OWNER TO scheduler;

--
-- Name: preference_trails; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.preference_trails (
    id uuid NOT NULL,
    faculty_id uuid NOT NULL,
    trail_type character varying(50) NOT NULL,
    slot_id uuid,
    slot_type character varying(100),
    block_type character varying(100),
    service_type character varying(100),
    target_faculty_id uuid,
    strength double precision NOT NULL,
    peak_strength double precision NOT NULL,
    evaporation_rate double precision NOT NULL,
    reinforcement_count integer NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    last_reinforced timestamp with time zone,
    last_evaporated timestamp with time zone
);


ALTER TABLE public.preference_trails OWNER TO scheduler;

--
-- Name: procedure_credentials; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.procedure_credentials (
    id uuid NOT NULL,
    person_id uuid NOT NULL,
    procedure_id uuid NOT NULL,
    status character varying(50) DEFAULT '''active'''::character varying NOT NULL,
    competency_level character varying(50) DEFAULT '''qualified'''::character varying,
    issued_date date DEFAULT CURRENT_DATE,
    expiration_date date,
    last_verified_date date,
    max_concurrent_residents integer,
    max_per_week integer,
    max_per_academic_year integer,
    notes text,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT check_competency_level CHECK (((competency_level)::text = ANY (ARRAY[('trainee'::character varying)::text, ('qualified'::character varying)::text, ('expert'::character varying)::text, ('master'::character varying)::text]))),
    CONSTRAINT check_credential_status CHECK (((status)::text = ANY (ARRAY[('active'::character varying)::text, ('expired'::character varying)::text, ('suspended'::character varying)::text, ('pending'::character varying)::text])))
);


ALTER TABLE public.procedure_credentials OWNER TO scheduler;

--
-- Name: procedures; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.procedures (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    category character varying(100),
    specialty character varying(100),
    supervision_ratio integer DEFAULT 1,
    requires_certification boolean DEFAULT true,
    complexity_level character varying(50) DEFAULT '''standard'''::character varying,
    min_pgy_level integer DEFAULT 1,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT check_complexity_level CHECK (((complexity_level)::text = ANY (ARRAY[('basic'::character varying)::text, ('standard'::character varying)::text, ('advanced'::character varying)::text, ('complex'::character varying)::text]))),
    CONSTRAINT check_procedure_pgy_level CHECK (((min_pgy_level >= 1) AND (min_pgy_level <= 3))),
    CONSTRAINT check_supervision_ratio CHECK ((supervision_ratio >= 1))
);


ALTER TABLE public.procedures OWNER TO scheduler;

--
-- Name: rag_documents; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.rag_documents (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    content text NOT NULL,
    embedding public.vector(384) NOT NULL,
    doc_type character varying(100) NOT NULL,
    metadata_ jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.rag_documents OWNER TO scheduler;

--
-- Name: COLUMN rag_documents.id; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.rag_documents.id IS 'Unique document chunk identifier';


--
-- Name: COLUMN rag_documents.content; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.rag_documents.content IS 'Text content of the document chunk';


--
-- Name: COLUMN rag_documents.embedding; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.rag_documents.embedding IS '384-dimensional embedding from sentence-transformers (all-MiniLM-L6-v2)';


--
-- Name: COLUMN rag_documents.doc_type; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.rag_documents.doc_type IS 'Document type: acgme_rules, scheduling_policy, user_guide, etc.';


--
-- Name: COLUMN rag_documents.metadata_; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.rag_documents.metadata_ IS 'Additional metadata: source_file, page_number, section, author, etc.';


--
-- Name: COLUMN rag_documents.created_at; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.rag_documents.created_at IS 'Timestamp when chunk was created';


--
-- Name: COLUMN rag_documents.updated_at; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.rag_documents.updated_at IS 'Timestamp of last update';


--
-- Name: request_signatures; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.request_signatures (
    id uuid NOT NULL,
    signature_hash character varying(255) NOT NULL,
    api_key_id uuid,
    request_method character varying(10) NOT NULL,
    request_path character varying(2000) NOT NULL,
    request_timestamp timestamp without time zone NOT NULL,
    is_valid boolean NOT NULL,
    failure_reason character varying(255),
    client_ip character varying(45) NOT NULL,
    user_agent character varying(500),
    verified_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.request_signatures OWNER TO scheduler;

--
-- Name: resident_call_preloads; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.resident_call_preloads (
    id uuid NOT NULL,
    person_id uuid NOT NULL,
    call_date date NOT NULL,
    call_type character varying(20) NOT NULL,
    assigned_by character varying(20),
    notes character varying(500),
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT check_resident_call_assigned_by CHECK (((assigned_by IS NULL) OR ((assigned_by)::text = ANY ((ARRAY['chief'::character varying, 'scheduler'::character varying])::text[])))),
    CONSTRAINT check_resident_call_type CHECK (((call_type)::text = ANY ((ARRAY['ld_24hr'::character varying, 'nf_coverage'::character varying, 'weekend'::character varying])::text[])))
);


ALTER TABLE public.resident_call_preloads OWNER TO scheduler;

--
-- Name: resident_weekly_requirements; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.resident_weekly_requirements (
    id uuid NOT NULL,
    rotation_template_id uuid NOT NULL,
    fm_clinic_min_per_week integer DEFAULT 2 NOT NULL,
    fm_clinic_max_per_week integer DEFAULT 3 NOT NULL,
    specialty_min_per_week integer DEFAULT 0 NOT NULL,
    specialty_max_per_week integer DEFAULT 10 NOT NULL,
    academics_required boolean DEFAULT true NOT NULL,
    protected_slots jsonb DEFAULT '{}'::jsonb NOT NULL,
    allowed_clinic_days jsonb DEFAULT '[]'::jsonb NOT NULL,
    specialty_name character varying(255),
    description character varying(1024),
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.resident_weekly_requirements OWNER TO scheduler;

--
-- Name: resilience_events; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.resilience_events (
    id uuid NOT NULL,
    "timestamp" timestamp without time zone DEFAULT now() NOT NULL,
    event_type character varying(50) NOT NULL,
    severity character varying(20),
    reason character varying(500),
    triggered_by character varying(100),
    previous_state jsonb,
    new_state jsonb,
    related_health_check_id uuid,
    metadata jsonb,
    CONSTRAINT check_event_type CHECK (((event_type)::text = ANY (ARRAY[('health_check'::character varying)::text, ('crisis_activated'::character varying)::text, ('crisis_deactivated'::character varying)::text, ('fallback_activated'::character varying)::text, ('fallback_deactivated'::character varying)::text, ('load_shedding_activated'::character varying)::text, ('load_shedding_deactivated'::character varying)::text, ('defense_level_changed'::character varying)::text, ('threshold_exceeded'::character varying)::text, ('n1_violation'::character varying)::text, ('n2_violation'::character varying)::text])))
);


ALTER TABLE public.resilience_events OWNER TO scheduler;

--
-- Name: resilience_health_checks; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.resilience_health_checks (
    id uuid NOT NULL,
    "timestamp" timestamp without time zone DEFAULT now() NOT NULL,
    overall_status character varying(20) NOT NULL,
    utilization_rate double precision NOT NULL,
    utilization_level character varying(20) NOT NULL,
    buffer_remaining double precision,
    defense_level character varying(30),
    load_shedding_level character varying(20),
    n1_pass boolean,
    n2_pass boolean,
    phase_transition_risk character varying(20),
    active_fallbacks character varying[],
    crisis_mode boolean,
    immediate_actions jsonb,
    watch_items jsonb,
    metrics_snapshot jsonb,
    CONSTRAINT check_health_status CHECK (((overall_status)::text = ANY (ARRAY[('healthy'::character varying)::text, ('warning'::character varying)::text, ('degraded'::character varying)::text, ('critical'::character varying)::text, ('emergency'::character varying)::text]))),
    CONSTRAINT check_utilization_level CHECK (((utilization_level)::text = ANY (ARRAY[('GREEN'::character varying)::text, ('YELLOW'::character varying)::text, ('ORANGE'::character varying)::text, ('RED'::character varying)::text, ('BLACK'::character varying)::text])))
);


ALTER TABLE public.resilience_health_checks OWNER TO scheduler;

--
-- Name: rotation_activity_requirements; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.rotation_activity_requirements (
    id uuid NOT NULL,
    rotation_template_id uuid NOT NULL,
    activity_id uuid NOT NULL,
    min_halfdays integer DEFAULT 0 NOT NULL,
    max_halfdays integer DEFAULT 14 NOT NULL,
    target_halfdays integer,
    applicable_weeks jsonb,
    applicable_weeks_hash uuid NOT NULL,
    prefer_full_days boolean DEFAULT true NOT NULL,
    preferred_days jsonb,
    avoid_days jsonb,
    priority integer DEFAULT 50 NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.rotation_activity_requirements OWNER TO scheduler;

--
-- Name: rotation_halfday_requirements; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.rotation_halfday_requirements (
    id uuid NOT NULL,
    rotation_template_id uuid NOT NULL,
    fm_clinic_halfdays integer NOT NULL,
    specialty_halfdays integer NOT NULL,
    specialty_name character varying(255),
    academics_halfdays integer NOT NULL,
    elective_halfdays integer,
    min_consecutive_specialty integer,
    prefer_combined_clinic_days boolean,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.rotation_halfday_requirements OWNER TO scheduler;

--
-- Name: rotation_preferences; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.rotation_preferences (
    id uuid NOT NULL,
    rotation_template_id uuid NOT NULL,
    preference_type character varying(50) NOT NULL,
    weight character varying(20) NOT NULL,
    config_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    is_active boolean NOT NULL,
    description character varying(200),
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


ALTER TABLE public.rotation_preferences OWNER TO scheduler;

--
-- Name: COLUMN rotation_preferences.preference_type; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.rotation_preferences.preference_type IS 'full_day_grouping, consecutive_specialty, avoid_isolated, preferred_days, avoid_friday_pm, balance_weekly';


--
-- Name: COLUMN rotation_preferences.weight; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.rotation_preferences.weight IS 'low, medium, high, required';


--
-- Name: COLUMN rotation_preferences.config_json; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.rotation_preferences.config_json IS 'Type-specific configuration parameters';


--
-- Name: rotation_templates; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.rotation_templates (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    activity_type character varying(255) NOT NULL,
    abbreviation character varying(20),
    clinic_location character varying(255),
    max_residents integer,
    requires_specialty character varying(255),
    requires_procedure_credential boolean,
    supervision_required boolean,
    max_supervision_ratio integer,
    created_at timestamp without time zone DEFAULT now(),
    leave_eligible boolean DEFAULT true NOT NULL,
    is_block_half_rotation boolean DEFAULT false NOT NULL,
    pattern_type character varying(20) DEFAULT 'regular'::character varying NOT NULL,
    setting_type character varying(20) DEFAULT 'outpatient'::character varying NOT NULL,
    paired_template_id uuid,
    split_day integer,
    is_mirror_primary boolean DEFAULT true NOT NULL,
    font_color character varying(50),
    background_color character varying(50),
    display_abbreviation character varying(20),
    is_archived boolean DEFAULT false NOT NULL,
    archived_at timestamp without time zone,
    archived_by uuid,
    template_category character varying(20) NOT NULL,
    includes_weekend_work boolean DEFAULT false NOT NULL,
    first_half_component_id uuid,
    second_half_component_id uuid
);


ALTER TABLE public.rotation_templates OWNER TO scheduler;

--
-- Name: COLUMN rotation_templates.pattern_type; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.rotation_templates.pattern_type IS 'regular, split, mirrored, alternating';


--
-- Name: COLUMN rotation_templates.setting_type; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.rotation_templates.setting_type IS 'inpatient or outpatient';


--
-- Name: COLUMN rotation_templates.paired_template_id; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.rotation_templates.paired_template_id IS 'For split rotations, the paired template';


--
-- Name: COLUMN rotation_templates.split_day; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.rotation_templates.split_day IS 'Day in block where split occurs (1-27)';


--
-- Name: COLUMN rotation_templates.is_mirror_primary; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.rotation_templates.is_mirror_primary IS 'For mirrored splits, is this the primary pattern?';


--
-- Name: COLUMN rotation_templates.includes_weekend_work; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.rotation_templates.includes_weekend_work IS 'True if rotation includes weekend assignments';


--
-- Name: sacrifice_decisions; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.sacrifice_decisions (
    id uuid NOT NULL,
    "timestamp" timestamp without time zone DEFAULT now() NOT NULL,
    from_level character varying(20) NOT NULL,
    to_level character varying(20) NOT NULL,
    reason character varying(500) NOT NULL,
    activities_suspended character varying[],
    activities_protected character varying[],
    approved_by character varying(100),
    approval_method character varying(50),
    utilization_at_decision double precision,
    coverage_at_decision double precision,
    related_event_id uuid,
    recovered_at timestamp without time zone,
    recovery_reason character varying(500),
    CONSTRAINT check_from_level CHECK (((from_level)::text = ANY (ARRAY[('NORMAL'::character varying)::text, ('YELLOW'::character varying)::text, ('ORANGE'::character varying)::text, ('RED'::character varying)::text, ('BLACK'::character varying)::text, ('CRITICAL'::character varying)::text]))),
    CONSTRAINT check_to_level CHECK (((to_level)::text = ANY (ARRAY[('NORMAL'::character varying)::text, ('YELLOW'::character varying)::text, ('ORANGE'::character varying)::text, ('RED'::character varying)::text, ('BLACK'::character varying)::text, ('CRITICAL'::character varying)::text])))
);


ALTER TABLE public.sacrifice_decisions OWNER TO scheduler;

--
-- Name: schedule_diffs; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.schedule_diffs (
    id uuid NOT NULL,
    from_version_id uuid NOT NULL,
    to_version_id uuid NOT NULL,
    computed_at timestamp without time zone DEFAULT now(),
    assignments_added jsonb DEFAULT '{}'::jsonb,
    assignments_removed jsonb DEFAULT '{}'::jsonb,
    assignments_modified jsonb DEFAULT '{}'::jsonb,
    total_changes integer,
    persons_affected integer,
    blocks_affected integer
);


ALTER TABLE public.schedule_diffs OWNER TO scheduler;

--
-- Name: schedule_draft_assignments; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.schedule_draft_assignments (
    id uuid NOT NULL,
    draft_id uuid NOT NULL,
    person_id uuid NOT NULL,
    assignment_date date NOT NULL,
    time_of_day character varying(10) DEFAULT 'ALL'::character varying NOT NULL,
    activity_code character varying(50),
    rotation_id uuid,
    change_type public.draft_assignment_change_type NOT NULL,
    existing_assignment_id uuid,
    created_assignment_id uuid
);


ALTER TABLE public.schedule_draft_assignments OWNER TO scheduler;

--
-- Name: schedule_draft_flags; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.schedule_draft_flags (
    id uuid NOT NULL,
    draft_id uuid NOT NULL,
    flag_type public.draft_flag_type NOT NULL,
    severity public.draft_flag_severity NOT NULL,
    message text NOT NULL,
    assignment_id uuid,
    person_id uuid,
    affected_date date,
    acknowledged_at timestamp without time zone,
    acknowledged_by_id uuid,
    resolution_note text,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.schedule_draft_flags OWNER TO scheduler;

--
-- Name: schedule_drafts; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.schedule_drafts (
    id uuid NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    created_by_id uuid,
    target_block integer,
    target_start_date date NOT NULL,
    target_end_date date NOT NULL,
    status public.schedule_draft_status DEFAULT 'draft'::public.schedule_draft_status NOT NULL,
    source_type public.draft_source_type NOT NULL,
    source_schedule_run_id uuid,
    published_at timestamp without time zone,
    published_by_id uuid,
    archived_version_id uuid,
    rollback_available boolean,
    rollback_expires_at timestamp without time zone,
    rolled_back_at timestamp without time zone,
    rolled_back_by_id uuid,
    notes text,
    change_summary jsonb,
    flags_total integer,
    flags_acknowledged integer,
    override_comment text,
    override_by_id uuid
);


ALTER TABLE public.schedule_drafts OWNER TO scheduler;

--
-- Name: schedule_runs; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.schedule_runs (
    id uuid NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    algorithm character varying(50) NOT NULL,
    status character varying(50) NOT NULL,
    total_blocks_assigned integer,
    acgme_violations integer,
    runtime_seconds numeric(10,2),
    config_json jsonb,
    created_at timestamp without time zone DEFAULT now(),
    acgme_override_count integer DEFAULT 0
);


ALTER TABLE public.schedule_runs OWNER TO scheduler;

--
-- Name: schedule_runs_version; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.schedule_runs_version (
    id uuid NOT NULL,
    start_date date,
    end_date date,
    algorithm character varying(50),
    status character varying(50),
    total_blocks_assigned integer,
    acgme_violations integer,
    acgme_override_count integer,
    runtime_seconds numeric(10,2),
    config_json jsonb,
    created_at timestamp without time zone,
    transaction_id bigint NOT NULL,
    operation_type smallint NOT NULL,
    end_transaction_id bigint,
    start_date_mod boolean,
    end_date_mod boolean,
    algorithm_mod boolean,
    status_mod boolean,
    total_blocks_assigned_mod boolean,
    acgme_violations_mod boolean,
    acgme_override_count_mod boolean,
    runtime_seconds_mod boolean,
    config_json_mod boolean,
    created_at_mod boolean
);


ALTER TABLE public.schedule_runs_version OWNER TO scheduler;

--
-- Name: schedule_versions; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.schedule_versions (
    id uuid NOT NULL,
    schedule_run_id uuid,
    version_number integer NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    trigger_type character varying(50) NOT NULL,
    parent_version_id uuid,
    model_hash character varying(64),
    total_assignments integer,
    total_persons integer,
    date_range_start date,
    date_range_end date,
    CONSTRAINT check_trigger_type CHECK (((trigger_type)::text = ANY (ARRAY[('generation'::character varying)::text, ('swap'::character varying)::text, ('absence'::character varying)::text, ('manual_edit'::character varying)::text, ('auto_rebalance'::character varying)::text])))
);


ALTER TABLE public.schedule_versions OWNER TO scheduler;

--
-- Name: scheduled_jobs; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.scheduled_jobs (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    job_func character varying(500) NOT NULL,
    trigger_type character varying(50) NOT NULL,
    trigger_config jsonb DEFAULT '{}'::jsonb NOT NULL,
    args jsonb DEFAULT '[]'::jsonb,
    kwargs jsonb DEFAULT '{}'::jsonb,
    next_run_time timestamp without time zone,
    last_run_time timestamp without time zone,
    run_count integer DEFAULT 0 NOT NULL,
    max_instances integer DEFAULT 1 NOT NULL,
    misfire_grace_time integer,
    "coalesce" boolean DEFAULT true NOT NULL,
    enabled boolean DEFAULT true NOT NULL,
    description text,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    created_by character varying(255)
);


ALTER TABLE public.scheduled_jobs OWNER TO scheduler;

--
-- Name: scheduled_notifications; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.scheduled_notifications (
    id uuid NOT NULL,
    recipient_id uuid NOT NULL,
    notification_type character varying(50) NOT NULL,
    data jsonb DEFAULT '{}'::jsonb,
    send_at timestamp without time zone NOT NULL,
    status character varying(20) DEFAULT '''pending'''::character varying,
    sent_at timestamp without time zone,
    error_message text,
    retry_count integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT check_scheduled_status CHECK (((status)::text = ANY (ARRAY[('pending'::character varying)::text, ('processing'::character varying)::text, ('sent'::character varying)::text, ('failed'::character varying)::text, ('cancelled'::character varying)::text])))
);


ALTER TABLE public.scheduled_notifications OWNER TO scheduler;

--
-- Name: scheduling_zones; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.scheduling_zones (
    id uuid NOT NULL,
    name character varying(100) NOT NULL,
    zone_type character varying(50) NOT NULL,
    description character varying(500),
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    services character varying[],
    minimum_coverage integer,
    optimal_coverage integer,
    maximum_coverage integer,
    status character varying(20),
    containment_level character varying(20),
    last_status_change timestamp without time zone,
    borrowing_limit integer,
    lending_limit integer,
    priority integer,
    can_borrow_from_zones character varying[],
    can_lend_to_zones character varying[],
    total_borrowing_requests integer,
    total_lending_events integer,
    is_active boolean,
    CONSTRAINT check_containment_level CHECK (((containment_level)::text = ANY (ARRAY[('none'::character varying)::text, ('soft'::character varying)::text, ('moderate'::character varying)::text, ('strict'::character varying)::text, ('lockdown'::character varying)::text]))),
    CONSTRAINT check_zone_status CHECK (((status)::text = ANY (ARRAY[('green'::character varying)::text, ('yellow'::character varying)::text, ('orange'::character varying)::text, ('red'::character varying)::text, ('black'::character varying)::text]))),
    CONSTRAINT check_zone_type CHECK (((zone_type)::text = ANY (ARRAY[('inpatient'::character varying)::text, ('outpatient'::character varying)::text, ('education'::character varying)::text, ('research'::character varying)::text, ('admin'::character varying)::text, ('on_call'::character varying)::text])))
);


ALTER TABLE public.scheduling_zones OWNER TO scheduler;

--
-- Name: swap_approvals; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.swap_approvals (
    id uuid NOT NULL,
    swap_id uuid NOT NULL,
    faculty_id uuid NOT NULL,
    role character varying(20) NOT NULL,
    approved boolean,
    responded_at timestamp without time zone,
    response_notes text
);


ALTER TABLE public.swap_approvals OWNER TO scheduler;

--
-- Name: swap_records; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.swap_records (
    id uuid NOT NULL,
    source_faculty_id uuid NOT NULL,
    source_week date NOT NULL,
    target_faculty_id uuid NOT NULL,
    target_week date,
    swap_type character varying(20) NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    requested_at timestamp without time zone DEFAULT now() NOT NULL,
    requested_by_id uuid,
    approved_at timestamp without time zone,
    approved_by_id uuid,
    executed_at timestamp without time zone,
    executed_by_id uuid,
    rolled_back_at timestamp without time zone,
    rolled_back_by_id uuid,
    rollback_reason text,
    reason text,
    notes text
);


ALTER TABLE public.swap_records OWNER TO scheduler;

--
-- Name: system_stress_records; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.system_stress_records (
    id uuid NOT NULL,
    stress_type character varying(50) NOT NULL,
    description character varying(500),
    applied_at timestamp without time zone DEFAULT now() NOT NULL,
    magnitude double precision NOT NULL,
    duration_days integer,
    is_acute boolean,
    is_reversible boolean,
    capacity_impact double precision,
    demand_impact double precision,
    is_active boolean,
    resolved_at timestamp without time zone,
    resolution_notes character varying(500),
    CONSTRAINT check_stress_type CHECK (((stress_type)::text = ANY (ARRAY[('faculty_loss'::character varying)::text, ('demand_surge'::character varying)::text, ('quality_pressure'::character varying)::text, ('time_compression'::character varying)::text, ('resource_scarcity'::character varying)::text, ('external_pressure'::character varying)::text])))
);


ALTER TABLE public.system_stress_records OWNER TO scheduler;

--
-- Name: task_history; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.task_history (
    id integer NOT NULL,
    task_description text NOT NULL,
    embedding public.vector(384),
    agent_used character varying NOT NULL,
    model_used character varying NOT NULL,
    success boolean NOT NULL,
    duration_ms integer,
    session_id character varying,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.task_history OWNER TO scheduler;

--
-- Name: COLUMN task_history.embedding; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.task_history.embedding IS 'Embedding of task description';


--
-- Name: COLUMN task_history.agent_used; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.task_history.agent_used IS 'Which agent handled this task';


--
-- Name: COLUMN task_history.model_used; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.task_history.model_used IS 'Which model was used (haiku, sonnet, opus)';


--
-- Name: COLUMN task_history.success; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.task_history.success IS 'Whether the task completed successfully';


--
-- Name: COLUMN task_history.duration_ms; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.task_history.duration_ms IS 'Task execution duration in milliseconds';


--
-- Name: COLUMN task_history.session_id; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.task_history.session_id IS 'Claude Code session identifier';


--
-- Name: task_history_id_seq; Type: SEQUENCE; Schema: public; Owner: scheduler
--

CREATE SEQUENCE public.task_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.task_history_id_seq OWNER TO scheduler;

--
-- Name: task_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: scheduler
--

ALTER SEQUENCE public.task_history_id_seq OWNED BY public.task_history.id;


--
-- Name: token_blacklist; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.token_blacklist (
    id uuid NOT NULL,
    jti character varying(36) NOT NULL,
    token_type character varying(20) DEFAULT '''access'''::character varying,
    user_id uuid,
    blacklisted_at timestamp without time zone DEFAULT now() NOT NULL,
    expires_at timestamp without time zone NOT NULL,
    reason character varying(100) DEFAULT '''logout'''::character varying
);


ALTER TABLE public.token_blacklist OWNER TO scheduler;

--
-- Name: trail_signals; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.trail_signals (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    trail_id uuid NOT NULL,
    signal_type character varying(50) NOT NULL,
    strength_change double precision NOT NULL,
    recorded_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.trail_signals OWNER TO scheduler;

--
-- Name: transaction; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.transaction (
    id bigint NOT NULL,
    issued_at timestamp without time zone DEFAULT now(),
    user_id character varying(255),
    remote_addr character varying(50)
);


ALTER TABLE public.transaction OWNER TO scheduler;

--
-- Name: transaction_id_seq; Type: SEQUENCE; Schema: public; Owner: scheduler
--

CREATE SEQUENCE public.transaction_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.transaction_id_seq OWNER TO scheduler;

--
-- Name: transaction_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: scheduler
--

ALTER SEQUENCE public.transaction_id_seq OWNED BY public.transaction.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.users (
    id uuid NOT NULL,
    username character varying(100) NOT NULL,
    email character varying(255) NOT NULL,
    hashed_password character varying(255) NOT NULL,
    role character varying(50) DEFAULT 'coordinator'::character varying NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    last_login timestamp without time zone,
    CONSTRAINT check_user_role CHECK (((role)::text = ANY (ARRAY[('admin'::character varying)::text, ('coordinator'::character varying)::text, ('faculty'::character varying)::text, ('clinical_staff'::character varying)::text, ('rn'::character varying)::text, ('lpn'::character varying)::text, ('msa'::character varying)::text, ('resident'::character varying)::text])))
);


ALTER TABLE public.users OWNER TO scheduler;

--
-- Name: v_absence_summary; Type: VIEW; Schema: public; Owner: scheduler
--

CREATE VIEW public.v_absence_summary AS
 SELECT p.id AS person_id,
    p.name,
    p.type AS person_type,
    a.absence_type,
    count(*) AS absence_count,
    sum(((a.end_date - a.start_date) + 1)) AS total_days
   FROM (public.people p
     LEFT JOIN public.absences a ON ((p.id = a.person_id)))
  GROUP BY p.id, p.name, p.type, a.absence_type;


ALTER TABLE public.v_absence_summary OWNER TO scheduler;

--
-- Name: v_block_absences; Type: VIEW; Schema: public; Owner: scheduler
--

CREATE VIEW public.v_block_absences AS
 WITH block_dates AS (
         SELECT t.block_num,
            t.start_date,
            t.end_date
           FROM ( VALUES (1,'2025-07-03'::date,'2025-07-30'::date), (2,'2025-07-31'::date,'2025-08-27'::date), (3,'2025-08-28'::date,'2025-09-24'::date), (4,'2025-09-25'::date,'2025-10-22'::date), (5,'2025-10-23'::date,'2025-11-19'::date), (6,'2025-11-20'::date,'2025-12-17'::date), (7,'2025-12-18'::date,'2026-01-14'::date), (8,'2026-01-15'::date,'2026-02-11'::date), (9,'2026-02-12'::date,'2026-03-11'::date), (10,'2026-03-12'::date,'2026-04-08'::date), (11,'2026-04-09'::date,'2026-05-06'::date), (12,'2026-05-07'::date,'2026-06-03'::date), (13,'2026-06-04'::date,'2026-06-30'::date)) t(block_num, start_date, end_date)
        )
 SELECT bd.block_num,
    p.name,
    p.type AS person_type,
    a.absence_type,
    a.is_away_from_program,
    GREATEST(a.start_date, bd.start_date) AS absence_start,
    LEAST(a.end_date, bd.end_date) AS absence_end,
    ((LEAST(a.end_date, bd.end_date) - GREATEST(a.start_date, bd.start_date)) + 1) AS days_in_block
   FROM ((block_dates bd
     JOIN public.absences a ON (((a.start_date <= bd.end_date) AND (a.end_date >= bd.start_date))))
     JOIN public.people p ON ((a.person_id = p.id)))
  ORDER BY bd.block_num, a.start_date;


ALTER TABLE public.v_block_absences OWNER TO scheduler;

--
-- Name: v_current_absences; Type: VIEW; Schema: public; Owner: scheduler
--

CREATE VIEW public.v_current_absences AS
 SELECT p.name,
    p.type AS person_type,
    a.absence_type,
    a.tdy_location,
    a.start_date,
    a.end_date,
    (a.end_date - CURRENT_DATE) AS days_remaining,
    a.is_away_from_program,
    a.is_blocking,
    a.notes
   FROM (public.absences a
     JOIN public.people p ON ((a.person_id = p.id)))
  WHERE ((CURRENT_DATE >= a.start_date) AND (CURRENT_DATE <= a.end_date))
  ORDER BY a.end_date;


ALTER TABLE public.v_current_absences OWNER TO scheduler;

--
-- Name: v_days_away_from_program; Type: VIEW; Schema: public; Owner: scheduler
--

CREATE VIEW public.v_days_away_from_program AS
 SELECT p.id AS person_id,
    p.name,
    p.type AS person_type,
    (EXTRACT(year FROM (a.start_date + '6 mons'::interval)))::integer AS academic_year,
    sum(((a.end_date - a.start_date) + 1)) AS total_days_away,
    sum(
        CASE
            WHEN a.is_tdy THEN ((a.end_date - a.start_date) + 1)
            ELSE 0
        END) AS tdy_days,
    count(*) AS absence_instances
   FROM (public.people p
     JOIN public.absences a ON ((p.id = a.person_id)))
  WHERE (a.is_away_from_program = true)
  GROUP BY p.id, p.name, p.type, (EXTRACT(year FROM (a.start_date + '6 mons'::interval)));


ALTER TABLE public.v_days_away_from_program OWNER TO scheduler;

--
-- Name: v_tdy_rotation_days; Type: VIEW; Schema: public; Owner: scheduler
--

CREATE VIEW public.v_tdy_rotation_days AS
 SELECT p.id AS person_id,
    p.name,
    p.type AS person_type,
    a.tdy_location,
    (EXTRACT(year FROM (a.start_date + '6 mons'::interval)))::integer AS academic_year,
    sum(((a.end_date - a.start_date) + 1)) AS total_days,
    count(*) AS rotation_count
   FROM (public.people p
     JOIN public.absences a ON ((p.id = a.person_id)))
  WHERE (((a.absence_type)::text = 'tdy'::text) AND (a.is_away_from_program = false))
  GROUP BY p.id, p.name, p.type, a.tdy_location, (EXTRACT(year FROM (a.start_date + '6 mons'::interval)));


ALTER TABLE public.v_tdy_rotation_days OWNER TO scheduler;

--
-- Name: v_tdy_rotations; Type: VIEW; Schema: public; Owner: scheduler
--

CREATE VIEW public.v_tdy_rotations AS
 SELECT p.id AS person_id,
    p.name,
    p.type AS person_type,
    ip.rotation_type,
    ip.tdy_location,
    ip.start_date,
    ip.end_date,
    ((ip.end_date - ip.start_date) + 1) AS days
   FROM (public.people p
     JOIN public.inpatient_preloads ip ON ((p.id = ip.person_id)))
  WHERE (ip.is_tdy = true)
  ORDER BY ip.start_date;


ALTER TABLE public.v_tdy_rotations OWNER TO scheduler;

--
-- Name: vulnerability_records; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.vulnerability_records (
    id uuid NOT NULL,
    analyzed_at timestamp without time zone DEFAULT now() NOT NULL,
    period_start timestamp without time zone,
    period_end timestamp without time zone,
    faculty_count integer,
    block_count integer,
    n1_pass boolean NOT NULL,
    n2_pass boolean NOT NULL,
    phase_transition_risk character varying(20),
    n1_vulnerabilities jsonb,
    n2_fatal_pairs jsonb,
    most_critical_faculty jsonb,
    recommended_actions character varying[],
    related_health_check_id uuid,
    CONSTRAINT check_phase_risk CHECK (((phase_transition_risk)::text = ANY (ARRAY[('low'::character varying)::text, ('medium'::character varying)::text, ('high'::character varying)::text, ('critical'::character varying)::text])))
);


ALTER TABLE public.vulnerability_records OWNER TO scheduler;

--
-- Name: weekly_patterns; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.weekly_patterns (
    id uuid NOT NULL,
    rotation_template_id uuid NOT NULL,
    day_of_week integer NOT NULL,
    time_of_day character varying(2) NOT NULL,
    activity_type character varying(50) NOT NULL,
    linked_template_id uuid,
    is_protected boolean NOT NULL,
    notes character varying(200),
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    week_number integer,
    activity_id uuid
);


ALTER TABLE public.weekly_patterns OWNER TO scheduler;

--
-- Name: COLUMN weekly_patterns.day_of_week; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.weekly_patterns.day_of_week IS '0=Sunday, 1=Monday, ..., 6=Saturday';


--
-- Name: COLUMN weekly_patterns.time_of_day; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.weekly_patterns.time_of_day IS 'AM or PM';


--
-- Name: COLUMN weekly_patterns.activity_type; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.weekly_patterns.activity_type IS 'fm_clinic, specialty, elective, conference, inpatient, call, procedure, off';


--
-- Name: COLUMN weekly_patterns.linked_template_id; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.weekly_patterns.linked_template_id IS 'Optional link to specific activity template';


--
-- Name: COLUMN weekly_patterns.is_protected; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.weekly_patterns.is_protected IS 'True for slots that cannot be changed (e.g., Wed AM conference)';


--
-- Name: COLUMN weekly_patterns.week_number; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.weekly_patterns.week_number IS 'Week 1-4 within the block. NULL = same pattern all weeks';


--
-- Name: COLUMN weekly_patterns.activity_id; Type: COMMENT; Schema: public; Owner: scheduler
--

COMMENT ON COLUMN public.weekly_patterns.activity_id IS 'FK to activities table - the activity assigned to this slot';


--
-- Name: zone_borrowing_records; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.zone_borrowing_records (
    id uuid NOT NULL,
    requesting_zone_id uuid NOT NULL,
    lending_zone_id uuid NOT NULL,
    faculty_id uuid NOT NULL,
    priority character varying(20) NOT NULL,
    reason character varying(500),
    duration_hours integer,
    requested_at timestamp without time zone DEFAULT now() NOT NULL,
    status character varying(20),
    approved_by character varying(100),
    approved_at timestamp without time zone,
    denial_reason character varying(500),
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    was_effective boolean,
    CONSTRAINT check_borrowing_priority CHECK (((priority)::text = ANY (ARRAY[('critical'::character varying)::text, ('high'::character varying)::text, ('medium'::character varying)::text, ('low'::character varying)::text]))),
    CONSTRAINT check_borrowing_status CHECK (((status)::text = ANY (ARRAY[('pending'::character varying)::text, ('approved'::character varying)::text, ('denied'::character varying)::text, ('completed'::character varying)::text])))
);


ALTER TABLE public.zone_borrowing_records OWNER TO scheduler;

--
-- Name: zone_faculty_assignments; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.zone_faculty_assignments (
    id uuid NOT NULL,
    zone_id uuid NOT NULL,
    faculty_id uuid NOT NULL,
    faculty_name character varying(200),
    role character varying(20) NOT NULL,
    assigned_at timestamp without time zone DEFAULT now() NOT NULL,
    is_available boolean,
    removed_at timestamp without time zone,
    CONSTRAINT check_faculty_role CHECK (((role)::text = ANY (ARRAY[('primary'::character varying)::text, ('secondary'::character varying)::text, ('backup'::character varying)::text])))
);


ALTER TABLE public.zone_faculty_assignments OWNER TO scheduler;

--
-- Name: zone_incidents; Type: TABLE; Schema: public; Owner: scheduler
--

CREATE TABLE public.zone_incidents (
    id uuid NOT NULL,
    zone_id uuid NOT NULL,
    incident_type character varying(50) NOT NULL,
    description character varying(500),
    started_at timestamp without time zone DEFAULT now() NOT NULL,
    severity character varying(20) NOT NULL,
    faculty_affected character varying[],
    capacity_lost double precision,
    services_affected character varying[],
    resolved_at timestamp without time zone,
    resolution_notes character varying(500),
    containment_successful boolean,
    CONSTRAINT check_incident_severity CHECK (((severity)::text = ANY (ARRAY[('minor'::character varying)::text, ('moderate'::character varying)::text, ('severe'::character varying)::text, ('critical'::character varying)::text])))
);


ALTER TABLE public.zone_incidents OWNER TO scheduler;

--
-- Name: task_history id; Type: DEFAULT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.task_history ALTER COLUMN id SET DEFAULT nextval('public.task_history_id_seq'::regclass);


--
-- Name: transaction id; Type: DEFAULT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.transaction ALTER COLUMN id SET DEFAULT nextval('public.transaction_id_seq'::regclass);


--
-- Name: absence_version absence_version_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.absence_version
    ADD CONSTRAINT absence_version_pkey PRIMARY KEY (id, transaction_id);


--
-- Name: absences absences_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.absences
    ADD CONSTRAINT absences_pkey PRIMARY KEY (id);


--
-- Name: absences_version absences_version_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.absences_version
    ADD CONSTRAINT absences_version_pkey PRIMARY KEY (id, transaction_id);


--
-- Name: activities activities_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.activities
    ADD CONSTRAINT activities_pkey PRIMARY KEY (id);


--
-- Name: activity_log activity_log_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.activity_log
    ADD CONSTRAINT activity_log_pkey PRIMARY KEY (id);


--
-- Name: agent_embeddings agent_embeddings_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.agent_embeddings
    ADD CONSTRAINT agent_embeddings_pkey PRIMARY KEY (agent_name);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: allostasis_records allostasis_records_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.allostasis_records
    ADD CONSTRAINT allostasis_records_pkey PRIMARY KEY (id);


--
-- Name: api_keys api_keys_key_hash_key; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.api_keys
    ADD CONSTRAINT api_keys_key_hash_key UNIQUE (key_hash);


--
-- Name: api_keys api_keys_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.api_keys
    ADD CONSTRAINT api_keys_pkey PRIMARY KEY (id);


--
-- Name: application_settings application_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.application_settings
    ADD CONSTRAINT application_settings_pkey PRIMARY KEY (id);


--
-- Name: approval_record approval_record_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.approval_record
    ADD CONSTRAINT approval_record_pkey PRIMARY KEY (id);


--
-- Name: assignments_version assignment_version_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.assignments_version
    ADD CONSTRAINT assignment_version_pkey PRIMARY KEY (id, transaction_id);


--
-- Name: assignments assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.assignments
    ADD CONSTRAINT assignments_pkey PRIMARY KEY (id);


--
-- Name: block_assignments block_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.block_assignments
    ADD CONSTRAINT block_assignments_pkey PRIMARY KEY (id);


--
-- Name: blocks blocks_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.blocks
    ADD CONSTRAINT blocks_pkey PRIMARY KEY (id);


--
-- Name: call_assignments call_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.call_assignments
    ADD CONSTRAINT call_assignments_pkey PRIMARY KEY (id);


--
-- Name: certification_types certification_types_name_key; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.certification_types
    ADD CONSTRAINT certification_types_name_key UNIQUE (name);


--
-- Name: certification_types certification_types_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.certification_types
    ADD CONSTRAINT certification_types_pkey PRIMARY KEY (id);


--
-- Name: chaos_experiments chaos_experiments_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.chaos_experiments
    ADD CONSTRAINT chaos_experiments_pkey PRIMARY KEY (id);


--
-- Name: clinic_sessions clinic_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.clinic_sessions
    ADD CONSTRAINT clinic_sessions_pkey PRIMARY KEY (id);


--
-- Name: cognitive_decisions cognitive_decisions_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.cognitive_decisions
    ADD CONSTRAINT cognitive_decisions_pkey PRIMARY KEY (id);


--
-- Name: cognitive_sessions cognitive_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.cognitive_sessions
    ADD CONSTRAINT cognitive_sessions_pkey PRIMARY KEY (id);


--
-- Name: compensation_records compensation_records_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.compensation_records
    ADD CONSTRAINT compensation_records_pkey PRIMARY KEY (id);


--
-- Name: conflict_alerts conflict_alerts_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.conflict_alerts
    ADD CONSTRAINT conflict_alerts_pkey PRIMARY KEY (id);


--
-- Name: cross_training_recommendations cross_training_recommendations_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.cross_training_recommendations
    ADD CONSTRAINT cross_training_recommendations_pkey PRIMARY KEY (id);


--
-- Name: email_logs email_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.email_logs
    ADD CONSTRAINT email_logs_pkey PRIMARY KEY (id);


--
-- Name: email_templates email_templates_name_key; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.email_templates
    ADD CONSTRAINT email_templates_name_key UNIQUE (name);


--
-- Name: email_templates email_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.email_templates
    ADD CONSTRAINT email_templates_pkey PRIMARY KEY (id);


--
-- Name: equilibrium_shifts equilibrium_shifts_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.equilibrium_shifts
    ADD CONSTRAINT equilibrium_shifts_pkey PRIMARY KEY (id);


--
-- Name: faculty_activity_permissions faculty_activity_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.faculty_activity_permissions
    ADD CONSTRAINT faculty_activity_permissions_pkey PRIMARY KEY (id);


--
-- Name: faculty_centrality faculty_centrality_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.faculty_centrality
    ADD CONSTRAINT faculty_centrality_pkey PRIMARY KEY (id);


--
-- Name: faculty_preferences faculty_preferences_faculty_id_key; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.faculty_preferences
    ADD CONSTRAINT faculty_preferences_faculty_id_key UNIQUE (faculty_id);


--
-- Name: faculty_preferences faculty_preferences_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.faculty_preferences
    ADD CONSTRAINT faculty_preferences_pkey PRIMARY KEY (id);


--
-- Name: faculty_weekly_overrides faculty_weekly_overrides_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.faculty_weekly_overrides
    ADD CONSTRAINT faculty_weekly_overrides_pkey PRIMARY KEY (id);


--
-- Name: faculty_weekly_templates faculty_weekly_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.faculty_weekly_templates
    ADD CONSTRAINT faculty_weekly_templates_pkey PRIMARY KEY (id);


--
-- Name: fallback_activations fallback_activations_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.fallback_activations
    ADD CONSTRAINT fallback_activations_pkey PRIMARY KEY (id);


--
-- Name: feature_flag_audit feature_flag_audit_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.feature_flag_audit
    ADD CONSTRAINT feature_flag_audit_pkey PRIMARY KEY (id);


--
-- Name: feature_flag_evaluations feature_flag_evaluations_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.feature_flag_evaluations
    ADD CONSTRAINT feature_flag_evaluations_pkey PRIMARY KEY (id);


--
-- Name: feature_flags feature_flags_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.feature_flags
    ADD CONSTRAINT feature_flags_pkey PRIMARY KEY (id);


--
-- Name: feedback_loop_states feedback_loop_states_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.feedback_loop_states
    ADD CONSTRAINT feedback_loop_states_pkey PRIMARY KEY (id);


--
-- Name: half_day_assignments half_day_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.half_day_assignments
    ADD CONSTRAINT half_day_assignments_pkey PRIMARY KEY (id);


--
-- Name: hub_protection_plans hub_protection_plans_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.hub_protection_plans
    ADD CONSTRAINT hub_protection_plans_pkey PRIMARY KEY (id);


--
-- Name: idempotency_requests idempotency_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.idempotency_requests
    ADD CONSTRAINT idempotency_requests_pkey PRIMARY KEY (id);


--
-- Name: import_batches import_batches_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.import_batches
    ADD CONSTRAINT import_batches_pkey PRIMARY KEY (id);


--
-- Name: import_staged_absences import_staged_absences_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.import_staged_absences
    ADD CONSTRAINT import_staged_absences_pkey PRIMARY KEY (id);


--
-- Name: import_staged_absences_version import_staged_absences_version_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.import_staged_absences_version
    ADD CONSTRAINT import_staged_absences_version_pkey PRIMARY KEY (id, transaction_id);


--
-- Name: import_staged_assignments import_staged_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.import_staged_assignments
    ADD CONSTRAINT import_staged_assignments_pkey PRIMARY KEY (id);


--
-- Name: inpatient_preloads inpatient_preloads_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.inpatient_preloads
    ADD CONSTRAINT inpatient_preloads_pkey PRIMARY KEY (id);


--
-- Name: intern_stagger_patterns intern_stagger_patterns_name_key; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.intern_stagger_patterns
    ADD CONSTRAINT intern_stagger_patterns_name_key UNIQUE (name);


--
-- Name: intern_stagger_patterns intern_stagger_patterns_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.intern_stagger_patterns
    ADD CONSTRAINT intern_stagger_patterns_pkey PRIMARY KEY (id);


--
-- Name: ip_blacklists ip_blacklists_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.ip_blacklists
    ADD CONSTRAINT ip_blacklists_pkey PRIMARY KEY (id);


--
-- Name: ip_whitelists ip_whitelists_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.ip_whitelists
    ADD CONSTRAINT ip_whitelists_pkey PRIMARY KEY (id);


--
-- Name: job_executions job_executions_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.job_executions
    ADD CONSTRAINT job_executions_pkey PRIMARY KEY (id);


--
-- Name: metric_snapshots metric_snapshots_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.metric_snapshots
    ADD CONSTRAINT metric_snapshots_pkey PRIMARY KEY (id);


--
-- Name: model_tiers model_tiers_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.model_tiers
    ADD CONSTRAINT model_tiers_pkey PRIMARY KEY (agent_name);


--
-- Name: notification_preferences notification_preferences_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.notification_preferences
    ADD CONSTRAINT notification_preferences_pkey PRIMARY KEY (id);


--
-- Name: notification_preferences notification_preferences_user_id_key; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.notification_preferences
    ADD CONSTRAINT notification_preferences_user_id_key UNIQUE (user_id);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id);


--
-- Name: oauth2_clients oauth2_clients_client_id_key; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.oauth2_clients
    ADD CONSTRAINT oauth2_clients_client_id_key UNIQUE (client_id);


--
-- Name: oauth2_clients oauth2_clients_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.oauth2_clients
    ADD CONSTRAINT oauth2_clients_pkey PRIMARY KEY (id);


--
-- Name: people people_email_key; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.people
    ADD CONSTRAINT people_email_key UNIQUE (email);


--
-- Name: people people_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.people
    ADD CONSTRAINT people_pkey PRIMARY KEY (id);


--
-- Name: person_certifications person_certifications_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.person_certifications
    ADD CONSTRAINT person_certifications_pkey PRIMARY KEY (id);


--
-- Name: positive_feedback_alerts positive_feedback_alerts_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.positive_feedback_alerts
    ADD CONSTRAINT positive_feedback_alerts_pkey PRIMARY KEY (id);


--
-- Name: preference_trails preference_trails_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.preference_trails
    ADD CONSTRAINT preference_trails_pkey PRIMARY KEY (id);


--
-- Name: procedure_credentials procedure_credentials_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.procedure_credentials
    ADD CONSTRAINT procedure_credentials_pkey PRIMARY KEY (id);


--
-- Name: procedures procedures_name_key; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.procedures
    ADD CONSTRAINT procedures_name_key UNIQUE (name);


--
-- Name: procedures procedures_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.procedures
    ADD CONSTRAINT procedures_pkey PRIMARY KEY (id);


--
-- Name: rag_documents rag_documents_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.rag_documents
    ADD CONSTRAINT rag_documents_pkey PRIMARY KEY (id);


--
-- Name: request_signatures request_signatures_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.request_signatures
    ADD CONSTRAINT request_signatures_pkey PRIMARY KEY (id);


--
-- Name: request_signatures request_signatures_signature_hash_key; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.request_signatures
    ADD CONSTRAINT request_signatures_signature_hash_key UNIQUE (signature_hash);


--
-- Name: resident_call_preloads resident_call_preloads_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.resident_call_preloads
    ADD CONSTRAINT resident_call_preloads_pkey PRIMARY KEY (id);


--
-- Name: resident_weekly_requirements resident_weekly_requirements_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.resident_weekly_requirements
    ADD CONSTRAINT resident_weekly_requirements_pkey PRIMARY KEY (id);


--
-- Name: resilience_events resilience_events_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.resilience_events
    ADD CONSTRAINT resilience_events_pkey PRIMARY KEY (id);


--
-- Name: resilience_health_checks resilience_health_checks_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.resilience_health_checks
    ADD CONSTRAINT resilience_health_checks_pkey PRIMARY KEY (id);


--
-- Name: rotation_activity_requirements rotation_activity_requirements_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.rotation_activity_requirements
    ADD CONSTRAINT rotation_activity_requirements_pkey PRIMARY KEY (id);


--
-- Name: rotation_halfday_requirements rotation_halfday_requirements_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.rotation_halfday_requirements
    ADD CONSTRAINT rotation_halfday_requirements_pkey PRIMARY KEY (id);


--
-- Name: rotation_preferences rotation_preferences_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.rotation_preferences
    ADD CONSTRAINT rotation_preferences_pkey PRIMARY KEY (id);


--
-- Name: rotation_templates rotation_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.rotation_templates
    ADD CONSTRAINT rotation_templates_pkey PRIMARY KEY (id);


--
-- Name: sacrifice_decisions sacrifice_decisions_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.sacrifice_decisions
    ADD CONSTRAINT sacrifice_decisions_pkey PRIMARY KEY (id);


--
-- Name: schedule_diffs schedule_diffs_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.schedule_diffs
    ADD CONSTRAINT schedule_diffs_pkey PRIMARY KEY (id);


--
-- Name: schedule_draft_assignments schedule_draft_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.schedule_draft_assignments
    ADD CONSTRAINT schedule_draft_assignments_pkey PRIMARY KEY (id);


--
-- Name: schedule_draft_flags schedule_draft_flags_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.schedule_draft_flags
    ADD CONSTRAINT schedule_draft_flags_pkey PRIMARY KEY (id);


--
-- Name: schedule_drafts schedule_drafts_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.schedule_drafts
    ADD CONSTRAINT schedule_drafts_pkey PRIMARY KEY (id);


--
-- Name: schedule_runs_version schedule_run_version_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.schedule_runs_version
    ADD CONSTRAINT schedule_run_version_pkey PRIMARY KEY (id, transaction_id);


--
-- Name: schedule_runs schedule_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.schedule_runs
    ADD CONSTRAINT schedule_runs_pkey PRIMARY KEY (id);


--
-- Name: schedule_versions schedule_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.schedule_versions
    ADD CONSTRAINT schedule_versions_pkey PRIMARY KEY (id);


--
-- Name: scheduled_jobs scheduled_jobs_name_key; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.scheduled_jobs
    ADD CONSTRAINT scheduled_jobs_name_key UNIQUE (name);


--
-- Name: scheduled_jobs scheduled_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.scheduled_jobs
    ADD CONSTRAINT scheduled_jobs_pkey PRIMARY KEY (id);


--
-- Name: scheduled_notifications scheduled_notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.scheduled_notifications
    ADD CONSTRAINT scheduled_notifications_pkey PRIMARY KEY (id);


--
-- Name: scheduling_zones scheduling_zones_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.scheduling_zones
    ADD CONSTRAINT scheduling_zones_pkey PRIMARY KEY (id);


--
-- Name: swap_approvals swap_approvals_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.swap_approvals
    ADD CONSTRAINT swap_approvals_pkey PRIMARY KEY (id);


--
-- Name: swap_records swap_records_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.swap_records
    ADD CONSTRAINT swap_records_pkey PRIMARY KEY (id);


--
-- Name: system_stress_records system_stress_records_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.system_stress_records
    ADD CONSTRAINT system_stress_records_pkey PRIMARY KEY (id);


--
-- Name: task_history task_history_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.task_history
    ADD CONSTRAINT task_history_pkey PRIMARY KEY (id);


--
-- Name: token_blacklist token_blacklist_jti_key; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.token_blacklist
    ADD CONSTRAINT token_blacklist_jti_key UNIQUE (jti);


--
-- Name: token_blacklist token_blacklist_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.token_blacklist
    ADD CONSTRAINT token_blacklist_pkey PRIMARY KEY (id);


--
-- Name: trail_signals trail_signals_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.trail_signals
    ADD CONSTRAINT trail_signals_pkey PRIMARY KEY (id);


--
-- Name: transaction transaction_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.transaction
    ADD CONSTRAINT transaction_pkey PRIMARY KEY (id);


--
-- Name: rotation_templates unique_abbreviation; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.rotation_templates
    ADD CONSTRAINT unique_abbreviation UNIQUE (abbreviation);


--
-- Name: blocks unique_block_per_half_day; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.blocks
    ADD CONSTRAINT unique_block_per_half_day UNIQUE (date, time_of_day);


--
-- Name: call_assignments unique_call_per_day; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.call_assignments
    ADD CONSTRAINT unique_call_per_day UNIQUE (date, person_id, call_type);


--
-- Name: assignments unique_person_per_block; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.assignments
    ADD CONSTRAINT unique_person_per_block UNIQUE (block_id, person_id);


--
-- Name: block_assignments unique_resident_per_block; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.block_assignments
    ADD CONSTRAINT unique_resident_per_block UNIQUE (block_number, academic_year, resident_id);


--
-- Name: activities uq_activity_code; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.activities
    ADD CONSTRAINT uq_activity_code UNIQUE (code);


--
-- Name: activities uq_activity_name; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.activities
    ADD CONSTRAINT uq_activity_name UNIQUE (name);


--
-- Name: approval_record uq_approval_record_chain_seq; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.approval_record
    ADD CONSTRAINT uq_approval_record_chain_seq UNIQUE (chain_id, sequence_num);


--
-- Name: schedule_draft_assignments uq_draft_assignment_slot; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.schedule_draft_assignments
    ADD CONSTRAINT uq_draft_assignment_slot UNIQUE (draft_id, person_id, assignment_date, time_of_day);


--
-- Name: faculty_activity_permissions uq_faculty_activity_permission; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.faculty_activity_permissions
    ADD CONSTRAINT uq_faculty_activity_permission UNIQUE (faculty_role, activity_id);


--
-- Name: faculty_weekly_overrides uq_faculty_weekly_override_slot; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.faculty_weekly_overrides
    ADD CONSTRAINT uq_faculty_weekly_override_slot UNIQUE (person_id, effective_date, day_of_week, time_of_day);


--
-- Name: faculty_weekly_templates uq_faculty_weekly_template_slot; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.faculty_weekly_templates
    ADD CONSTRAINT uq_faculty_weekly_template_slot UNIQUE (person_id, day_of_week, time_of_day, week_number);


--
-- Name: half_day_assignments uq_half_day_assignment_person_date_time; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.half_day_assignments
    ADD CONSTRAINT uq_half_day_assignment_person_date_time UNIQUE (person_id, date, time_of_day);


--
-- Name: inpatient_preloads uq_inpatient_preload_person_start_type; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.inpatient_preloads
    ADD CONSTRAINT uq_inpatient_preload_person_start_type UNIQUE (person_id, start_date, rotation_type);


--
-- Name: person_certifications uq_person_certification_type; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.person_certifications
    ADD CONSTRAINT uq_person_certification_type UNIQUE (person_id, certification_type_id);


--
-- Name: procedure_credentials uq_person_procedure_credential; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.procedure_credentials
    ADD CONSTRAINT uq_person_procedure_credential UNIQUE (person_id, procedure_id);


--
-- Name: resident_call_preloads uq_resident_call_person_date; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.resident_call_preloads
    ADD CONSTRAINT uq_resident_call_person_date UNIQUE (person_id, call_date);


--
-- Name: resident_weekly_requirements uq_resident_weekly_requirement_template; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.resident_weekly_requirements
    ADD CONSTRAINT uq_resident_weekly_requirement_template UNIQUE (rotation_template_id);


--
-- Name: rotation_activity_requirements uq_rotation_activity_req; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.rotation_activity_requirements
    ADD CONSTRAINT uq_rotation_activity_req UNIQUE (rotation_template_id, activity_id, applicable_weeks_hash);


--
-- Name: weekly_patterns uq_weekly_pattern_slot_v2; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.weekly_patterns
    ADD CONSTRAINT uq_weekly_pattern_slot_v2 UNIQUE (rotation_template_id, day_of_week, time_of_day, week_number);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: vulnerability_records vulnerability_records_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.vulnerability_records
    ADD CONSTRAINT vulnerability_records_pkey PRIMARY KEY (id);


--
-- Name: weekly_patterns weekly_patterns_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.weekly_patterns
    ADD CONSTRAINT weekly_patterns_pkey PRIMARY KEY (id);


--
-- Name: zone_borrowing_records zone_borrowing_records_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.zone_borrowing_records
    ADD CONSTRAINT zone_borrowing_records_pkey PRIMARY KEY (id);


--
-- Name: zone_faculty_assignments zone_faculty_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.zone_faculty_assignments
    ADD CONSTRAINT zone_faculty_assignments_pkey PRIMARY KEY (id);


--
-- Name: zone_incidents zone_incidents_pkey; Type: CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.zone_incidents
    ADD CONSTRAINT zone_incidents_pkey PRIMARY KEY (id);


--
-- Name: idx_absence_person_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_absence_person_id ON public.absences USING btree (person_id);


--
-- Name: idx_absence_version_end_transaction; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_absence_version_end_transaction ON public.absence_version USING btree (end_transaction_id);


--
-- Name: idx_absence_version_operation; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_absence_version_operation ON public.absence_version USING btree (operation_type);


--
-- Name: idx_absence_version_transaction; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_absence_version_transaction ON public.absence_version USING btree (transaction_id);


--
-- Name: idx_absences_dates; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_absences_dates ON public.absences USING btree (start_date, end_date);


--
-- Name: idx_absences_person_dates; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_absences_person_dates ON public.absences USING btree (person_id, start_date, end_date);


--
-- Name: idx_absences_type; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_absences_type ON public.absences USING btree (absence_type);


--
-- Name: idx_allostasis_calculated; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_allostasis_calculated ON public.allostasis_records USING btree (calculated_at);


--
-- Name: idx_allostasis_entity; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_allostasis_entity ON public.allostasis_records USING btree (entity_id, entity_type);


--
-- Name: idx_allostasis_risk; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_allostasis_risk ON public.allostasis_records USING btree (risk_level);


--
-- Name: idx_api_key_active; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_api_key_active ON public.api_keys USING btree (is_active, expires_at);


--
-- Name: idx_api_key_owner; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_api_key_owner ON public.api_keys USING btree (owner_id, is_active);


--
-- Name: idx_assignment_block_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_assignment_block_id ON public.assignments USING btree (block_id);


--
-- Name: idx_assignment_person_block; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_assignment_person_block ON public.assignments USING btree (person_id, block_id);


--
-- Name: idx_assignment_person_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_assignment_person_id ON public.assignments USING btree (person_id);


--
-- Name: idx_assignment_rotation_template_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_assignment_rotation_template_id ON public.assignments USING btree (rotation_template_id);


--
-- Name: idx_assignment_version_end_transaction; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_assignment_version_end_transaction ON public.assignments_version USING btree (end_transaction_id);


--
-- Name: idx_assignment_version_operation; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_assignment_version_operation ON public.assignments_version USING btree (operation_type);


--
-- Name: idx_assignment_version_transaction; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_assignment_version_transaction ON public.assignments_version USING btree (transaction_id);


--
-- Name: idx_assignments_block; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_assignments_block ON public.assignments USING btree (block_id);


--
-- Name: idx_assignments_person; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_assignments_person ON public.assignments USING btree (person_id);


--
-- Name: idx_assignments_schedule_run; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_assignments_schedule_run ON public.assignments USING btree (schedule_run_id);


--
-- Name: idx_blacklist_expires; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_blacklist_expires ON public.token_blacklist USING btree (expires_at);


--
-- Name: idx_blacklist_jti; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_blacklist_jti ON public.token_blacklist USING btree (jti);


--
-- Name: idx_blacklist_jti_expires; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_blacklist_jti_expires ON public.token_blacklist USING btree (jti, expires_at);


--
-- Name: idx_block_date; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_block_date ON public.blocks USING btree (date);


--
-- Name: idx_block_date_time_of_day; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_block_date_time_of_day ON public.blocks USING btree (date, time_of_day);


--
-- Name: idx_blocks_block_number; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_blocks_block_number ON public.blocks USING btree (block_number);


--
-- Name: idx_blocks_date; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_blocks_date ON public.blocks USING btree (date);


--
-- Name: idx_borrowing_lending; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_borrowing_lending ON public.zone_borrowing_records USING btree (lending_zone_id);


--
-- Name: idx_borrowing_requested_at; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_borrowing_requested_at ON public.zone_borrowing_records USING btree (requested_at);


--
-- Name: idx_borrowing_requesting; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_borrowing_requesting ON public.zone_borrowing_records USING btree (requesting_zone_id);


--
-- Name: idx_borrowing_status; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_borrowing_status ON public.zone_borrowing_records USING btree (status);


--
-- Name: idx_call_assignment_date; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_call_assignment_date ON public.call_assignments USING btree (date);


--
-- Name: idx_call_assignment_person_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_call_assignment_person_id ON public.call_assignments USING btree (person_id);


--
-- Name: idx_call_date; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_call_date ON public.call_assignments USING btree (date);


--
-- Name: idx_call_person; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_call_person ON public.call_assignments USING btree (person_id);


--
-- Name: idx_cert_types_active; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_cert_types_active ON public.certification_types USING btree (is_active);


--
-- Name: idx_cert_types_name; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_cert_types_name ON public.certification_types USING btree (name);


--
-- Name: idx_compensation_active; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_compensation_active ON public.compensation_records USING btree (is_active);


--
-- Name: idx_compensation_initiated; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_compensation_initiated ON public.compensation_records USING btree (initiated_at);


--
-- Name: idx_compensation_stress; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_compensation_stress ON public.compensation_records USING btree (stress_id);


--
-- Name: idx_credentials_expiration; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_credentials_expiration ON public.procedure_credentials USING btree (expiration_date);


--
-- Name: idx_credentials_person; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_credentials_person ON public.procedure_credentials USING btree (person_id);


--
-- Name: idx_credentials_procedure; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_credentials_procedure ON public.procedure_credentials USING btree (procedure_id);


--
-- Name: idx_credentials_status; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_credentials_status ON public.procedure_credentials USING btree (status);


--
-- Name: idx_diffs_computed; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_diffs_computed ON public.schedule_diffs USING btree (computed_at);


--
-- Name: idx_diffs_from_to; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_diffs_from_to ON public.schedule_diffs USING btree (from_version_id, to_version_id);


--
-- Name: idx_diffs_from_version; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_diffs_from_version ON public.schedule_diffs USING btree (from_version_id);


--
-- Name: idx_diffs_to_version; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_diffs_to_version ON public.schedule_diffs USING btree (to_version_id);


--
-- Name: idx_draft_assignments_date; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_draft_assignments_date ON public.schedule_draft_assignments USING btree (assignment_date);


--
-- Name: idx_draft_assignments_draft; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_draft_assignments_draft ON public.schedule_draft_assignments USING btree (draft_id);


--
-- Name: idx_draft_assignments_person; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_draft_assignments_person ON public.schedule_draft_assignments USING btree (person_id);


--
-- Name: idx_draft_flags_acknowledged; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_draft_flags_acknowledged ON public.schedule_draft_flags USING btree (acknowledged_at);


--
-- Name: idx_draft_flags_draft; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_draft_flags_draft ON public.schedule_draft_flags USING btree (draft_id);


--
-- Name: idx_draft_flags_severity; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_draft_flags_severity ON public.schedule_draft_flags USING btree (severity);


--
-- Name: idx_draft_flags_type; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_draft_flags_type ON public.schedule_draft_flags USING btree (flag_type);


--
-- Name: idx_equilibrium_calculated; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_equilibrium_calculated ON public.equilibrium_shifts USING btree (calculated_at);


--
-- Name: idx_equilibrium_state; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_equilibrium_state ON public.equilibrium_shifts USING btree (equilibrium_state);


--
-- Name: idx_equilibrium_sustainable; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_equilibrium_sustainable ON public.equilibrium_shifts USING btree (is_sustainable);


--
-- Name: idx_events_severity; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_events_severity ON public.resilience_events USING btree (severity);


--
-- Name: idx_events_timestamp; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_events_timestamp ON public.resilience_events USING btree ("timestamp");


--
-- Name: idx_events_type; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_events_type ON public.resilience_events USING btree (event_type);


--
-- Name: idx_fallback_activated_at; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_fallback_activated_at ON public.fallback_activations USING btree (activated_at);


--
-- Name: idx_fallback_active; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_fallback_active ON public.fallback_activations USING btree (deactivated_at);


--
-- Name: idx_fallback_scenario; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_fallback_scenario ON public.fallback_activations USING btree (scenario);


--
-- Name: idx_feature_flag_enabled; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_feature_flag_enabled ON public.feature_flags USING btree (enabled);


--
-- Name: idx_feature_flag_type; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_feature_flag_type ON public.feature_flags USING btree (flag_type);


--
-- Name: idx_feedback_loop_name; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_feedback_loop_name ON public.feedback_loop_states USING btree (loop_name);


--
-- Name: idx_feedback_loop_severity; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_feedback_loop_severity ON public.feedback_loop_states USING btree (deviation_severity);


--
-- Name: idx_feedback_loop_timestamp; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_feedback_loop_timestamp ON public.feedback_loop_states USING btree ("timestamp");


--
-- Name: idx_flag_audit_timestamp; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_flag_audit_timestamp ON public.feature_flag_audit USING btree (created_at);


--
-- Name: idx_flag_audit_user; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_flag_audit_user ON public.feature_flag_audit USING btree (user_id);


--
-- Name: idx_flag_eval_flag_user; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_flag_eval_flag_user ON public.feature_flag_evaluations USING btree (flag_id, user_id);


--
-- Name: idx_flag_eval_timestamp; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_flag_eval_timestamp ON public.feature_flag_evaluations USING btree (evaluated_at);


--
-- Name: idx_hda_activity_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_hda_activity_id ON public.half_day_assignments USING btree (activity_id);


--
-- Name: idx_hda_block_assignment_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_hda_block_assignment_id ON public.half_day_assignments USING btree (block_assignment_id);


--
-- Name: idx_hda_date; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_hda_date ON public.half_day_assignments USING btree (date);


--
-- Name: idx_hda_date_time; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_hda_date_time ON public.half_day_assignments USING btree (date, time_of_day);


--
-- Name: idx_hda_person_date; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_hda_person_date ON public.half_day_assignments USING btree (person_id, date);


--
-- Name: idx_hda_person_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_hda_person_id ON public.half_day_assignments USING btree (person_id);


--
-- Name: idx_hda_source; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_hda_source ON public.half_day_assignments USING btree (source);


--
-- Name: idx_health_checks_status; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_health_checks_status ON public.resilience_health_checks USING btree (overall_status);


--
-- Name: idx_health_checks_timestamp; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_health_checks_timestamp ON public.resilience_health_checks USING btree ("timestamp");


--
-- Name: idx_idempotency_expires; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_idempotency_expires ON public.idempotency_requests USING btree (expires_at);


--
-- Name: idx_idempotency_key_hash; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE UNIQUE INDEX idx_idempotency_key_hash ON public.idempotency_requests USING btree (idempotency_key, body_hash);


--
-- Name: idx_idempotency_status; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_idempotency_status ON public.idempotency_requests USING btree (status);


--
-- Name: idx_incidents_resolved; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_incidents_resolved ON public.zone_incidents USING btree (resolved_at);


--
-- Name: idx_incidents_severity; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_incidents_severity ON public.zone_incidents USING btree (severity);


--
-- Name: idx_incidents_started; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_incidents_started ON public.zone_incidents USING btree (started_at);


--
-- Name: idx_incidents_zone; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_incidents_zone ON public.zone_incidents USING btree (zone_id);


--
-- Name: idx_inpatient_preload_dates; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_inpatient_preload_dates ON public.inpatient_preloads USING btree (start_date, end_date);


--
-- Name: idx_inpatient_preload_person_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_inpatient_preload_person_id ON public.inpatient_preloads USING btree (person_id);


--
-- Name: idx_inpatient_preload_rotation_type; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_inpatient_preload_rotation_type ON public.inpatient_preloads USING btree (rotation_type);


--
-- Name: idx_inpatient_preload_start_date; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_inpatient_preload_start_date ON public.inpatient_preloads USING btree (start_date);


--
-- Name: idx_ip_blacklist_active; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_ip_blacklist_active ON public.ip_blacklists USING btree (is_active, expires_at);


--
-- Name: idx_ip_blacklist_detection; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_ip_blacklist_detection ON public.ip_blacklists USING btree (detection_method, is_active);


--
-- Name: idx_ip_whitelist_active; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_ip_whitelist_active ON public.ip_whitelists USING btree (is_active, expires_at);


--
-- Name: idx_ip_whitelist_applies_to; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_ip_whitelist_applies_to ON public.ip_whitelists USING btree (applies_to, is_active);


--
-- Name: idx_metrics_category; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_metrics_category ON public.metric_snapshots USING btree (category);


--
-- Name: idx_notifications_created; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_notifications_created ON public.notifications USING btree (created_at);


--
-- Name: idx_notifications_is_read; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_notifications_is_read ON public.notifications USING btree (is_read);


--
-- Name: idx_notifications_recipient; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_notifications_recipient ON public.notifications USING btree (recipient_id);


--
-- Name: idx_notifications_type; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_notifications_type ON public.notifications USING btree (notification_type);


--
-- Name: idx_oauth2_client_active; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_oauth2_client_active ON public.oauth2_clients USING btree (is_active);


--
-- Name: idx_oauth2_client_owner; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_oauth2_client_owner ON public.oauth2_clients USING btree (owner_id, is_active);


--
-- Name: idx_people_type; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_people_type ON public.people USING btree (type);


--
-- Name: idx_person_certs_expiration; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_person_certs_expiration ON public.person_certifications USING btree (expiration_date);


--
-- Name: idx_person_certs_person; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_person_certs_person ON public.person_certifications USING btree (person_id);


--
-- Name: idx_person_certs_status; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_person_certs_status ON public.person_certifications USING btree (status);


--
-- Name: idx_person_certs_type; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_person_certs_type ON public.person_certifications USING btree (certification_type_id);


--
-- Name: idx_positive_feedback_detected; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_positive_feedback_detected ON public.positive_feedback_alerts USING btree (detected_at);


--
-- Name: idx_positive_feedback_resolved; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_positive_feedback_resolved ON public.positive_feedback_alerts USING btree (resolved_at);


--
-- Name: idx_positive_feedback_urgency; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_positive_feedback_urgency ON public.positive_feedback_alerts USING btree (urgency);


--
-- Name: idx_prefs_user; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_prefs_user ON public.notification_preferences USING btree (user_id);


--
-- Name: idx_procedures_active; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_procedures_active ON public.procedures USING btree (is_active);


--
-- Name: idx_procedures_category; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_procedures_category ON public.procedures USING btree (category);


--
-- Name: idx_procedures_name; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_procedures_name ON public.procedures USING btree (name);


--
-- Name: idx_procedures_specialty; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_procedures_specialty ON public.procedures USING btree (specialty);


--
-- Name: idx_request_signature_api_key; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_request_signature_api_key ON public.request_signatures USING btree (api_key_id, verified_at);


--
-- Name: idx_request_signature_timestamp; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_request_signature_timestamp ON public.request_signatures USING btree (request_timestamp, verified_at);


--
-- Name: idx_resident_call_date; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_resident_call_date ON public.resident_call_preloads USING btree (call_date);


--
-- Name: idx_resident_call_person_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_resident_call_person_id ON public.resident_call_preloads USING btree (person_id);


--
-- Name: idx_rotation_halfday_template; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE UNIQUE INDEX idx_rotation_halfday_template ON public.rotation_halfday_requirements USING btree (rotation_template_id);


--
-- Name: idx_sacrifice_active; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_sacrifice_active ON public.sacrifice_decisions USING btree (recovered_at);


--
-- Name: idx_sacrifice_timestamp; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_sacrifice_timestamp ON public.sacrifice_decisions USING btree ("timestamp");


--
-- Name: idx_schedule_drafts_block; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_schedule_drafts_block ON public.schedule_drafts USING btree (target_block);


--
-- Name: idx_schedule_drafts_dates; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_schedule_drafts_dates ON public.schedule_drafts USING btree (target_start_date, target_end_date);


--
-- Name: idx_schedule_drafts_status; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_schedule_drafts_status ON public.schedule_drafts USING btree (status);


--
-- Name: idx_schedule_runs_date; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_schedule_runs_date ON public.schedule_runs USING btree (created_at);


--
-- Name: idx_schedule_runs_version_end_transaction; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_schedule_runs_version_end_transaction ON public.schedule_runs_version USING btree (end_transaction_id);


--
-- Name: idx_schedule_runs_version_operation; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_schedule_runs_version_operation ON public.schedule_runs_version USING btree (operation_type);


--
-- Name: idx_schedule_runs_version_transaction; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_schedule_runs_version_transaction ON public.schedule_runs_version USING btree (transaction_id);


--
-- Name: idx_schedule_versions_created; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_schedule_versions_created ON public.schedule_versions USING btree (created_at);


--
-- Name: idx_schedule_versions_parent; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_schedule_versions_parent ON public.schedule_versions USING btree (parent_version_id);


--
-- Name: idx_schedule_versions_run; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_schedule_versions_run ON public.schedule_versions USING btree (schedule_run_id);


--
-- Name: idx_schedule_versions_trigger; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_schedule_versions_trigger ON public.schedule_versions USING btree (trigger_type);


--
-- Name: idx_scheduled_recipient; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_scheduled_recipient ON public.scheduled_notifications USING btree (recipient_id);


--
-- Name: idx_scheduled_send_at; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_scheduled_send_at ON public.scheduled_notifications USING btree (send_at);


--
-- Name: idx_scheduled_status; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_scheduled_status ON public.scheduled_notifications USING btree (status);


--
-- Name: idx_stress_active; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_stress_active ON public.system_stress_records USING btree (is_active);


--
-- Name: idx_stress_applied; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_stress_applied ON public.system_stress_records USING btree (applied_at);


--
-- Name: idx_stress_type; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_stress_type ON public.system_stress_records USING btree (stress_type);


--
-- Name: idx_swap_source_faculty; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_swap_source_faculty ON public.swap_records USING btree (source_faculty_id);


--
-- Name: idx_swap_target_faculty; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_swap_target_faculty ON public.swap_records USING btree (target_faculty_id);


--
-- Name: idx_transaction_issued_at; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_transaction_issued_at ON public.transaction USING btree (issued_at);


--
-- Name: idx_transaction_user_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_transaction_user_id ON public.transaction USING btree (user_id);


--
-- Name: idx_vulnerability_analyzed_at; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_vulnerability_analyzed_at ON public.vulnerability_records USING btree (analyzed_at);


--
-- Name: idx_vulnerability_n1_pass; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_vulnerability_n1_pass ON public.vulnerability_records USING btree (n1_pass);


--
-- Name: idx_vulnerability_n2_pass; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_vulnerability_n2_pass ON public.vulnerability_records USING btree (n2_pass);


--
-- Name: idx_zone_faculty_available; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_zone_faculty_available ON public.zone_faculty_assignments USING btree (is_available);


--
-- Name: idx_zone_faculty_faculty; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_zone_faculty_faculty ON public.zone_faculty_assignments USING btree (faculty_id);


--
-- Name: idx_zone_faculty_zone; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_zone_faculty_zone ON public.zone_faculty_assignments USING btree (zone_id);


--
-- Name: idx_zones_name; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE UNIQUE INDEX idx_zones_name ON public.scheduling_zones USING btree (name);


--
-- Name: idx_zones_status; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_zones_status ON public.scheduling_zones USING btree (status);


--
-- Name: idx_zones_type; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX idx_zones_type ON public.scheduling_zones USING btree (zone_type);


--
-- Name: ix_activities_activity_category; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_activities_activity_category ON public.activities USING btree (activity_category);


--
-- Name: ix_activities_code; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_activities_code ON public.activities USING btree (code);


--
-- Name: ix_activities_is_archived; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_activities_is_archived ON public.activities USING btree (is_archived);


--
-- Name: ix_activities_is_protected; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_activities_is_protected ON public.activities USING btree (is_protected);


--
-- Name: ix_activity_log_action_type; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_activity_log_action_type ON public.activity_log USING btree (action_type);


--
-- Name: ix_activity_log_created_at; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_activity_log_created_at ON public.activity_log USING btree (created_at DESC);


--
-- Name: ix_activity_log_failed_actions; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_activity_log_failed_actions ON public.activity_log USING btree (created_at DESC) WHERE (((details ->> 'success'::text) = 'false'::text) OR ((action_type)::text ~~ '%_FAILED'::text));


--
-- Name: ix_activity_log_target; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_activity_log_target ON public.activity_log USING btree (target_entity, target_id);


--
-- Name: ix_activity_log_user_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_activity_log_user_id ON public.activity_log USING btree (user_id);


--
-- Name: ix_api_keys_key_hash; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_api_keys_key_hash ON public.api_keys USING btree (key_hash);


--
-- Name: ix_api_keys_key_prefix; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_api_keys_key_prefix ON public.api_keys USING btree (key_prefix);


--
-- Name: ix_approval_record_acgme_overrides; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_approval_record_acgme_overrides ON public.approval_record USING btree (created_at DESC) WHERE ((action)::text ~~ 'ACGME_OVERRIDE%'::text);


--
-- Name: ix_approval_record_action; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_approval_record_action ON public.approval_record USING btree (action);


--
-- Name: ix_approval_record_actor_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_approval_record_actor_id ON public.approval_record USING btree (actor_id);


--
-- Name: ix_approval_record_chain_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_approval_record_chain_id ON public.approval_record USING btree (chain_id);


--
-- Name: ix_approval_record_chain_seq; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_approval_record_chain_seq ON public.approval_record USING btree (chain_id, sequence_num);


--
-- Name: ix_approval_record_created_at; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_approval_record_created_at ON public.approval_record USING btree (created_at DESC);


--
-- Name: ix_approval_record_seals; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_approval_record_seals ON public.approval_record USING btree (chain_id, sequence_num DESC) WHERE ((action)::text = 'DAY_SEALED'::text);


--
-- Name: ix_approval_record_target; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_approval_record_target ON public.approval_record USING btree (target_entity_type, target_entity_id);


--
-- Name: ix_block_assignments_block_year; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_block_assignments_block_year ON public.block_assignments USING btree (block_number, academic_year);


--
-- Name: ix_block_assignments_has_leave; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_block_assignments_has_leave ON public.block_assignments USING btree (has_leave) WHERE (has_leave = true);


--
-- Name: ix_block_assignments_resident_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_block_assignments_resident_id ON public.block_assignments USING btree (resident_id);


--
-- Name: ix_block_assignments_rotation_template_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_block_assignments_rotation_template_id ON public.block_assignments USING btree (rotation_template_id);


--
-- Name: ix_block_assignments_secondary_rotation; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_block_assignments_secondary_rotation ON public.block_assignments USING btree (secondary_rotation_template_id);


--
-- Name: ix_chaos_experiments_injector_type; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_chaos_experiments_injector_type ON public.chaos_experiments USING btree (injector_type);


--
-- Name: ix_chaos_experiments_scheduled_at; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_chaos_experiments_scheduled_at ON public.chaos_experiments USING btree (scheduled_at);


--
-- Name: ix_chaos_experiments_started_at; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_chaos_experiments_started_at ON public.chaos_experiments USING btree (started_at);


--
-- Name: ix_chaos_experiments_status; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_chaos_experiments_status ON public.chaos_experiments USING btree (status);


--
-- Name: ix_clinic_sessions_date; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_clinic_sessions_date ON public.clinic_sessions USING btree (date);


--
-- Name: ix_cognitive_decisions_category; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_cognitive_decisions_category ON public.cognitive_decisions USING btree (category);


--
-- Name: ix_cognitive_decisions_created_at; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_cognitive_decisions_created_at ON public.cognitive_decisions USING btree (created_at);


--
-- Name: ix_cognitive_decisions_outcome; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_cognitive_decisions_outcome ON public.cognitive_decisions USING btree (outcome);


--
-- Name: ix_cognitive_decisions_session_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_cognitive_decisions_session_id ON public.cognitive_decisions USING btree (session_id);


--
-- Name: ix_cognitive_sessions_started_at; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_cognitive_sessions_started_at ON public.cognitive_sessions USING btree (started_at);


--
-- Name: ix_cognitive_sessions_user_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_cognitive_sessions_user_id ON public.cognitive_sessions USING btree (user_id);


--
-- Name: ix_conflict_alerts_faculty_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_conflict_alerts_faculty_id ON public.conflict_alerts USING btree (faculty_id);


--
-- Name: ix_conflict_alerts_fmit_week; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_conflict_alerts_fmit_week ON public.conflict_alerts USING btree (fmit_week);


--
-- Name: ix_conflict_alerts_status; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_conflict_alerts_status ON public.conflict_alerts USING btree (status);


--
-- Name: ix_cross_training_priority; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_cross_training_priority ON public.cross_training_recommendations USING btree (priority);


--
-- Name: ix_cross_training_status; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_cross_training_status ON public.cross_training_recommendations USING btree (status);


--
-- Name: ix_email_logs_created_at; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_email_logs_created_at ON public.email_logs USING btree (created_at);


--
-- Name: ix_email_logs_notification_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_email_logs_notification_id ON public.email_logs USING btree (notification_id);


--
-- Name: ix_email_logs_recipient_email; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_email_logs_recipient_email ON public.email_logs USING btree (recipient_email);


--
-- Name: ix_email_logs_status; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_email_logs_status ON public.email_logs USING btree (status);


--
-- Name: ix_email_logs_template_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_email_logs_template_id ON public.email_logs USING btree (template_id);


--
-- Name: ix_email_templates_is_active; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_email_templates_is_active ON public.email_templates USING btree (is_active);


--
-- Name: ix_email_templates_name; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_email_templates_name ON public.email_templates USING btree (name);


--
-- Name: ix_email_templates_template_type; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_email_templates_template_type ON public.email_templates USING btree (template_type);


--
-- Name: ix_faculty_activity_permissions_role; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_faculty_activity_permissions_role ON public.faculty_activity_permissions USING btree (faculty_role);


--
-- Name: ix_faculty_centrality_composite_score; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_faculty_centrality_composite_score ON public.faculty_centrality USING btree (composite_score);


--
-- Name: ix_faculty_centrality_faculty_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_faculty_centrality_faculty_id ON public.faculty_centrality USING btree (faculty_id);


--
-- Name: ix_faculty_centrality_is_hub; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_faculty_centrality_is_hub ON public.faculty_centrality USING btree (is_hub);


--
-- Name: ix_faculty_preferences_faculty_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_faculty_preferences_faculty_id ON public.faculty_preferences USING btree (faculty_id);


--
-- Name: ix_faculty_weekly_overrides_effective_date; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_faculty_weekly_overrides_effective_date ON public.faculty_weekly_overrides USING btree (effective_date);


--
-- Name: ix_faculty_weekly_overrides_person_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_faculty_weekly_overrides_person_id ON public.faculty_weekly_overrides USING btree (person_id);


--
-- Name: ix_faculty_weekly_templates_activity_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_faculty_weekly_templates_activity_id ON public.faculty_weekly_templates USING btree (activity_id);


--
-- Name: ix_faculty_weekly_templates_person_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_faculty_weekly_templates_person_id ON public.faculty_weekly_templates USING btree (person_id);


--
-- Name: ix_feature_flag_audit_created_at; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_feature_flag_audit_created_at ON public.feature_flag_audit USING btree (created_at);


--
-- Name: ix_feature_flag_audit_flag_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_feature_flag_audit_flag_id ON public.feature_flag_audit USING btree (flag_id);


--
-- Name: ix_feature_flag_audit_user_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_feature_flag_audit_user_id ON public.feature_flag_audit USING btree (user_id);


--
-- Name: ix_feature_flag_evaluations_evaluated_at; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_feature_flag_evaluations_evaluated_at ON public.feature_flag_evaluations USING btree (evaluated_at);


--
-- Name: ix_feature_flag_evaluations_flag_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_feature_flag_evaluations_flag_id ON public.feature_flag_evaluations USING btree (flag_id);


--
-- Name: ix_feature_flag_evaluations_user_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_feature_flag_evaluations_user_id ON public.feature_flag_evaluations USING btree (user_id);


--
-- Name: ix_feature_flags_key; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE UNIQUE INDEX ix_feature_flags_key ON public.feature_flags USING btree (key);


--
-- Name: ix_hub_protection_plans_hub_faculty_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_hub_protection_plans_hub_faculty_id ON public.hub_protection_plans USING btree (hub_faculty_id);


--
-- Name: ix_hub_protection_plans_period; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_hub_protection_plans_period ON public.hub_protection_plans USING btree (period_start, period_end);


--
-- Name: ix_hub_protection_plans_status; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_hub_protection_plans_status ON public.hub_protection_plans USING btree (status);


--
-- Name: ix_import_batches_created_at; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_import_batches_created_at ON public.import_batches USING btree (created_at);


--
-- Name: ix_import_batches_file_hash; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_import_batches_file_hash ON public.import_batches USING btree (file_hash);


--
-- Name: ix_import_batches_status; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_import_batches_status ON public.import_batches USING btree (status);


--
-- Name: ix_import_staged_absences_batch_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_import_staged_absences_batch_id ON public.import_staged_absences USING btree (batch_id);


--
-- Name: ix_import_staged_absences_batch_status; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_import_staged_absences_batch_status ON public.import_staged_absences USING btree (batch_id, status);


--
-- Name: ix_import_staged_absences_date_range; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_import_staged_absences_date_range ON public.import_staged_absences USING btree (start_date, end_date);


--
-- Name: ix_import_staged_absences_matched_person_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_import_staged_absences_matched_person_id ON public.import_staged_absences USING btree (matched_person_id);


--
-- Name: ix_import_staged_absences_overlap_type; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_import_staged_absences_overlap_type ON public.import_staged_absences USING btree (overlap_type);


--
-- Name: ix_import_staged_absences_status; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_import_staged_absences_status ON public.import_staged_absences USING btree (status);


--
-- Name: ix_import_staged_absences_version_end_txn; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_import_staged_absences_version_end_txn ON public.import_staged_absences_version USING btree (end_transaction_id);


--
-- Name: ix_import_staged_absences_version_txn; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_import_staged_absences_version_txn ON public.import_staged_absences_version USING btree (transaction_id);


--
-- Name: ix_import_staged_assignments_assignment_date; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_import_staged_assignments_assignment_date ON public.import_staged_assignments USING btree (assignment_date);


--
-- Name: ix_import_staged_assignments_batch_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_import_staged_assignments_batch_id ON public.import_staged_assignments USING btree (batch_id);


--
-- Name: ix_import_staged_assignments_batch_status; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_import_staged_assignments_batch_status ON public.import_staged_assignments USING btree (batch_id, status);


--
-- Name: ix_import_staged_assignments_matched_person_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_import_staged_assignments_matched_person_id ON public.import_staged_assignments USING btree (matched_person_id);


--
-- Name: ix_import_staged_assignments_status; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_import_staged_assignments_status ON public.import_staged_assignments USING btree (status);


--
-- Name: ix_ip_blacklists_ip_address; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_ip_blacklists_ip_address ON public.ip_blacklists USING btree (ip_address);


--
-- Name: ix_ip_whitelists_ip_address; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_ip_whitelists_ip_address ON public.ip_whitelists USING btree (ip_address);


--
-- Name: ix_job_executions_job_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_job_executions_job_id ON public.job_executions USING btree (job_id);


--
-- Name: ix_job_executions_job_name; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_job_executions_job_name ON public.job_executions USING btree (job_name);


--
-- Name: ix_job_executions_started_at; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_job_executions_started_at ON public.job_executions USING btree (started_at);


--
-- Name: ix_job_executions_status; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_job_executions_status ON public.job_executions USING btree (status);


--
-- Name: ix_metrics_name_time; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_metrics_name_time ON public.metric_snapshots USING btree (metric_name, computed_at);


--
-- Name: ix_metrics_version_category; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_metrics_version_category ON public.metric_snapshots USING btree (schedule_version_id, category);


--
-- Name: ix_oauth2_clients_client_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_oauth2_clients_client_id ON public.oauth2_clients USING btree (client_id);


--
-- Name: ix_preference_trails_faculty_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_preference_trails_faculty_id ON public.preference_trails USING btree (faculty_id);


--
-- Name: ix_preference_trails_slot_type; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_preference_trails_slot_type ON public.preference_trails USING btree (slot_type);


--
-- Name: ix_preference_trails_strength; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_preference_trails_strength ON public.preference_trails USING btree (strength);


--
-- Name: ix_preference_trails_trail_type; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_preference_trails_trail_type ON public.preference_trails USING btree (trail_type);


--
-- Name: ix_rag_documents_doc_type; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_rag_documents_doc_type ON public.rag_documents USING btree (doc_type);


--
-- Name: ix_rag_documents_embedding_hnsw; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_rag_documents_embedding_hnsw ON public.rag_documents USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: ix_rag_documents_embedding_ivfflat; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_rag_documents_embedding_ivfflat ON public.rag_documents USING ivfflat (embedding public.vector_cosine_ops) WITH (lists='100');


--
-- Name: ix_rag_documents_metadata; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_rag_documents_metadata ON public.rag_documents USING gin (metadata_);


--
-- Name: ix_request_signatures_signature_hash; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_request_signatures_signature_hash ON public.request_signatures USING btree (signature_hash);


--
-- Name: ix_resident_weekly_requirements_template_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_resident_weekly_requirements_template_id ON public.resident_weekly_requirements USING btree (rotation_template_id);


--
-- Name: ix_rotation_activity_req_activity; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_rotation_activity_req_activity ON public.rotation_activity_requirements USING btree (activity_id);


--
-- Name: ix_rotation_activity_req_template; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_rotation_activity_req_template ON public.rotation_activity_requirements USING btree (rotation_template_id);


--
-- Name: ix_rotation_preferences_rotation_template_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_rotation_preferences_rotation_template_id ON public.rotation_preferences USING btree (rotation_template_id);


--
-- Name: ix_rotation_templates_half_components; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_rotation_templates_half_components ON public.rotation_templates USING btree (first_half_component_id, second_half_component_id) WHERE (is_block_half_rotation = true);


--
-- Name: ix_rotation_templates_is_archived; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_rotation_templates_is_archived ON public.rotation_templates USING btree (is_archived);


--
-- Name: ix_rotation_templates_template_category; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_rotation_templates_template_category ON public.rotation_templates USING btree (template_category);


--
-- Name: ix_scheduled_jobs_enabled; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_scheduled_jobs_enabled ON public.scheduled_jobs USING btree (enabled);


--
-- Name: ix_scheduled_jobs_name; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_scheduled_jobs_name ON public.scheduled_jobs USING btree (name);


--
-- Name: ix_scheduled_jobs_next_run_time; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_scheduled_jobs_next_run_time ON public.scheduled_jobs USING btree (next_run_time);


--
-- Name: ix_swap_approvals_swap_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_swap_approvals_swap_id ON public.swap_approvals USING btree (swap_id);


--
-- Name: ix_swap_records_source_faculty_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_swap_records_source_faculty_id ON public.swap_records USING btree (source_faculty_id);


--
-- Name: ix_swap_records_source_week; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_swap_records_source_week ON public.swap_records USING btree (source_week);


--
-- Name: ix_swap_records_status; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_swap_records_status ON public.swap_records USING btree (status);


--
-- Name: ix_swap_records_target_faculty_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_swap_records_target_faculty_id ON public.swap_records USING btree (target_faculty_id);


--
-- Name: ix_trail_signals_recorded_at; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_trail_signals_recorded_at ON public.trail_signals USING btree (recorded_at);


--
-- Name: ix_trail_signals_trail_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_trail_signals_trail_id ON public.trail_signals USING btree (trail_id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: ix_weekly_patterns_activity_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_weekly_patterns_activity_id ON public.weekly_patterns USING btree (activity_id);


--
-- Name: ix_weekly_patterns_rotation_template_id; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX ix_weekly_patterns_rotation_template_id ON public.weekly_patterns USING btree (rotation_template_id);


--
-- Name: task_history_agent_idx; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX task_history_agent_idx ON public.task_history USING btree (agent_used, created_at DESC);


--
-- Name: task_history_embedding_idx; Type: INDEX; Schema: public; Owner: scheduler
--

CREATE INDEX task_history_embedding_idx ON public.task_history USING hnsw (embedding public.vector_cosine_ops);


--
-- Name: rag_documents rag_documents_updated_at_trigger; Type: TRIGGER; Schema: public; Owner: scheduler
--

CREATE TRIGGER rag_documents_updated_at_trigger BEFORE UPDATE ON public.rag_documents FOR EACH ROW EXECUTE FUNCTION public.update_rag_documents_updated_at();


--
-- Name: absence_version absence_version_end_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.absence_version
    ADD CONSTRAINT absence_version_end_transaction_id_fkey FOREIGN KEY (end_transaction_id) REFERENCES public.transaction(id);


--
-- Name: absence_version absence_version_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.absence_version
    ADD CONSTRAINT absence_version_transaction_id_fkey FOREIGN KEY (transaction_id) REFERENCES public.transaction(id);


--
-- Name: absences absences_person_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.absences
    ADD CONSTRAINT absences_person_id_fkey FOREIGN KEY (person_id) REFERENCES public.people(id) ON DELETE CASCADE;


--
-- Name: absences_version absences_version_end_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.absences_version
    ADD CONSTRAINT absences_version_end_transaction_id_fkey FOREIGN KEY (end_transaction_id) REFERENCES public.transaction(id);


--
-- Name: activity_log activity_log_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.activity_log
    ADD CONSTRAINT activity_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: api_keys api_keys_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.api_keys
    ADD CONSTRAINT api_keys_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: api_keys api_keys_revoked_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.api_keys
    ADD CONSTRAINT api_keys_revoked_by_id_fkey FOREIGN KEY (revoked_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: api_keys api_keys_rotated_from_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.api_keys
    ADD CONSTRAINT api_keys_rotated_from_id_fkey FOREIGN KEY (rotated_from_id) REFERENCES public.api_keys(id) ON DELETE SET NULL;


--
-- Name: api_keys api_keys_rotated_to_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.api_keys
    ADD CONSTRAINT api_keys_rotated_to_id_fkey FOREIGN KEY (rotated_to_id) REFERENCES public.api_keys(id) ON DELETE SET NULL;


--
-- Name: approval_record approval_record_actor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.approval_record
    ADD CONSTRAINT approval_record_actor_id_fkey FOREIGN KEY (actor_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: approval_record approval_record_prev_record_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.approval_record
    ADD CONSTRAINT approval_record_prev_record_id_fkey FOREIGN KEY (prev_record_id) REFERENCES public.approval_record(id) ON DELETE SET NULL;


--
-- Name: assignments_version assignment_version_end_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.assignments_version
    ADD CONSTRAINT assignment_version_end_transaction_id_fkey FOREIGN KEY (end_transaction_id) REFERENCES public.transaction(id);


--
-- Name: assignments_version assignment_version_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.assignments_version
    ADD CONSTRAINT assignment_version_transaction_id_fkey FOREIGN KEY (transaction_id) REFERENCES public.transaction(id);


--
-- Name: assignments assignments_block_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.assignments
    ADD CONSTRAINT assignments_block_id_fkey FOREIGN KEY (block_id) REFERENCES public.blocks(id) ON DELETE CASCADE;


--
-- Name: assignments assignments_person_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.assignments
    ADD CONSTRAINT assignments_person_id_fkey FOREIGN KEY (person_id) REFERENCES public.people(id) ON DELETE CASCADE;


--
-- Name: assignments assignments_rotation_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.assignments
    ADD CONSTRAINT assignments_rotation_template_id_fkey FOREIGN KEY (rotation_template_id) REFERENCES public.rotation_templates(id);


--
-- Name: block_assignments block_assignments_resident_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.block_assignments
    ADD CONSTRAINT block_assignments_resident_id_fkey FOREIGN KEY (resident_id) REFERENCES public.people(id) ON DELETE CASCADE;


--
-- Name: block_assignments block_assignments_rotation_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.block_assignments
    ADD CONSTRAINT block_assignments_rotation_template_id_fkey FOREIGN KEY (rotation_template_id) REFERENCES public.rotation_templates(id) ON DELETE SET NULL;


--
-- Name: block_assignments block_assignments_secondary_rotation_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.block_assignments
    ADD CONSTRAINT block_assignments_secondary_rotation_template_id_fkey FOREIGN KEY (secondary_rotation_template_id) REFERENCES public.rotation_templates(id) ON DELETE SET NULL;


--
-- Name: call_assignments call_assignments_person_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.call_assignments
    ADD CONSTRAINT call_assignments_person_id_fkey FOREIGN KEY (person_id) REFERENCES public.people(id) ON DELETE CASCADE;


--
-- Name: cognitive_decisions cognitive_decisions_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.cognitive_decisions
    ADD CONSTRAINT cognitive_decisions_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.cognitive_sessions(id) ON DELETE SET NULL;


--
-- Name: compensation_records compensation_records_stress_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.compensation_records
    ADD CONSTRAINT compensation_records_stress_id_fkey FOREIGN KEY (stress_id) REFERENCES public.system_stress_records(id) ON DELETE CASCADE;


--
-- Name: conflict_alerts conflict_alerts_acknowledged_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.conflict_alerts
    ADD CONSTRAINT conflict_alerts_acknowledged_by_id_fkey FOREIGN KEY (acknowledged_by_id) REFERENCES public.users(id);


--
-- Name: conflict_alerts conflict_alerts_faculty_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.conflict_alerts
    ADD CONSTRAINT conflict_alerts_faculty_id_fkey FOREIGN KEY (faculty_id) REFERENCES public.people(id);


--
-- Name: conflict_alerts conflict_alerts_leave_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.conflict_alerts
    ADD CONSTRAINT conflict_alerts_leave_id_fkey FOREIGN KEY (leave_id) REFERENCES public.absences(id);


--
-- Name: conflict_alerts conflict_alerts_resolved_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.conflict_alerts
    ADD CONSTRAINT conflict_alerts_resolved_by_id_fkey FOREIGN KEY (resolved_by_id) REFERENCES public.users(id);


--
-- Name: email_logs email_logs_notification_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.email_logs
    ADD CONSTRAINT email_logs_notification_id_fkey FOREIGN KEY (notification_id) REFERENCES public.notifications(id) ON DELETE SET NULL;


--
-- Name: faculty_activity_permissions faculty_activity_permissions_activity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.faculty_activity_permissions
    ADD CONSTRAINT faculty_activity_permissions_activity_id_fkey FOREIGN KEY (activity_id) REFERENCES public.activities(id) ON DELETE CASCADE;


--
-- Name: faculty_preferences faculty_preferences_faculty_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.faculty_preferences
    ADD CONSTRAINT faculty_preferences_faculty_id_fkey FOREIGN KEY (faculty_id) REFERENCES public.people(id);


--
-- Name: faculty_weekly_overrides faculty_weekly_overrides_activity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.faculty_weekly_overrides
    ADD CONSTRAINT faculty_weekly_overrides_activity_id_fkey FOREIGN KEY (activity_id) REFERENCES public.activities(id) ON DELETE RESTRICT;


--
-- Name: faculty_weekly_overrides faculty_weekly_overrides_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.faculty_weekly_overrides
    ADD CONSTRAINT faculty_weekly_overrides_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.people(id) ON DELETE SET NULL;


--
-- Name: faculty_weekly_overrides faculty_weekly_overrides_person_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.faculty_weekly_overrides
    ADD CONSTRAINT faculty_weekly_overrides_person_id_fkey FOREIGN KEY (person_id) REFERENCES public.people(id) ON DELETE CASCADE;


--
-- Name: faculty_weekly_templates faculty_weekly_templates_activity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.faculty_weekly_templates
    ADD CONSTRAINT faculty_weekly_templates_activity_id_fkey FOREIGN KEY (activity_id) REFERENCES public.activities(id) ON DELETE RESTRICT;


--
-- Name: faculty_weekly_templates faculty_weekly_templates_person_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.faculty_weekly_templates
    ADD CONSTRAINT faculty_weekly_templates_person_id_fkey FOREIGN KEY (person_id) REFERENCES public.people(id) ON DELETE CASCADE;


--
-- Name: fallback_activations fallback_activations_related_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.fallback_activations
    ADD CONSTRAINT fallback_activations_related_event_id_fkey FOREIGN KEY (related_event_id) REFERENCES public.resilience_events(id) ON DELETE SET NULL;


--
-- Name: feature_flag_audit feature_flag_audit_flag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.feature_flag_audit
    ADD CONSTRAINT feature_flag_audit_flag_id_fkey FOREIGN KEY (flag_id) REFERENCES public.feature_flags(id) ON DELETE CASCADE;


--
-- Name: feature_flag_evaluations feature_flag_evaluations_flag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.feature_flag_evaluations
    ADD CONSTRAINT feature_flag_evaluations_flag_id_fkey FOREIGN KEY (flag_id) REFERENCES public.feature_flags(id) ON DELETE CASCADE;


--
-- Name: absences fk_absence_created_by; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.absences
    ADD CONSTRAINT fk_absence_created_by FOREIGN KEY (created_by_id) REFERENCES public.people(id) ON DELETE SET NULL;


--
-- Name: assignments fk_assignments_schedule_run; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.assignments
    ADD CONSTRAINT fk_assignments_schedule_run FOREIGN KEY (schedule_run_id) REFERENCES public.schedule_runs(id) ON DELETE SET NULL;


--
-- Name: email_logs fk_email_logs_template_id; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.email_logs
    ADD CONSTRAINT fk_email_logs_template_id FOREIGN KEY (template_id) REFERENCES public.email_templates(id) ON DELETE SET NULL;


--
-- Name: email_templates fk_email_templates_created_by_id; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.email_templates
    ADD CONSTRAINT fk_email_templates_created_by_id FOREIGN KEY (created_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: rotation_templates fk_rotation_first_half_component; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.rotation_templates
    ADD CONSTRAINT fk_rotation_first_half_component FOREIGN KEY (first_half_component_id) REFERENCES public.rotation_templates(id) ON DELETE SET NULL;


--
-- Name: rotation_templates fk_rotation_second_half_component; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.rotation_templates
    ADD CONSTRAINT fk_rotation_second_half_component FOREIGN KEY (second_half_component_id) REFERENCES public.rotation_templates(id) ON DELETE SET NULL;


--
-- Name: rotation_templates fk_rotation_template_paired; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.rotation_templates
    ADD CONSTRAINT fk_rotation_template_paired FOREIGN KEY (paired_template_id) REFERENCES public.rotation_templates(id) ON DELETE SET NULL;


--
-- Name: rotation_templates fk_rotation_templates_archived_by_users; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.rotation_templates
    ADD CONSTRAINT fk_rotation_templates_archived_by_users FOREIGN KEY (archived_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: weekly_patterns fk_weekly_patterns_activity_id; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.weekly_patterns
    ADD CONSTRAINT fk_weekly_patterns_activity_id FOREIGN KEY (activity_id) REFERENCES public.activities(id) ON DELETE RESTRICT;


--
-- Name: half_day_assignments half_day_assignments_activity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.half_day_assignments
    ADD CONSTRAINT half_day_assignments_activity_id_fkey FOREIGN KEY (activity_id) REFERENCES public.activities(id) ON DELETE RESTRICT;


--
-- Name: half_day_assignments half_day_assignments_block_assignment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.half_day_assignments
    ADD CONSTRAINT half_day_assignments_block_assignment_id_fkey FOREIGN KEY (block_assignment_id) REFERENCES public.block_assignments(id) ON DELETE SET NULL;


--
-- Name: half_day_assignments half_day_assignments_overridden_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.half_day_assignments
    ADD CONSTRAINT half_day_assignments_overridden_by_fkey FOREIGN KEY (overridden_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: half_day_assignments half_day_assignments_person_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.half_day_assignments
    ADD CONSTRAINT half_day_assignments_person_id_fkey FOREIGN KEY (person_id) REFERENCES public.people(id) ON DELETE CASCADE;


--
-- Name: import_batches import_batches_applied_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.import_batches
    ADD CONSTRAINT import_batches_applied_by_id_fkey FOREIGN KEY (applied_by_id) REFERENCES public.users(id);


--
-- Name: import_batches import_batches_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.import_batches
    ADD CONSTRAINT import_batches_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id);


--
-- Name: import_batches import_batches_rolled_back_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.import_batches
    ADD CONSTRAINT import_batches_rolled_back_by_id_fkey FOREIGN KEY (rolled_back_by_id) REFERENCES public.users(id);


--
-- Name: import_staged_absences import_staged_absences_batch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.import_staged_absences
    ADD CONSTRAINT import_staged_absences_batch_id_fkey FOREIGN KEY (batch_id) REFERENCES public.import_batches(id) ON DELETE CASCADE;


--
-- Name: import_staged_absences import_staged_absences_matched_person_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.import_staged_absences
    ADD CONSTRAINT import_staged_absences_matched_person_id_fkey FOREIGN KEY (matched_person_id) REFERENCES public.people(id);


--
-- Name: import_staged_assignments import_staged_assignments_batch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.import_staged_assignments
    ADD CONSTRAINT import_staged_assignments_batch_id_fkey FOREIGN KEY (batch_id) REFERENCES public.import_batches(id) ON DELETE CASCADE;


--
-- Name: import_staged_assignments import_staged_assignments_matched_person_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.import_staged_assignments
    ADD CONSTRAINT import_staged_assignments_matched_person_id_fkey FOREIGN KEY (matched_person_id) REFERENCES public.people(id);


--
-- Name: import_staged_assignments import_staged_assignments_matched_rotation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.import_staged_assignments
    ADD CONSTRAINT import_staged_assignments_matched_rotation_id_fkey FOREIGN KEY (matched_rotation_id) REFERENCES public.rotation_templates(id);


--
-- Name: inpatient_preloads inpatient_preloads_person_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.inpatient_preloads
    ADD CONSTRAINT inpatient_preloads_person_id_fkey FOREIGN KEY (person_id) REFERENCES public.people(id) ON DELETE CASCADE;


--
-- Name: ip_blacklists ip_blacklists_added_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.ip_blacklists
    ADD CONSTRAINT ip_blacklists_added_by_id_fkey FOREIGN KEY (added_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: ip_whitelists ip_whitelists_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.ip_whitelists
    ADD CONSTRAINT ip_whitelists_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: metric_snapshots metric_snapshots_schedule_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.metric_snapshots
    ADD CONSTRAINT metric_snapshots_schedule_version_id_fkey FOREIGN KEY (schedule_version_id) REFERENCES public.schedule_versions(id) ON DELETE CASCADE;


--
-- Name: notification_preferences notification_preferences_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.notification_preferences
    ADD CONSTRAINT notification_preferences_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.people(id) ON DELETE CASCADE;


--
-- Name: notifications notifications_recipient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_recipient_id_fkey FOREIGN KEY (recipient_id) REFERENCES public.people(id) ON DELETE CASCADE;


--
-- Name: oauth2_clients oauth2_clients_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.oauth2_clients
    ADD CONSTRAINT oauth2_clients_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: person_certifications person_certifications_certification_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.person_certifications
    ADD CONSTRAINT person_certifications_certification_type_id_fkey FOREIGN KEY (certification_type_id) REFERENCES public.certification_types(id) ON DELETE CASCADE;


--
-- Name: person_certifications person_certifications_person_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.person_certifications
    ADD CONSTRAINT person_certifications_person_id_fkey FOREIGN KEY (person_id) REFERENCES public.people(id) ON DELETE CASCADE;


--
-- Name: procedure_credentials procedure_credentials_person_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.procedure_credentials
    ADD CONSTRAINT procedure_credentials_person_id_fkey FOREIGN KEY (person_id) REFERENCES public.people(id) ON DELETE CASCADE;


--
-- Name: procedure_credentials procedure_credentials_procedure_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.procedure_credentials
    ADD CONSTRAINT procedure_credentials_procedure_id_fkey FOREIGN KEY (procedure_id) REFERENCES public.procedures(id) ON DELETE CASCADE;


--
-- Name: request_signatures request_signatures_api_key_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.request_signatures
    ADD CONSTRAINT request_signatures_api_key_id_fkey FOREIGN KEY (api_key_id) REFERENCES public.api_keys(id) ON DELETE CASCADE;


--
-- Name: resident_call_preloads resident_call_preloads_person_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.resident_call_preloads
    ADD CONSTRAINT resident_call_preloads_person_id_fkey FOREIGN KEY (person_id) REFERENCES public.people(id) ON DELETE CASCADE;


--
-- Name: resident_weekly_requirements resident_weekly_requirements_rotation_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.resident_weekly_requirements
    ADD CONSTRAINT resident_weekly_requirements_rotation_template_id_fkey FOREIGN KEY (rotation_template_id) REFERENCES public.rotation_templates(id) ON DELETE CASCADE;


--
-- Name: resilience_events resilience_events_related_health_check_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.resilience_events
    ADD CONSTRAINT resilience_events_related_health_check_id_fkey FOREIGN KEY (related_health_check_id) REFERENCES public.resilience_health_checks(id) ON DELETE SET NULL;


--
-- Name: rotation_activity_requirements rotation_activity_requirements_activity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.rotation_activity_requirements
    ADD CONSTRAINT rotation_activity_requirements_activity_id_fkey FOREIGN KEY (activity_id) REFERENCES public.activities(id) ON DELETE RESTRICT;


--
-- Name: rotation_activity_requirements rotation_activity_requirements_rotation_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.rotation_activity_requirements
    ADD CONSTRAINT rotation_activity_requirements_rotation_template_id_fkey FOREIGN KEY (rotation_template_id) REFERENCES public.rotation_templates(id) ON DELETE CASCADE;


--
-- Name: rotation_halfday_requirements rotation_halfday_requirements_rotation_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.rotation_halfday_requirements
    ADD CONSTRAINT rotation_halfday_requirements_rotation_template_id_fkey FOREIGN KEY (rotation_template_id) REFERENCES public.rotation_templates(id) ON DELETE CASCADE;


--
-- Name: rotation_preferences rotation_preferences_rotation_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.rotation_preferences
    ADD CONSTRAINT rotation_preferences_rotation_template_id_fkey FOREIGN KEY (rotation_template_id) REFERENCES public.rotation_templates(id) ON DELETE CASCADE;


--
-- Name: sacrifice_decisions sacrifice_decisions_related_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.sacrifice_decisions
    ADD CONSTRAINT sacrifice_decisions_related_event_id_fkey FOREIGN KEY (related_event_id) REFERENCES public.resilience_events(id) ON DELETE SET NULL;


--
-- Name: schedule_diffs schedule_diffs_from_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.schedule_diffs
    ADD CONSTRAINT schedule_diffs_from_version_id_fkey FOREIGN KEY (from_version_id) REFERENCES public.schedule_versions(id) ON DELETE CASCADE;


--
-- Name: schedule_diffs schedule_diffs_to_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.schedule_diffs
    ADD CONSTRAINT schedule_diffs_to_version_id_fkey FOREIGN KEY (to_version_id) REFERENCES public.schedule_versions(id) ON DELETE CASCADE;


--
-- Name: schedule_draft_assignments schedule_draft_assignments_draft_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.schedule_draft_assignments
    ADD CONSTRAINT schedule_draft_assignments_draft_id_fkey FOREIGN KEY (draft_id) REFERENCES public.schedule_drafts(id) ON DELETE CASCADE;


--
-- Name: schedule_draft_assignments schedule_draft_assignments_person_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.schedule_draft_assignments
    ADD CONSTRAINT schedule_draft_assignments_person_id_fkey FOREIGN KEY (person_id) REFERENCES public.people(id);


--
-- Name: schedule_draft_assignments schedule_draft_assignments_rotation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.schedule_draft_assignments
    ADD CONSTRAINT schedule_draft_assignments_rotation_id_fkey FOREIGN KEY (rotation_id) REFERENCES public.rotation_templates(id);


--
-- Name: schedule_draft_flags schedule_draft_flags_acknowledged_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.schedule_draft_flags
    ADD CONSTRAINT schedule_draft_flags_acknowledged_by_id_fkey FOREIGN KEY (acknowledged_by_id) REFERENCES public.users(id);


--
-- Name: schedule_draft_flags schedule_draft_flags_assignment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.schedule_draft_flags
    ADD CONSTRAINT schedule_draft_flags_assignment_id_fkey FOREIGN KEY (assignment_id) REFERENCES public.schedule_draft_assignments(id) ON DELETE SET NULL;


--
-- Name: schedule_draft_flags schedule_draft_flags_draft_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.schedule_draft_flags
    ADD CONSTRAINT schedule_draft_flags_draft_id_fkey FOREIGN KEY (draft_id) REFERENCES public.schedule_drafts(id) ON DELETE CASCADE;


--
-- Name: schedule_draft_flags schedule_draft_flags_person_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.schedule_draft_flags
    ADD CONSTRAINT schedule_draft_flags_person_id_fkey FOREIGN KEY (person_id) REFERENCES public.people(id);


--
-- Name: schedule_drafts schedule_drafts_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.schedule_drafts
    ADD CONSTRAINT schedule_drafts_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id);


--
-- Name: schedule_drafts schedule_drafts_override_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.schedule_drafts
    ADD CONSTRAINT schedule_drafts_override_by_id_fkey FOREIGN KEY (override_by_id) REFERENCES public.users(id);


--
-- Name: schedule_drafts schedule_drafts_published_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.schedule_drafts
    ADD CONSTRAINT schedule_drafts_published_by_id_fkey FOREIGN KEY (published_by_id) REFERENCES public.users(id);


--
-- Name: schedule_drafts schedule_drafts_rolled_back_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.schedule_drafts
    ADD CONSTRAINT schedule_drafts_rolled_back_by_id_fkey FOREIGN KEY (rolled_back_by_id) REFERENCES public.users(id);


--
-- Name: schedule_drafts schedule_drafts_source_schedule_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.schedule_drafts
    ADD CONSTRAINT schedule_drafts_source_schedule_run_id_fkey FOREIGN KEY (source_schedule_run_id) REFERENCES public.schedule_runs(id);


--
-- Name: schedule_runs_version schedule_run_version_end_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.schedule_runs_version
    ADD CONSTRAINT schedule_run_version_end_transaction_id_fkey FOREIGN KEY (end_transaction_id) REFERENCES public.transaction(id);


--
-- Name: schedule_runs_version schedule_run_version_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.schedule_runs_version
    ADD CONSTRAINT schedule_run_version_transaction_id_fkey FOREIGN KEY (transaction_id) REFERENCES public.transaction(id);


--
-- Name: schedule_versions schedule_versions_parent_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.schedule_versions
    ADD CONSTRAINT schedule_versions_parent_version_id_fkey FOREIGN KEY (parent_version_id) REFERENCES public.schedule_versions(id) ON DELETE SET NULL;


--
-- Name: schedule_versions schedule_versions_schedule_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.schedule_versions
    ADD CONSTRAINT schedule_versions_schedule_run_id_fkey FOREIGN KEY (schedule_run_id) REFERENCES public.schedule_runs(id) ON DELETE CASCADE;


--
-- Name: scheduled_notifications scheduled_notifications_recipient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.scheduled_notifications
    ADD CONSTRAINT scheduled_notifications_recipient_id_fkey FOREIGN KEY (recipient_id) REFERENCES public.people(id) ON DELETE CASCADE;


--
-- Name: swap_approvals swap_approvals_faculty_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.swap_approvals
    ADD CONSTRAINT swap_approvals_faculty_id_fkey FOREIGN KEY (faculty_id) REFERENCES public.people(id);


--
-- Name: swap_approvals swap_approvals_swap_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.swap_approvals
    ADD CONSTRAINT swap_approvals_swap_id_fkey FOREIGN KEY (swap_id) REFERENCES public.swap_records(id);


--
-- Name: swap_records swap_records_approved_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.swap_records
    ADD CONSTRAINT swap_records_approved_by_id_fkey FOREIGN KEY (approved_by_id) REFERENCES public.users(id);


--
-- Name: swap_records swap_records_executed_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.swap_records
    ADD CONSTRAINT swap_records_executed_by_id_fkey FOREIGN KEY (executed_by_id) REFERENCES public.users(id);


--
-- Name: swap_records swap_records_requested_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.swap_records
    ADD CONSTRAINT swap_records_requested_by_id_fkey FOREIGN KEY (requested_by_id) REFERENCES public.users(id);


--
-- Name: swap_records swap_records_rolled_back_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.swap_records
    ADD CONSTRAINT swap_records_rolled_back_by_id_fkey FOREIGN KEY (rolled_back_by_id) REFERENCES public.users(id);


--
-- Name: swap_records swap_records_source_faculty_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.swap_records
    ADD CONSTRAINT swap_records_source_faculty_id_fkey FOREIGN KEY (source_faculty_id) REFERENCES public.people(id);


--
-- Name: swap_records swap_records_target_faculty_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.swap_records
    ADD CONSTRAINT swap_records_target_faculty_id_fkey FOREIGN KEY (target_faculty_id) REFERENCES public.people(id);


--
-- Name: trail_signals trail_signals_trail_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.trail_signals
    ADD CONSTRAINT trail_signals_trail_id_fkey FOREIGN KEY (trail_id) REFERENCES public.preference_trails(id) ON DELETE CASCADE;


--
-- Name: vulnerability_records vulnerability_records_related_health_check_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.vulnerability_records
    ADD CONSTRAINT vulnerability_records_related_health_check_id_fkey FOREIGN KEY (related_health_check_id) REFERENCES public.resilience_health_checks(id) ON DELETE SET NULL;


--
-- Name: weekly_patterns weekly_patterns_linked_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.weekly_patterns
    ADD CONSTRAINT weekly_patterns_linked_template_id_fkey FOREIGN KEY (linked_template_id) REFERENCES public.rotation_templates(id) ON DELETE SET NULL;


--
-- Name: weekly_patterns weekly_patterns_rotation_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.weekly_patterns
    ADD CONSTRAINT weekly_patterns_rotation_template_id_fkey FOREIGN KEY (rotation_template_id) REFERENCES public.rotation_templates(id) ON DELETE CASCADE;


--
-- Name: zone_borrowing_records zone_borrowing_records_lending_zone_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.zone_borrowing_records
    ADD CONSTRAINT zone_borrowing_records_lending_zone_id_fkey FOREIGN KEY (lending_zone_id) REFERENCES public.scheduling_zones(id) ON DELETE CASCADE;


--
-- Name: zone_borrowing_records zone_borrowing_records_requesting_zone_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.zone_borrowing_records
    ADD CONSTRAINT zone_borrowing_records_requesting_zone_id_fkey FOREIGN KEY (requesting_zone_id) REFERENCES public.scheduling_zones(id) ON DELETE CASCADE;


--
-- Name: zone_faculty_assignments zone_faculty_assignments_zone_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.zone_faculty_assignments
    ADD CONSTRAINT zone_faculty_assignments_zone_id_fkey FOREIGN KEY (zone_id) REFERENCES public.scheduling_zones(id) ON DELETE CASCADE;


--
-- Name: zone_incidents zone_incidents_zone_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: scheduler
--

ALTER TABLE ONLY public.zone_incidents
    ADD CONSTRAINT zone_incidents_zone_id_fkey FOREIGN KEY (zone_id) REFERENCES public.scheduling_zones(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict mM7vwmAXeHpmDeA80fqHWI8IHi9NvkxcCL7etBmmg2ytpKkuag5Mw3D2CO6nG7K
