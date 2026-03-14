--
-- PostgreSQL database dump
--

\restrict UpHG3zmXP5cCveXS6gsH8Oaa22e3MPHmDJc42l7XBlTcetA26gaSEfMBYQVePFF

-- Dumped from database version 17.7 (Homebrew)
-- Dumped by pg_dump version 17.7 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA public IS '';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


--
-- Name: conflictresolutionmode; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.conflictresolutionmode AS ENUM (
    'replace',
    'merge',
    'upsert'
);


--
-- Name: daytype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.daytype AS ENUM (
    'NORMAL',
    'FEDERAL_HOLIDAY',
    'TRAINING_HOLIDAY',
    'MINIMAL_MANNING',
    'EO_CLOSURE',
    'INAUGURATION_DAY'
);


--
-- Name: draft_assignment_change_type; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.draft_assignment_change_type AS ENUM (
    'add',
    'modify',
    'delete'
);


--
-- Name: draft_flag_severity; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.draft_flag_severity AS ENUM (
    'error',
    'warning',
    'info'
);


--
-- Name: draft_flag_type; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.draft_flag_type AS ENUM (
    'conflict',
    'acgme_violation',
    'coverage_gap',
    'manual_review',
    'lock_window_violation',
    'credential_missing'
);


--
-- Name: draft_source_type; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.draft_source_type AS ENUM (
    'solver',
    'manual',
    'swap',
    'import',
    'resilience'
);


--
-- Name: emailstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.emailstatus AS ENUM (
    'queued',
    'sent',
    'failed',
    'bounced'
);


--
-- Name: emailtemplatetype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.emailtemplatetype AS ENUM (
    'schedule_change',
    'swap_notification',
    'certification_expiry',
    'absence_reminder',
    'compliance_alert'
);


--
-- Name: facultypreferencedirection; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.facultypreferencedirection AS ENUM (
    'prefer',
    'avoid'
);


--
-- Name: facultypreferencetype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.facultypreferencetype AS ENUM (
    'clinic',
    'call'
);


--
-- Name: importbatchstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.importbatchstatus AS ENUM (
    'staged',
    'approved',
    'rejected',
    'applied',
    'rolled_back',
    'failed'
);


--
-- Name: institutionaleventscope; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.institutionaleventscope AS ENUM (
    'all',
    'faculty',
    'resident'
);


--
-- Name: institutionaleventtype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.institutionaleventtype AS ENUM (
    'holiday',
    'conference',
    'retreat',
    'training',
    'closure',
    'other'
);


--
-- Name: operationalintent; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.operationalintent AS ENUM (
    'NORMAL',
    'REDUCED_CAPACITY',
    'NON_OPERATIONAL'
);


--
-- Name: overlaptype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.overlaptype AS ENUM (
    'none',
    'partial',
    'exact',
    'contained',
    'contains'
);


--
-- Name: schedule_draft_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.schedule_draft_status AS ENUM (
    'draft',
    'published',
    'rolled_back',
    'discarded'
);


--
-- Name: stagedabsencestatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.stagedabsencestatus AS ENUM (
    'pending',
    'approved',
    'skipped',
    'applied',
    'failed'
);


--
-- Name: stagedassignmentstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.stagedassignmentstatus AS ENUM (
    'pending',
    'approved',
    'skipped',
    'applied',
    'failed'
);


--
-- Name: update_rag_documents_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_rag_documents_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: absence_version; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: absences; Type: TABLE; Schema: public; Owner: -
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
    status character varying(20) NOT NULL,
    reviewed_at timestamp without time zone,
    reviewed_by_id uuid,
    review_notes text,
    CONSTRAINT ck_absences_check_absence_dates CHECK ((end_date >= start_date)),
    CONSTRAINT ck_absences_check_absence_status CHECK (((status)::text = ANY (ARRAY[('pending'::character varying)::text, ('approved'::character varying)::text, ('rejected'::character varying)::text, ('cancelled'::character varying)::text, ('anticipated'::character varying)::text, ('confirmed'::character varying)::text, ('denied'::character varying)::text]))),
    CONSTRAINT ck_absences_check_absence_type CHECK (((absence_type)::text = ANY (ARRAY[('vacation'::character varying)::text, ('deployment'::character varying)::text, ('tdy'::character varying)::text, ('medical'::character varying)::text, ('family_emergency'::character varying)::text, ('conference'::character varying)::text, ('bereavement'::character varying)::text, ('emergency_leave'::character varying)::text, ('sick'::character varying)::text, ('convalescent'::character varying)::text, ('maternity_paternity'::character varying)::text])))
);


--
-- Name: absences_version; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: academic_blocks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.academic_blocks (
    id uuid NOT NULL,
    block_number integer NOT NULL,
    academic_year integer NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    name character varying(50),
    is_orientation boolean NOT NULL,
    is_variable_length boolean NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_academic_blocks_ck_academic_block_date_order CHECK ((end_date >= start_date)),
    CONSTRAINT ck_academic_blocks_ck_academic_block_number_range CHECK (((block_number >= 0) AND (block_number <= 13))),
    CONSTRAINT ck_academic_blocks_ck_academic_year_range CHECK (((academic_year >= 2020) AND (academic_year <= 2100)))
);


--
-- Name: activities; Type: TABLE; Schema: public; Owner: -
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
    capacity_units integer DEFAULT 1 NOT NULL,
    procedure_id uuid
);


--
-- Name: COLUMN activities.provides_supervision; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.activities.provides_supervision IS 'True for supervision activities (AT, PCAT, DO) that count toward supervision ratios';


--
-- Name: activity_log; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: agent_embeddings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.agent_embeddings (
    agent_name character varying NOT NULL,
    embedding public.vector(384) NOT NULL,
    spec_hash character varying NOT NULL,
    capabilities text,
    updated_at timestamp without time zone DEFAULT now()
);


--
-- Name: ai_budget_config; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_budget_config (
    id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    budget_period character varying(50) NOT NULL,
    budget_limit_usd double precision NOT NULL,
    warning_threshold_pct double precision DEFAULT '0.8'::double precision NOT NULL,
    critical_threshold_pct double precision DEFAULT '0.95'::double precision NOT NULL,
    hard_stop boolean DEFAULT true NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    priority_tasks text
);


--
-- Name: ai_budget_config_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ai_budget_config_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: ai_budget_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.ai_budget_config_id_seq OWNED BY public.ai_budget_config.id;


--
-- Name: ai_usage_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_usage_log (
    id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    task_name character varying(255) NOT NULL,
    model_id character varying(100) NOT NULL,
    input_tokens integer DEFAULT 0 NOT NULL,
    output_tokens integer DEFAULT 0 NOT NULL,
    total_tokens integer DEFAULT 0 NOT NULL,
    cost_usd double precision DEFAULT '0'::double precision NOT NULL,
    job_id character varying(255),
    status character varying(50) DEFAULT 'success'::character varying NOT NULL,
    metadata_json text
);


--
-- Name: ai_usage_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ai_usage_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: ai_usage_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.ai_usage_log_id_seq OWNED BY public.ai_usage_log.id;


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(128) NOT NULL
);


--
-- Name: allostasis_records; Type: TABLE; Schema: public; Owner: -
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
    CONSTRAINT ck_allostasis_records_check_allostasis_state CHECK (((allostasis_state IS NULL) OR ((allostasis_state)::text = ANY (ARRAY[('homeostasis'::character varying)::text, ('allostasis'::character varying)::text, ('allostatic_load'::character varying)::text, ('allostatic_overload'::character varying)::text])))),
    CONSTRAINT ck_allostasis_records_check_entity_type CHECK (((entity_type)::text = ANY (ARRAY[('faculty'::character varying)::text, ('system'::character varying)::text])))
);


--
-- Name: annual_rotation_assignments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.annual_rotation_assignments (
    id uuid NOT NULL,
    plan_id uuid NOT NULL,
    person_id uuid NOT NULL,
    block_number integer NOT NULL,
    rotation_name character varying(100) NOT NULL,
    is_fixed boolean DEFAULT false
);


--
-- Name: annual_rotation_plans; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.annual_rotation_plans (
    id uuid NOT NULL,
    academic_year integer NOT NULL,
    name character varying(200) NOT NULL,
    status character varying(20) DEFAULT 'draft'::character varying NOT NULL,
    solver_time_limit double precision DEFAULT '30'::double precision,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    created_by uuid,
    objective_value integer,
    solver_status character varying(50),
    solve_duration_ms integer
);


--
-- Name: api_keys; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: application_settings; Type: TABLE; Schema: public; Owner: -
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
    schedule_lock_date date,
    CONSTRAINT ck_application_settings_check_block_duration CHECK (((default_block_duration_hours >= 1) AND (default_block_duration_hours <= 12))),
    CONSTRAINT ck_application_settings_check_consecutive_days CHECK (((max_consecutive_days >= 1) AND (max_consecutive_days <= 7))),
    CONSTRAINT ck_application_settings_check_days_off CHECK (((min_days_off_per_week >= 1) AND (min_days_off_per_week <= 3))),
    CONSTRAINT ck_application_settings_check_freeze_horizon CHECK (((freeze_horizon_days >= 0) AND (freeze_horizon_days <= 30))),
    CONSTRAINT ck_application_settings_check_freeze_scope CHECK (((freeze_scope)::text = ANY (ARRAY[('none'::character varying)::text, ('non_emergency_only'::character varying)::text, ('all_changes_require_override'::character varying)::text]))),
    CONSTRAINT ck_application_settings_check_scheduling_algorithm CHECK (((scheduling_algorithm)::text = ANY (ARRAY[('greedy'::character varying)::text, ('min_conflicts'::character varying)::text, ('cp_sat'::character varying)::text, ('pulp'::character varying)::text, ('hybrid'::character varying)::text]))),
    CONSTRAINT ck_application_settings_check_work_hours CHECK (((work_hours_per_week >= 40) AND (work_hours_per_week <= 100)))
);


--
-- Name: approval_record; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: assignment_backups; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.assignment_backups (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    draft_assignment_id uuid NOT NULL,
    original_assignment_id uuid,
    backup_type character varying(20) NOT NULL,
    original_data_json jsonb NOT NULL,
    source_table character varying(50) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    restored_at timestamp with time zone,
    restored_by_id uuid,
    CONSTRAINT ck_assignment_backups_ck_assignment_backups_backup_type CHECK (((backup_type)::text = ANY (ARRAY[('MODIFY'::character varying)::text, ('DELETE'::character varying)::text])))
);


--
-- Name: COLUMN assignment_backups.backup_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.assignment_backups.backup_type IS 'MODIFY or DELETE';


--
-- Name: COLUMN assignment_backups.original_data_json; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.assignment_backups.original_data_json IS 'Complete original assignment data for restoration';


--
-- Name: COLUMN assignment_backups.restored_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.assignment_backups.restored_at IS 'When this backup was used for restoration';


--
-- Name: assignments; Type: TABLE; Schema: public; Owner: -
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
    CONSTRAINT ck_assignments_check_role CHECK (((role)::text = ANY (ARRAY[('primary'::character varying)::text, ('supervising'::character varying)::text, ('backup'::character varying)::text])))
);


--
-- Name: assignments_version; Type: TABLE; Schema: public; Owner: -
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
    schedule_run_id uuid,
    schedule_run_id_mod boolean,
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
    updated_at_mod boolean
);


--
-- Name: block_assignments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.block_assignments (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    block_number integer NOT NULL,
    academic_year integer NOT NULL,
    resident_id uuid NOT NULL,
    rotation_template_id uuid,
    assignment_reason character varying(50) DEFAULT 'balanced'::character varying NOT NULL,
    notes text,
    created_by character varying(255),
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    academic_block_id uuid,
    block_half smallint NOT NULL,
    CONSTRAINT ck_block_assignments_check_assignment_reason CHECK (((assignment_reason)::text = ANY (ARRAY[('leave_eligible_match'::character varying)::text, ('coverage_priority'::character varying)::text, ('balanced'::character varying)::text, ('manual'::character varying)::text, ('specialty_match'::character varying)::text]))),
    CONSTRAINT ck_block_assignments_check_block_half_range CHECK ((block_half = ANY (ARRAY[1, 2]))),
    CONSTRAINT ck_block_assignments_check_block_number_range CHECK (((block_number >= 0) AND (block_number <= 13)))
);


--
-- Name: COLUMN block_assignments.block_number; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.block_assignments.block_number IS 'Academic block number (0-13, where 0 is orientation)';


--
-- Name: COLUMN block_assignments.academic_year; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.block_assignments.academic_year IS 'Academic year starting July 1 (e.g., 2025)';


--
-- Name: COLUMN block_assignments.assignment_reason; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.block_assignments.assignment_reason IS 'leave_eligible_match, coverage_priority, balanced, manual, specialty_match';


--
-- Name: blocks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.blocks (
    id uuid NOT NULL,
    date date NOT NULL,
    time_of_day character varying(2) NOT NULL,
    block_number integer NOT NULL,
    is_weekend boolean,
    is_holiday boolean,
    holiday_name character varying(255),
    day_type public.daytype DEFAULT 'NORMAL'::public.daytype NOT NULL,
    operational_intent public.operationalintent DEFAULT 'NORMAL'::public.operationalintent NOT NULL,
    actual_date date,
    CONSTRAINT ck_blocks_check_time_of_day CHECK (((time_of_day)::text = ANY (ARRAY[('AM'::character varying)::text, ('PM'::character varying)::text])))
);


--
-- Name: call_assignments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.call_assignments (
    id uuid NOT NULL,
    date date NOT NULL,
    person_id uuid NOT NULL,
    call_type character varying(50) NOT NULL,
    is_weekend boolean,
    is_holiday boolean,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT ck_call_assignments_check_call_type CHECK (((call_type)::text = ANY (ARRAY[('overnight'::character varying)::text, ('weekend'::character varying)::text, ('backup'::character varying)::text])))
);


--
-- Name: call_overrides; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.call_overrides (
    id uuid NOT NULL,
    call_assignment_id uuid NOT NULL,
    original_person_id uuid,
    replacement_person_id uuid,
    override_type character varying(20) DEFAULT 'coverage'::character varying NOT NULL,
    reason character varying(50),
    notes text,
    effective_date date NOT NULL,
    call_type character varying(50) NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_by_id uuid,
    created_at timestamp without time zone NOT NULL,
    deactivated_at timestamp without time zone,
    deactivated_by_id uuid,
    supersedes_override_id uuid,
    CONSTRAINT ck_call_overrides_ck_call_override_replacement CHECK ((replacement_person_id IS NOT NULL)),
    CONSTRAINT ck_call_overrides_ck_call_override_type CHECK (((override_type)::text = 'coverage'::text))
);


--
-- Name: certification_types; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: chaos_experiments; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: clinic_sessions; Type: TABLE; Schema: public; Owner: -
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
    CONSTRAINT ck_clinic_sessions_check_clinic_type CHECK (((clinic_type)::text = ANY (ARRAY[('family_medicine'::character varying)::text, ('sports_medicine'::character varying)::text, ('pediatrics'::character varying)::text, ('procedures'::character varying)::text]))),
    CONSTRAINT ck_clinic_sessions_check_physician_count CHECK ((physician_count >= 0)),
    CONSTRAINT ck_clinic_sessions_check_screener_count CHECK ((screener_count >= 0)),
    CONSTRAINT ck_clinic_sessions_check_screener_ratio CHECK (((screener_ratio IS NULL) OR (screener_ratio >= (0)::double precision))),
    CONSTRAINT ck_clinic_sessions_check_session_type CHECK (((session_type)::text = ANY (ARRAY[('am'::character varying)::text, ('pm'::character varying)::text]))),
    CONSTRAINT ck_clinic_sessions_check_staffing_status CHECK (((staffing_status)::text = ANY (ARRAY[('optimal'::character varying)::text, ('adequate'::character varying)::text, ('suboptimal'::character varying)::text, ('inadequate'::character varying)::text, ('unstaffed'::character varying)::text])))
);


--
-- Name: cognitive_decisions; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: cognitive_sessions; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: compensation_records; Type: TABLE; Schema: public; Owner: -
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
    CONSTRAINT ck_compensation_records_check_compensation_type CHECK (((compensation_type)::text = ANY (ARRAY[('overtime'::character varying)::text, ('cross_coverage'::character varying)::text, ('deferred_leave'::character varying)::text, ('service_reduction'::character varying)::text, ('efficiency_gain'::character varying)::text, ('backup_activation'::character varying)::text, ('quality_trade'::character varying)::text])))
);


--
-- Name: conflict_alerts; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: constraint_configurations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.constraint_configurations (
    id uuid NOT NULL,
    name character varying(100) NOT NULL,
    enabled boolean DEFAULT true NOT NULL,
    weight double precision DEFAULT '1'::double precision NOT NULL,
    priority character varying(20) DEFAULT '''MEDIUM'''::character varying NOT NULL,
    category character varying(30) NOT NULL,
    description text,
    updated_at timestamp without time zone,
    updated_by character varying(100),
    CONSTRAINT ck_constraint_configurations_check_constraint_priority CHECK (((priority)::text = ANY (ARRAY[('CRITICAL'::character varying)::text, ('HIGH'::character varying)::text, ('MEDIUM'::character varying)::text, ('LOW'::character varying)::text]))),
    CONSTRAINT ck_constraint_configurations_check_constraint_weight_positive CHECK ((weight >= (0)::double precision))
);


--
-- Name: cross_training_recommendations; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: email_logs; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: email_templates; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: equilibrium_shifts; Type: TABLE; Schema: public; Owner: -
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
    CONSTRAINT ck_equilibrium_shifts_check_equilibrium_state CHECK (((equilibrium_state IS NULL) OR ((equilibrium_state)::text = ANY (ARRAY[('stable'::character varying)::text, ('compensating'::character varying)::text, ('stressed'::character varying)::text, ('unsustainable'::character varying)::text, ('critical'::character varying)::text]))))
);


--
-- Name: faculty_activity_permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.faculty_activity_permissions (
    id uuid NOT NULL,
    faculty_role character varying(20) NOT NULL,
    activity_id uuid NOT NULL,
    is_default boolean DEFAULT false NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: COLUMN faculty_activity_permissions.faculty_role; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.faculty_activity_permissions.faculty_role IS 'FacultyRole enum value (pd, apd, oic, dept_chief, sports_med, core, adjunct)';


--
-- Name: COLUMN faculty_activity_permissions.is_default; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.faculty_activity_permissions.is_default IS 'Auto-assign this activity to new templates for this role';


--
-- Name: faculty_centrality; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: faculty_preferences; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: faculty_schedule_preferences; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.faculty_schedule_preferences (
    id uuid NOT NULL,
    person_id uuid NOT NULL,
    preference_type public.facultypreferencetype NOT NULL,
    direction public.facultypreferencedirection NOT NULL,
    rank integer NOT NULL,
    day_of_week integer NOT NULL,
    time_of_day character varying(2),
    weight integer DEFAULT 6 NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    notes character varying(500),
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    CONSTRAINT ck_faculty_schedule_preferences_check_faculty_schedule__172a CHECK (((day_of_week >= 0) AND (day_of_week <= 6))),
    CONSTRAINT ck_faculty_schedule_preferences_check_faculty_schedule__5413 CHECK ((((time_of_day)::text = ANY (ARRAY[('AM'::character varying)::text, ('PM'::character varying)::text])) OR (time_of_day IS NULL))),
    CONSTRAINT ck_faculty_schedule_preferences_check_faculty_schedule__88ad CHECK ((((preference_type = 'clinic'::public.facultypreferencetype) AND (time_of_day IS NOT NULL)) OR ((preference_type = 'call'::public.facultypreferencetype) AND (time_of_day IS NULL)))),
    CONSTRAINT ck_faculty_schedule_preferences_check_faculty_schedule__c020 CHECK ((rank = ANY (ARRAY[1, 2])))
);


--
-- Name: faculty_weekly_overrides; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: COLUMN faculty_weekly_overrides.effective_date; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.faculty_weekly_overrides.effective_date IS 'Week start date (Monday) for this override';


--
-- Name: COLUMN faculty_weekly_overrides.day_of_week; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.faculty_weekly_overrides.day_of_week IS '0=Sunday, 6=Saturday';


--
-- Name: COLUMN faculty_weekly_overrides.time_of_day; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.faculty_weekly_overrides.time_of_day IS 'AM or PM';


--
-- Name: COLUMN faculty_weekly_overrides.activity_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.faculty_weekly_overrides.activity_id IS 'Activity for this override (NULL = clear slot)';


--
-- Name: COLUMN faculty_weekly_overrides.is_locked; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.faculty_weekly_overrides.is_locked IS 'HARD constraint for this specific week';


--
-- Name: COLUMN faculty_weekly_overrides.override_reason; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.faculty_weekly_overrides.override_reason IS 'Why this override was created';


--
-- Name: COLUMN faculty_weekly_overrides.created_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.faculty_weekly_overrides.created_by IS 'Who created this override';


--
-- Name: faculty_weekly_templates; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: COLUMN faculty_weekly_templates.day_of_week; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.faculty_weekly_templates.day_of_week IS '0=Sunday, 6=Saturday';


--
-- Name: COLUMN faculty_weekly_templates.time_of_day; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.faculty_weekly_templates.time_of_day IS 'AM or PM';


--
-- Name: COLUMN faculty_weekly_templates.week_number; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.faculty_weekly_templates.week_number IS 'Week 1-4 within block. NULL = same pattern all weeks';


--
-- Name: COLUMN faculty_weekly_templates.activity_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.faculty_weekly_templates.activity_id IS 'Activity assigned to this slot (NULL = unassigned)';


--
-- Name: COLUMN faculty_weekly_templates.is_locked; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.faculty_weekly_templates.is_locked IS 'HARD constraint - solver cannot change';


--
-- Name: COLUMN faculty_weekly_templates.priority; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.faculty_weekly_templates.priority IS 'Soft preference 0-100 (higher = more important)';


--
-- Name: fallback_activations; Type: TABLE; Schema: public; Owner: -
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
    CONSTRAINT ck_fallback_activations_check_fallback_scenario CHECK (((scenario)::text = ANY (ARRAY[('single_faculty_loss'::character varying)::text, ('double_faculty_loss'::character varying)::text, ('pcs_season_50_percent'::character varying)::text, ('holiday_skeleton'::character varying)::text, ('pandemic_essential'::character varying)::text, ('mass_casualty'::character varying)::text, ('weather_emergency'::character varying)::text])))
);


--
-- Name: feature_flag_audit; Type: TABLE; Schema: public; Owner: -
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
    CONSTRAINT ck_feature_flag_audit_check_audit_action CHECK (((action)::text = ANY (ARRAY[('created'::character varying)::text, ('updated'::character varying)::text, ('deleted'::character varying)::text, ('enabled'::character varying)::text, ('disabled'::character varying)::text])))
);


--
-- Name: feature_flag_evaluations; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: feature_flags; Type: TABLE; Schema: public; Owner: -
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
    CONSTRAINT ck_feature_flags_check_flag_type CHECK (((flag_type)::text = ANY (ARRAY[('boolean'::character varying)::text, ('percentage'::character varying)::text, ('variant'::character varying)::text]))),
    CONSTRAINT ck_feature_flags_check_rollout_percentage_range CHECK (((rollout_percentage IS NULL) OR ((rollout_percentage >= (0.0)::double precision) AND (rollout_percentage <= (1.0)::double precision))))
);


--
-- Name: feedback_loop_states; Type: TABLE; Schema: public; Owner: -
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
    CONSTRAINT ck_feedback_loop_states_check_deviation_severity CHECK (((deviation_severity IS NULL) OR ((deviation_severity)::text = ANY (ARRAY[('none'::character varying)::text, ('minor'::character varying)::text, ('moderate'::character varying)::text, ('major'::character varying)::text, ('critical'::character varying)::text]))))
);


--
-- Name: game_theory_evolution; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.game_theory_evolution (
    id uuid NOT NULL,
    name character varying(200) NOT NULL,
    description text,
    created_at timestamp without time zone NOT NULL,
    created_by character varying(100),
    initial_population_size integer NOT NULL,
    turns_per_interaction integer NOT NULL,
    max_generations integer,
    mutation_rate double precision,
    initial_composition jsonb NOT NULL,
    status character varying(20) NOT NULL,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    error_message text,
    celery_task_id character varying(100),
    generations_completed integer,
    winner_strategy_id uuid,
    winner_strategy_name character varying(100),
    is_evolutionarily_stable boolean,
    population_history jsonb,
    final_population jsonb
);


--
-- Name: game_theory_matches; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.game_theory_matches (
    id uuid NOT NULL,
    tournament_id uuid NOT NULL,
    strategy1_id uuid NOT NULL,
    strategy1_name character varying(100),
    strategy2_id uuid NOT NULL,
    strategy2_name character varying(100),
    score1 double precision NOT NULL,
    score2 double precision NOT NULL,
    cooperation_rate1 double precision,
    cooperation_rate2 double precision,
    actions1 text,
    actions2 text
);


--
-- Name: game_theory_strategies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.game_theory_strategies (
    id uuid NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    strategy_type character varying(30) NOT NULL,
    created_at timestamp without time zone NOT NULL,
    created_by character varying(100),
    utilization_target double precision,
    cross_zone_borrowing boolean,
    sacrifice_willingness character varying(20),
    defense_activation_threshold integer,
    response_timeout_ms integer,
    initial_action character varying(10),
    forgiveness_probability double precision,
    retaliation_memory integer,
    is_stochastic boolean,
    custom_logic jsonb,
    tournaments_participated integer,
    total_matches integer,
    total_wins integer,
    average_score double precision,
    cooperation_rate double precision,
    is_active boolean
);


--
-- Name: game_theory_tournaments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.game_theory_tournaments (
    id uuid NOT NULL,
    name character varying(200) NOT NULL,
    description text,
    created_at timestamp without time zone NOT NULL,
    created_by character varying(100),
    turns_per_match integer NOT NULL,
    repetitions integer NOT NULL,
    noise double precision,
    payoff_cc double precision,
    payoff_cd double precision,
    payoff_dc double precision,
    payoff_dd double precision,
    strategy_ids character varying[],
    status character varying(20) NOT NULL,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    error_message text,
    celery_task_id character varying(100),
    total_matches integer,
    winner_strategy_id uuid,
    winner_strategy_name character varying(100),
    results_json jsonb,
    rankings jsonb,
    payoff_matrix jsonb
);


--
-- Name: game_theory_validations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.game_theory_validations (
    id uuid NOT NULL,
    strategy_id uuid NOT NULL,
    strategy_name character varying(100),
    validated_at timestamp without time zone NOT NULL,
    turns integer,
    repetitions integer,
    passed boolean NOT NULL,
    average_score double precision NOT NULL,
    cooperation_rate double precision NOT NULL,
    pass_threshold double precision,
    assessment character varying(50),
    recommendation text
);


--
-- Name: graduation_requirements; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.graduation_requirements (
    id uuid NOT NULL,
    pgy_level integer NOT NULL,
    rotation_template_id uuid NOT NULL,
    min_halves integer NOT NULL,
    target_halves integer,
    by_date date,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


--
-- Name: half_day_assignments; Type: TABLE; Schema: public; Owner: -
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
    counts_toward_fmc_capacity boolean,
    rotation_template_id uuid,
    CONSTRAINT ck_half_day_assignments_check_half_day_source CHECK (((source)::text = ANY (ARRAY[('preload'::character varying)::text, ('manual'::character varying)::text, ('solver'::character varying)::text, ('template'::character varying)::text]))),
    CONSTRAINT ck_half_day_assignments_check_half_day_time_of_day CHECK (((time_of_day)::text = ANY (ARRAY[('AM'::character varying)::text, ('PM'::character varying)::text])))
);


--
-- Name: COLUMN half_day_assignments.rotation_template_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.half_day_assignments.rotation_template_id IS 'Optional rotation template context for this assignment (enables counting clinic types)';


--
-- Name: hopfield_positions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.hopfield_positions (
    id uuid NOT NULL,
    person_id uuid NOT NULL,
    x_position double precision NOT NULL,
    y_position double precision NOT NULL,
    z_position double precision,
    basin_depth double precision,
    energy_value double precision,
    stability_score double precision,
    nearest_attractor_id character varying(100),
    nearest_attractor_type character varying(50),
    hamming_distance integer,
    confidence integer,
    notes text,
    block_number integer,
    academic_year integer,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_hopfield_positions_check_confidence_range CHECK (((confidence IS NULL) OR ((confidence >= 1) AND (confidence <= 5)))),
    CONSTRAINT ck_hopfield_positions_check_hopfield_block_range CHECK (((block_number IS NULL) OR ((block_number >= 0) AND (block_number <= 13)))),
    CONSTRAINT ck_hopfield_positions_check_x_position_range CHECK (((x_position >= (0)::double precision) AND (x_position <= (1)::double precision))),
    CONSTRAINT ck_hopfield_positions_check_y_position_range CHECK (((y_position >= (0)::double precision) AND (y_position <= (1)::double precision))),
    CONSTRAINT ck_hopfield_positions_check_z_position_range CHECK (((z_position IS NULL) OR ((z_position >= (0)::double precision) AND (z_position <= (1)::double precision))))
);


--
-- Name: hub_protection_plans; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: idempotency_requests; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: import_batches; Type: TABLE; Schema: public; Owner: -
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
    rolled_back_by_id uuid,
    academic_year integer,
    parent_batch_id uuid
);


--
-- Name: import_staged_absences; Type: TABLE; Schema: public; Owner: -
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
    CONSTRAINT ck_import_staged_absences_check_staged_absence_dates CHECK ((end_date >= start_date)),
    CONSTRAINT ck_import_staged_absences_check_staged_absence_type CHECK (((absence_type)::text = ANY (ARRAY[('vacation'::character varying)::text, ('deployment'::character varying)::text, ('tdy'::character varying)::text, ('medical'::character varying)::text, ('family_emergency'::character varying)::text, ('conference'::character varying)::text, ('bereavement'::character varying)::text, ('emergency_leave'::character varying)::text, ('sick'::character varying)::text, ('convalescent'::character varying)::text, ('maternity_paternity'::character varying)::text])))
);


--
-- Name: import_staged_absences_version; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: import_staged_assignments; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: inpatient_preloads; Type: TABLE; Schema: public; Owner: -
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
    CONSTRAINT ck_inpatient_preloads_check_fmit_week_number CHECK (((fmit_week_number IS NULL) OR ((fmit_week_number >= 1) AND (fmit_week_number <= 4)))),
    CONSTRAINT ck_inpatient_preloads_check_inpatient_rotation_type CHECK (((rotation_type)::text = ANY (ARRAY[('FMIT'::character varying)::text, ('NF'::character varying)::text, ('PedW'::character varying)::text, ('PedNF'::character varying)::text, ('KAP'::character varying)::text, ('IM'::character varying)::text, ('LDNF'::character varying)::text]))),
    CONSTRAINT ck_inpatient_preloads_check_preload_assigned_by CHECK (((assigned_by IS NULL) OR ((assigned_by)::text = ANY (ARRAY[('chief'::character varying)::text, ('scheduler'::character varying)::text, ('coordinator'::character varying)::text, ('manual'::character varying)::text])))),
    CONSTRAINT ck_inpatient_preloads_check_preload_dates CHECK ((end_date >= start_date))
);


--
-- Name: institutional_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.institutional_events (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    event_type public.institutionaleventtype NOT NULL,
    applies_to public.institutionaleventscope DEFAULT 'all'::public.institutionaleventscope NOT NULL,
    activity_id uuid,
    start_date date NOT NULL,
    end_date date NOT NULL,
    time_of_day character varying(2),
    applies_to_inpatient boolean DEFAULT false NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    notes text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    CONSTRAINT ck_institutional_events_check_institutional_event_dates CHECK ((end_date >= start_date)),
    CONSTRAINT ck_institutional_events_check_institutional_event_time_of_day CHECK ((((time_of_day)::text = ANY (ARRAY[('AM'::character varying)::text, ('PM'::character varying)::text])) OR (time_of_day IS NULL)))
);


--
-- Name: intern_stagger_patterns; Type: TABLE; Schema: public; Owner: -
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
    CONSTRAINT ck_intern_stagger_patterns_check_min_experience CHECK ((min_intern_a_experience_weeks >= 0)),
    CONSTRAINT ck_intern_stagger_patterns_check_overlap_duration CHECK ((overlap_duration_minutes > 0)),
    CONSTRAINT ck_intern_stagger_patterns_check_overlap_efficiency CHECK (((overlap_efficiency >= 0) AND (overlap_efficiency <= 100)))
);


--
-- Name: ip_blacklists; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: ip_whitelists; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: job_executions; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: learner_assignments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.learner_assignments (
    id uuid NOT NULL,
    learner_id uuid NOT NULL,
    parent_assignment_id uuid,
    block_id uuid NOT NULL,
    activity_type character varying(20) NOT NULL,
    day_of_week integer NOT NULL,
    time_of_day character varying(2) NOT NULL,
    source character varying(20) DEFAULT 'solver'::character varying,
    created_at timestamp without time zone,
    CONSTRAINT ck_learner_assignments_check_learner_activity_type CHECK (((activity_type)::text = ANY (ARRAY[('FMIT'::character varying)::text, ('ASM'::character varying)::text, ('clinic'::character varying)::text, ('procedures'::character varying)::text, ('post_call'::character varying)::text, ('inprocessing'::character varying)::text, ('outprocessing'::character varying)::text, ('didactics'::character varying)::text, ('advising'::character varying)::text]))),
    CONSTRAINT ck_learner_assignments_check_learner_day CHECK (((day_of_week >= 0) AND (day_of_week <= 4))),
    CONSTRAINT ck_learner_assignments_check_learner_time CHECK (((time_of_day)::text = ANY (ARRAY[('AM'::character varying)::text, ('PM'::character varying)::text])))
);


--
-- Name: learner_to_tracks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.learner_to_tracks (
    id uuid NOT NULL,
    learner_id uuid NOT NULL,
    track_id uuid NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    requires_fmit boolean DEFAULT true NOT NULL,
    created_at timestamp without time zone,
    CONSTRAINT ck_learner_to_tracks_check_learner_dates CHECK ((end_date >= start_date))
);


--
-- Name: learner_tracks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.learner_tracks (
    id uuid NOT NULL,
    track_number integer NOT NULL,
    default_fmit_week integer NOT NULL,
    description text,
    CONSTRAINT ck_learner_tracks_check_fmit_week CHECK (((default_fmit_week >= 1) AND (default_fmit_week <= 4))),
    CONSTRAINT ck_learner_tracks_check_track_number CHECK (((track_number >= 1) AND (track_number <= 7)))
);


--
-- Name: metric_snapshots; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.metric_snapshots (
    id uuid NOT NULL,
    schedule_version_id uuid NOT NULL,
    category character varying(20) NOT NULL,
    metric_name character varying(50) NOT NULL,
    value double precision NOT NULL,
    computed_at timestamp without time zone DEFAULT now(),
    methodology_version character varying(20) DEFAULT '''1.0'''::character varying,
    CONSTRAINT ck_metric_snapshots_check_metric_category CHECK (((category)::text = ANY (ARRAY[('fairness'::character varying)::text, ('satisfaction'::character varying)::text, ('stability'::character varying)::text, ('compliance'::character varying)::text, ('resilience'::character varying)::text])))
);


--
-- Name: model_tiers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.model_tiers (
    agent_name character varying NOT NULL,
    default_model character varying NOT NULL,
    updated_at timestamp without time zone DEFAULT now(),
    notes text
);


--
-- Name: COLUMN model_tiers.default_model; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.model_tiers.default_model IS 'Model tier: haiku, sonnet, opus';


--
-- Name: COLUMN model_tiers.notes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.model_tiers.notes IS 'Optional notes about tier selection';


--
-- Name: notification_preferences; Type: TABLE; Schema: public; Owner: -
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
    CONSTRAINT ck_notification_preferences_check_digest_frequency CHECK (((email_digest_frequency)::text = ANY (ARRAY[('daily'::character varying)::text, ('weekly'::character varying)::text]))),
    CONSTRAINT ck_notification_preferences_check_quiet_end CHECK (((quiet_hours_end IS NULL) OR ((quiet_hours_end >= 0) AND (quiet_hours_end <= 23)))),
    CONSTRAINT ck_notification_preferences_check_quiet_start CHECK (((quiet_hours_start IS NULL) OR ((quiet_hours_start >= 0) AND (quiet_hours_start <= 23))))
);


--
-- Name: notifications; Type: TABLE; Schema: public; Owner: -
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
    CONSTRAINT ck_notifications_check_notification_priority CHECK (((priority)::text = ANY (ARRAY[('high'::character varying)::text, ('normal'::character varying)::text, ('low'::character varying)::text])))
);


--
-- Name: oauth2_clients; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: people; Type: TABLE; Schema: public; Owner: -
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
    prefer_full_days boolean DEFAULT true NOT NULL,
    learner_type character varying(10),
    med_school character varying(255),
    ms_year integer,
    rotation_start timestamp without time zone,
    rotation_end timestamp without time zone,
    requires_fmit boolean DEFAULT true,
    CONSTRAINT ck_people_check_faculty_role CHECK (((faculty_role IS NULL) OR ((faculty_role)::text = ANY (ARRAY[('pd'::character varying)::text, ('apd'::character varying)::text, ('oic'::character varying)::text, ('dept_chief'::character varying)::text, ('sports_med'::character varying)::text, ('core'::character varying)::text, ('adjunct'::character varying)::text])))),
    CONSTRAINT ck_people_check_learner_type CHECK (((learner_type IS NULL) OR ((learner_type)::text = ANY (ARRAY[('MS'::character varying)::text, ('TY'::character varying)::text, ('PSYCH'::character varying)::text])))),
    CONSTRAINT ck_people_check_person_type CHECK (((type)::text = ANY (ARRAY[('resident'::character varying)::text, ('faculty'::character varying)::text, ('med_student'::character varying)::text, ('rotating_intern'::character varying)::text]))),
    CONSTRAINT ck_people_check_pgy_level CHECK (((pgy_level IS NULL) OR ((pgy_level >= 1) AND (pgy_level <= 3)))),
    CONSTRAINT ck_people_check_screener_role CHECK (((screener_role IS NULL) OR ((screener_role)::text = ANY (ARRAY[('dedicated'::character varying)::text, ('rn'::character varying)::text, ('emt'::character varying)::text, ('resident'::character varying)::text])))),
    CONSTRAINT ck_people_check_screening_efficiency CHECK (((screening_efficiency IS NULL) OR ((screening_efficiency >= 0) AND (screening_efficiency <= 100))))
);


--
-- Name: COLUMN people.prefer_full_days; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.people.prefer_full_days IS 'If true, solver prefers AM+PM on the same day for clinics instead of scattering them';


--
-- Name: person_academic_years; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.person_academic_years (
    id uuid NOT NULL,
    person_id uuid NOT NULL,
    academic_year integer NOT NULL,
    pgy_level integer,
    is_graduated boolean DEFAULT false NOT NULL,
    clinic_min integer,
    clinic_max integer,
    sunday_call_count integer DEFAULT 0 NOT NULL,
    weekday_call_count integer DEFAULT 0 NOT NULL,
    fmit_weeks_count integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT ck_person_academic_years_check_ay_pgy_level CHECK (((pgy_level IS NULL) OR ((pgy_level >= 1) AND (pgy_level <= 3))))
);


--
-- Name: person_certifications; Type: TABLE; Schema: public; Owner: -
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
    CONSTRAINT ck_person_certifications_check_cert_status CHECK (((status)::text = ANY (ARRAY[('current'::character varying)::text, ('expiring_soon'::character varying)::text, ('expired'::character varying)::text, ('pending'::character varying)::text])))
);


--
-- Name: positive_feedback_alerts; Type: TABLE; Schema: public; Owner: -
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
    CONSTRAINT ck_positive_feedback_alerts_check_urgency CHECK (((urgency IS NULL) OR ((urgency)::text = ANY (ARRAY[('immediate'::character varying)::text, ('soon'::character varying)::text, ('monitor'::character varying)::text]))))
);


--
-- Name: preference_trails; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: procedure_credentials; Type: TABLE; Schema: public; Owner: -
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
    CONSTRAINT ck_procedure_credentials_check_competency_level CHECK (((competency_level)::text = ANY (ARRAY[('trainee'::character varying)::text, ('qualified'::character varying)::text, ('expert'::character varying)::text, ('master'::character varying)::text]))),
    CONSTRAINT ck_procedure_credentials_check_credential_status CHECK (((status)::text = ANY (ARRAY[('active'::character varying)::text, ('expired'::character varying)::text, ('suspended'::character varying)::text, ('pending'::character varying)::text])))
);


--
-- Name: procedures; Type: TABLE; Schema: public; Owner: -
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
    CONSTRAINT ck_procedures_check_complexity_level CHECK (((complexity_level)::text = ANY (ARRAY[('basic'::character varying)::text, ('standard'::character varying)::text, ('advanced'::character varying)::text, ('complex'::character varying)::text]))),
    CONSTRAINT ck_procedures_check_procedure_pgy_level CHECK (((min_pgy_level >= 1) AND (min_pgy_level <= 3))),
    CONSTRAINT ck_procedures_check_supervision_ratio CHECK ((supervision_ratio >= 1))
);


--
-- Name: rag_documents; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: request_signatures; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: resident_call_preloads; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.resident_call_preloads (
    id uuid NOT NULL,
    person_id uuid NOT NULL,
    call_date date NOT NULL,
    call_type character varying(20) NOT NULL,
    assigned_by character varying(20),
    notes character varying(500),
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_resident_call_preloads_check_resident_call_assigned_by CHECK (((assigned_by IS NULL) OR ((assigned_by)::text = ANY (ARRAY[('chief'::character varying)::text, ('scheduler'::character varying)::text])))),
    CONSTRAINT ck_resident_call_preloads_check_resident_call_type CHECK (((call_type)::text = ANY (ARRAY[('ld_24hr'::character varying)::text, ('nf_coverage'::character varying)::text, ('weekend'::character varying)::text])))
);


--
-- Name: resident_weekly_requirements; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: resilience_events; Type: TABLE; Schema: public; Owner: -
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
    CONSTRAINT ck_resilience_events_check_event_type CHECK (((event_type)::text = ANY (ARRAY[('health_check'::character varying)::text, ('crisis_activated'::character varying)::text, ('crisis_deactivated'::character varying)::text, ('fallback_activated'::character varying)::text, ('fallback_deactivated'::character varying)::text, ('load_shedding_activated'::character varying)::text, ('load_shedding_deactivated'::character varying)::text, ('defense_level_changed'::character varying)::text, ('threshold_exceeded'::character varying)::text, ('n1_violation'::character varying)::text, ('n2_violation'::character varying)::text])))
);


--
-- Name: resilience_health_checks; Type: TABLE; Schema: public; Owner: -
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
    CONSTRAINT ck_resilience_health_checks_check_health_status CHECK (((overall_status)::text = ANY (ARRAY[('healthy'::character varying)::text, ('warning'::character varying)::text, ('degraded'::character varying)::text, ('critical'::character varying)::text, ('emergency'::character varying)::text]))),
    CONSTRAINT ck_resilience_health_checks_check_utilization_level CHECK (((utilization_level)::text = ANY (ARRAY[('GREEN'::character varying)::text, ('YELLOW'::character varying)::text, ('ORANGE'::character varying)::text, ('RED'::character varying)::text, ('BLACK'::character varying)::text])))
);


--
-- Name: rotation_activity_requirements; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: rotation_halfday_requirements; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: rotation_preferences; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: COLUMN rotation_preferences.preference_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.rotation_preferences.preference_type IS 'full_day_grouping, consecutive_specialty, avoid_isolated, preferred_days, avoid_friday_pm, balance_weekly';


--
-- Name: COLUMN rotation_preferences.weight; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.rotation_preferences.weight IS 'low, medium, high, required';


--
-- Name: COLUMN rotation_preferences.config_json; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.rotation_preferences.config_json IS 'Type-specific configuration parameters';


--
-- Name: rotation_templates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rotation_templates (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    rotation_type character varying(255) NOT NULL,
    abbreviation character varying(10),
    clinic_location character varying(255),
    max_residents integer,
    requires_specialty character varying(255),
    requires_procedure_credential boolean,
    supervision_required boolean,
    max_supervision_ratio integer,
    created_at timestamp without time zone DEFAULT now(),
    leave_eligible boolean DEFAULT true NOT NULL,
    is_block_half_rotation boolean DEFAULT false NOT NULL,
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


--
-- Name: COLUMN rotation_templates.includes_weekend_work; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.rotation_templates.includes_weekend_work IS 'True if rotation includes weekend assignments';


--
-- Name: sacrifice_decisions; Type: TABLE; Schema: public; Owner: -
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
    CONSTRAINT ck_sacrifice_decisions_check_from_level CHECK (((from_level)::text = ANY (ARRAY[('NORMAL'::character varying)::text, ('YELLOW'::character varying)::text, ('ORANGE'::character varying)::text, ('RED'::character varying)::text, ('BLACK'::character varying)::text, ('CRITICAL'::character varying)::text]))),
    CONSTRAINT ck_sacrifice_decisions_check_to_level CHECK (((to_level)::text = ANY (ARRAY[('NORMAL'::character varying)::text, ('YELLOW'::character varying)::text, ('ORANGE'::character varying)::text, ('RED'::character varying)::text, ('BLACK'::character varying)::text, ('CRITICAL'::character varying)::text])))
);


--
-- Name: schedule_diffs; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: schedule_draft_assignments; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: schedule_draft_flags; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: schedule_drafts; Type: TABLE; Schema: public; Owner: -
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
    override_by_id uuid,
    approved_at timestamp without time zone,
    approved_by_id uuid,
    approval_reason text,
    lock_date_at_approval date
);


--
-- Name: schedule_drafts_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.schedule_drafts_version (
    id uuid NOT NULL,
    created_at timestamp without time zone,
    created_by_id uuid,
    target_block integer,
    target_start_date date,
    target_end_date date,
    status character varying,
    source_type character varying,
    source_schedule_run_id uuid,
    published_at timestamp without time zone,
    published_by_id uuid,
    archived_version_id uuid,
    rollback_available boolean,
    rollback_expires_at timestamp without time zone,
    rolled_back_at timestamp without time zone,
    rolled_back_by_id uuid,
    notes text,
    change_summary json,
    flags_total integer,
    flags_acknowledged integer,
    override_comment text,
    override_by_id uuid,
    approved_at timestamp without time zone,
    approved_by_id uuid,
    approval_reason text,
    lock_date_at_approval date,
    transaction_id bigint NOT NULL,
    operation_type smallint NOT NULL,
    end_transaction_id bigint,
    created_at_mod boolean,
    created_by_id_mod boolean,
    target_block_mod boolean,
    target_start_date_mod boolean,
    target_end_date_mod boolean,
    status_mod boolean,
    source_type_mod boolean,
    source_schedule_run_id_mod boolean,
    published_at_mod boolean,
    published_by_id_mod boolean,
    archived_version_id_mod boolean,
    rollback_available_mod boolean,
    rollback_expires_at_mod boolean,
    rolled_back_at_mod boolean,
    rolled_back_by_id_mod boolean,
    notes_mod boolean,
    change_summary_mod boolean,
    flags_total_mod boolean,
    flags_acknowledged_mod boolean,
    override_comment_mod boolean,
    override_by_id_mod boolean,
    approved_at_mod boolean,
    approved_by_id_mod boolean,
    approval_reason_mod boolean,
    lock_date_at_approval_mod boolean
);


--
-- Name: schedule_grid; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.schedule_grid AS
 SELECT p.id AS person_id,
    p.name,
    p.type AS person_type,
    p.faculty_role,
    p.pgy_level,
    hda.date,
    (EXTRACT(dow FROM hda.date))::integer AS day_of_week,
    (EXTRACT(isodow FROM hda.date))::integer AS iso_day_of_week,
    max((
        CASE
            WHEN ((hda.time_of_day)::text = 'AM'::text) THEN a.code
            ELSE NULL::character varying
        END)::text) AS am_code,
    max((
        CASE
            WHEN ((hda.time_of_day)::text = 'PM'::text) THEN a.code
            ELSE NULL::character varying
        END)::text) AS pm_code,
    max((
        CASE
            WHEN ((hda.time_of_day)::text = 'AM'::text) THEN a.display_abbreviation
            ELSE NULL::character varying
        END)::text) AS am_display,
    max((
        CASE
            WHEN ((hda.time_of_day)::text = 'PM'::text) THEN a.display_abbreviation
            ELSE NULL::character varying
        END)::text) AS pm_display,
    max((
        CASE
            WHEN ((hda.time_of_day)::text = 'AM'::text) THEN hda.source
            ELSE NULL::character varying
        END)::text) AS am_source,
    max((
        CASE
            WHEN ((hda.time_of_day)::text = 'PM'::text) THEN hda.source
            ELSE NULL::character varying
        END)::text) AS pm_source,
    (max(
        CASE
            WHEN ((hda.time_of_day)::text = 'AM'::text) THEN (hda.is_override)::integer
            ELSE NULL::integer
        END))::boolean AS am_override,
    (max(
        CASE
            WHEN ((hda.time_of_day)::text = 'PM'::text) THEN (hda.is_override)::integer
            ELSE NULL::integer
        END))::boolean AS pm_override
   FROM ((public.half_day_assignments hda
     JOIN public.people p ON ((hda.person_id = p.id)))
     LEFT JOIN public.activities a ON ((hda.activity_id = a.id)))
  GROUP BY p.id, p.name, p.type, p.faculty_role, p.pgy_level, hda.date;


--
-- Name: schedule_overrides; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.schedule_overrides (
    id uuid NOT NULL,
    half_day_assignment_id uuid NOT NULL,
    original_person_id uuid,
    replacement_person_id uuid,
    override_type character varying(20) DEFAULT '''coverage'''::character varying NOT NULL,
    reason character varying(50),
    notes text,
    effective_date date NOT NULL,
    time_of_day character varying(2) NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_by_id uuid,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deactivated_at timestamp without time zone,
    deactivated_by_id uuid,
    supersedes_override_id uuid,
    CONSTRAINT ck_schedule_overrides_ck_schedule_override_replacement CHECK (((((override_type)::text = 'coverage'::text) AND (replacement_person_id IS NOT NULL)) OR (((override_type)::text = ANY (ARRAY[('cancellation'::character varying)::text, ('gap'::character varying)::text])) AND (replacement_person_id IS NULL)))),
    CONSTRAINT ck_schedule_overrides_ck_schedule_override_time_of_day CHECK (((time_of_day)::text = ANY (ARRAY[('AM'::character varying)::text, ('PM'::character varying)::text]))),
    CONSTRAINT ck_schedule_overrides_ck_schedule_override_type CHECK (((override_type)::text = ANY (ARRAY[('coverage'::character varying)::text, ('cancellation'::character varying)::text, ('gap'::character varying)::text])))
);


--
-- Name: schedule_runs; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: schedule_runs_version; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: schedule_versions; Type: TABLE; Schema: public; Owner: -
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
    CONSTRAINT ck_schedule_versions_check_trigger_type CHECK (((trigger_type)::text = ANY (ARRAY[('generation'::character varying)::text, ('swap'::character varying)::text, ('absence'::character varying)::text, ('manual_edit'::character varying)::text, ('auto_rebalance'::character varying)::text])))
);


--
-- Name: scheduled_jobs; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: scheduled_notifications; Type: TABLE; Schema: public; Owner: -
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
    CONSTRAINT ck_scheduled_notifications_check_scheduled_status CHECK (((status)::text = ANY (ARRAY[('pending'::character varying)::text, ('processing'::character varying)::text, ('sent'::character varying)::text, ('failed'::character varying)::text, ('cancelled'::character varying)::text])))
);


--
-- Name: scheduling_zones; Type: TABLE; Schema: public; Owner: -
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
    CONSTRAINT ck_scheduling_zones_check_containment_level CHECK (((containment_level)::text = ANY (ARRAY[('none'::character varying)::text, ('soft'::character varying)::text, ('moderate'::character varying)::text, ('strict'::character varying)::text, ('lockdown'::character varying)::text]))),
    CONSTRAINT ck_scheduling_zones_check_zone_status CHECK (((status)::text = ANY (ARRAY[('green'::character varying)::text, ('yellow'::character varying)::text, ('orange'::character varying)::text, ('red'::character varying)::text, ('black'::character varying)::text]))),
    CONSTRAINT ck_scheduling_zones_check_zone_type CHECK (((zone_type)::text = ANY (ARRAY[('inpatient'::character varying)::text, ('outpatient'::character varying)::text, ('education'::character varying)::text, ('research'::character varying)::text, ('admin'::character varying)::text, ('on_call'::character varying)::text])))
);


--
-- Name: survey_availability; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.survey_availability (
    id uuid NOT NULL,
    person_id uuid NOT NULL,
    survey_id uuid NOT NULL,
    last_completed_at timestamp without time zone,
    next_available_at timestamp without time zone,
    completions_this_block integer,
    completions_this_year integer,
    current_block_number integer,
    current_academic_year integer,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: survey_responses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.survey_responses (
    id uuid NOT NULL,
    survey_id uuid NOT NULL,
    person_id uuid,
    block_number integer,
    academic_year integer,
    response_data json NOT NULL,
    score double precision,
    score_interpretation character varying(100),
    submitted_at timestamp without time zone DEFAULT now() NOT NULL,
    ip_address character varying(45),
    user_agent character varying(500),
    algorithm_snapshot_json json,
    CONSTRAINT ck_survey_responses_check_academic_year_range CHECK (((academic_year IS NULL) OR ((academic_year >= 2000) AND (academic_year <= 2100)))),
    CONSTRAINT ck_survey_responses_check_block_number_range CHECK (((block_number IS NULL) OR ((block_number >= 0) AND (block_number <= 13))))
);


--
-- Name: surveys; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.surveys (
    id uuid NOT NULL,
    name character varying(50) NOT NULL,
    display_name character varying(200) NOT NULL,
    survey_type character varying(50) NOT NULL,
    description text,
    instructions text,
    questions_json json NOT NULL,
    scoring_json json,
    points_value integer NOT NULL,
    estimated_seconds integer,
    frequency character varying(20) NOT NULL,
    is_active boolean NOT NULL,
    target_roles_json json,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_surveys_check_points_non_negative CHECK ((points_value >= 0)),
    CONSTRAINT ck_surveys_check_survey_frequency CHECK (((frequency)::text = ANY (ARRAY[('daily'::character varying)::text, ('weekly'::character varying)::text, ('biweekly'::character varying)::text, ('block'::character varying)::text, ('annual'::character varying)::text]))),
    CONSTRAINT ck_surveys_check_survey_type CHECK (((survey_type)::text = ANY (ARRAY[('burnout'::character varying)::text, ('stress'::character varying)::text, ('sleep'::character varying)::text, ('efficacy'::character varying)::text, ('pulse'::character varying)::text, ('hopfield'::character varying)::text, ('custom'::character varying)::text])))
);


--
-- Name: swap_approvals; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: swap_records; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: system_stress_records; Type: TABLE; Schema: public; Owner: -
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
    CONSTRAINT ck_system_stress_records_check_stress_type CHECK (((stress_type)::text = ANY (ARRAY[('faculty_loss'::character varying)::text, ('demand_surge'::character varying)::text, ('quality_pressure'::character varying)::text, ('time_compression'::character varying)::text, ('resource_scarcity'::character varying)::text, ('external_pressure'::character varying)::text])))
);


--
-- Name: task_history; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: task_history_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.task_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: task_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.task_history_id_seq OWNED BY public.task_history.id;


--
-- Name: token_blacklist; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: trail_signals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.trail_signals (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    trail_id uuid NOT NULL,
    signal_type character varying(50) NOT NULL,
    strength_change double precision NOT NULL,
    recorded_at timestamp with time zone DEFAULT now()
);


--
-- Name: transaction; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transaction (
    id bigint NOT NULL,
    issued_at timestamp without time zone DEFAULT now(),
    user_id character varying(255),
    remote_addr character varying(50)
);


--
-- Name: transaction_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.transaction_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: transaction_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.transaction_id_seq OWNED BY public.transaction.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
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
    person_id uuid,
    CONSTRAINT ck_users_check_user_role CHECK (((role)::text = ANY (ARRAY[('admin'::character varying)::text, ('coordinator'::character varying)::text, ('faculty'::character varying)::text, ('clinical_staff'::character varying)::text, ('rn'::character varying)::text, ('lpn'::character varying)::text, ('msa'::character varying)::text, ('resident'::character varying)::text])))
);


--
-- Name: COLUMN users.person_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.users.person_id IS 'Optional link to a Person record (faculty or resident)';


--
-- Name: users_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users_version (
    id uuid NOT NULL,
    username character varying(100),
    email character varying(255),
    hashed_password character varying(255),
    role character varying(50),
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    last_login timestamp without time zone,
    username_mod boolean,
    email_mod boolean,
    hashed_password_mod boolean,
    role_mod boolean,
    is_active_mod boolean,
    created_at_mod boolean,
    updated_at_mod boolean,
    last_login_mod boolean,
    transaction_id bigint NOT NULL,
    operation_type smallint NOT NULL,
    end_transaction_id bigint
);


--
-- Name: v_absence_summary; Type: VIEW; Schema: public; Owner: -
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


--
-- Name: v_block_absences; Type: VIEW; Schema: public; Owner: -
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


--
-- Name: v_current_absences; Type: VIEW; Schema: public; Owner: -
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


--
-- Name: v_tdy_rotation_days; Type: VIEW; Schema: public; Owner: -
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


--
-- Name: vulnerability_records; Type: TABLE; Schema: public; Owner: -
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
    CONSTRAINT ck_vulnerability_records_check_phase_risk CHECK (((phase_transition_risk)::text = ANY (ARRAY[('low'::character varying)::text, ('medium'::character varying)::text, ('high'::character varying)::text, ('critical'::character varying)::text])))
);


--
-- Name: weekly_patterns; Type: TABLE; Schema: public; Owner: -
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
    activity_id uuid NOT NULL
);


--
-- Name: COLUMN weekly_patterns.day_of_week; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.weekly_patterns.day_of_week IS '0=Sunday, 1=Monday, ..., 6=Saturday';


--
-- Name: COLUMN weekly_patterns.time_of_day; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.weekly_patterns.time_of_day IS 'AM or PM';


--
-- Name: COLUMN weekly_patterns.activity_type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.weekly_patterns.activity_type IS 'fm_clinic, specialty, elective, conference, inpatient, call, procedure, off';


--
-- Name: COLUMN weekly_patterns.linked_template_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.weekly_patterns.linked_template_id IS 'Optional link to specific activity template';


--
-- Name: COLUMN weekly_patterns.is_protected; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.weekly_patterns.is_protected IS 'True for slots that cannot be changed (e.g., Wed AM conference)';


--
-- Name: COLUMN weekly_patterns.week_number; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.weekly_patterns.week_number IS 'Week 1-4 within the block. NULL = same pattern all weeks';


--
-- Name: COLUMN weekly_patterns.activity_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.weekly_patterns.activity_id IS 'FK to activities table - the activity assigned to this slot';


--
-- Name: wellness_accounts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.wellness_accounts (
    id uuid NOT NULL,
    person_id uuid NOT NULL,
    points_balance integer NOT NULL,
    points_lifetime integer NOT NULL,
    points_spent integer NOT NULL,
    current_streak_weeks integer NOT NULL,
    longest_streak_weeks integer NOT NULL,
    last_activity_date date,
    streak_start_date date,
    achievements_json json,
    achievements_earned_at_json json,
    leaderboard_opt_in boolean NOT NULL,
    display_name character varying(50),
    research_consent boolean NOT NULL,
    consent_date timestamp without time zone,
    consent_version character varying(20),
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_wellness_accounts_check_streak_non_negative CHECK ((current_streak_weeks >= 0)),
    CONSTRAINT ck_wellness_accounts_check_wellness_lifetime_non_negative CHECK ((points_lifetime >= 0)),
    CONSTRAINT ck_wellness_accounts_check_wellness_points_non_negative CHECK ((points_balance >= 0))
);


--
-- Name: wellness_leaderboard_snapshots; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.wellness_leaderboard_snapshots (
    id uuid NOT NULL,
    snapshot_date date NOT NULL,
    snapshot_type character varying(20) NOT NULL,
    rankings_json json NOT NULL,
    total_participants integer NOT NULL,
    average_points double precision,
    median_points double precision,
    top_10_cutoff integer,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_wellness_leaderboard_snapshots_check_snapshot_type CHECK (((snapshot_type)::text = ANY (ARRAY[('daily'::character varying)::text, ('weekly'::character varying)::text, ('block'::character varying)::text])))
);


--
-- Name: wellness_point_transactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.wellness_point_transactions (
    id uuid NOT NULL,
    account_id uuid NOT NULL,
    points integer NOT NULL,
    balance_after integer NOT NULL,
    transaction_type character varying(50) NOT NULL,
    source character varying(200) NOT NULL,
    survey_response_id uuid,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_wellness_point_transactions_check_transaction_type CHECK (((transaction_type)::text = ANY (ARRAY[('survey'::character varying)::text, ('streak'::character varying)::text, ('achievement'::character varying)::text, ('block_bonus'::character varying)::text, ('admin'::character varying)::text, ('redemption'::character varying)::text])))
);


--
-- Name: zone_borrowing_records; Type: TABLE; Schema: public; Owner: -
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
    CONSTRAINT ck_zone_borrowing_records_check_borrowing_priority CHECK (((priority)::text = ANY (ARRAY[('critical'::character varying)::text, ('high'::character varying)::text, ('medium'::character varying)::text, ('low'::character varying)::text]))),
    CONSTRAINT ck_zone_borrowing_records_check_borrowing_status CHECK (((status)::text = ANY (ARRAY[('pending'::character varying)::text, ('approved'::character varying)::text, ('denied'::character varying)::text, ('completed'::character varying)::text])))
);


--
-- Name: zone_faculty_assignments; Type: TABLE; Schema: public; Owner: -
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
    CONSTRAINT ck_zone_faculty_assignments_check_faculty_role CHECK (((role)::text = ANY (ARRAY[('primary'::character varying)::text, ('secondary'::character varying)::text, ('backup'::character varying)::text])))
);


--
-- Name: zone_incidents; Type: TABLE; Schema: public; Owner: -
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
    CONSTRAINT ck_zone_incidents_check_incident_severity CHECK (((severity)::text = ANY (ARRAY[('minor'::character varying)::text, ('moderate'::character varying)::text, ('severe'::character varying)::text, ('critical'::character varying)::text])))
);


--
-- Name: ai_budget_config id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_budget_config ALTER COLUMN id SET DEFAULT nextval('public.ai_budget_config_id_seq'::regclass);


--
-- Name: ai_usage_log id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_usage_log ALTER COLUMN id SET DEFAULT nextval('public.ai_usage_log_id_seq'::regclass);


--
-- Name: task_history id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task_history ALTER COLUMN id SET DEFAULT nextval('public.task_history_id_seq'::regclass);


--
-- Name: transaction id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transaction ALTER COLUMN id SET DEFAULT nextval('public.transaction_id_seq'::regclass);


--
-- Name: absences_version absences_version_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.absences_version
    ADD CONSTRAINT absences_version_pkey PRIMARY KEY (id, transaction_id);


--
-- Name: agent_embeddings agent_embeddings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agent_embeddings
    ADD CONSTRAINT agent_embeddings_pkey PRIMARY KEY (agent_name);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: api_keys api_keys_key_hash_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_keys
    ADD CONSTRAINT api_keys_key_hash_key UNIQUE (key_hash);


--
-- Name: certification_types certification_types_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.certification_types
    ADD CONSTRAINT certification_types_name_key UNIQUE (name);


--
-- Name: email_templates email_templates_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.email_templates
    ADD CONSTRAINT email_templates_name_key UNIQUE (name);


--
-- Name: faculty_preferences faculty_preferences_faculty_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.faculty_preferences
    ADD CONSTRAINT faculty_preferences_faculty_id_key UNIQUE (faculty_id);


--
-- Name: intern_stagger_patterns intern_stagger_patterns_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.intern_stagger_patterns
    ADD CONSTRAINT intern_stagger_patterns_name_key UNIQUE (name);


--
-- Name: notification_preferences notification_preferences_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notification_preferences
    ADD CONSTRAINT notification_preferences_user_id_key UNIQUE (user_id);


--
-- Name: oauth2_clients oauth2_clients_client_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.oauth2_clients
    ADD CONSTRAINT oauth2_clients_client_id_key UNIQUE (client_id);


--
-- Name: people people_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.people
    ADD CONSTRAINT people_email_key UNIQUE (email);


--
-- Name: absence_version pk_absence_version; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.absence_version
    ADD CONSTRAINT pk_absence_version PRIMARY KEY (id, transaction_id);


--
-- Name: absences pk_absences; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.absences
    ADD CONSTRAINT pk_absences PRIMARY KEY (id);


--
-- Name: academic_blocks pk_academic_blocks; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.academic_blocks
    ADD CONSTRAINT pk_academic_blocks PRIMARY KEY (id);


--
-- Name: activities pk_activities; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activities
    ADD CONSTRAINT pk_activities PRIMARY KEY (id);


--
-- Name: activity_log pk_activity_log; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activity_log
    ADD CONSTRAINT pk_activity_log PRIMARY KEY (id);


--
-- Name: ai_budget_config pk_ai_budget_config; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_budget_config
    ADD CONSTRAINT pk_ai_budget_config PRIMARY KEY (id);


--
-- Name: ai_usage_log pk_ai_usage_log; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_usage_log
    ADD CONSTRAINT pk_ai_usage_log PRIMARY KEY (id);


--
-- Name: allostasis_records pk_allostasis_records; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.allostasis_records
    ADD CONSTRAINT pk_allostasis_records PRIMARY KEY (id);


--
-- Name: annual_rotation_assignments pk_annual_rotation_assignments; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.annual_rotation_assignments
    ADD CONSTRAINT pk_annual_rotation_assignments PRIMARY KEY (id);


--
-- Name: annual_rotation_plans pk_annual_rotation_plans; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.annual_rotation_plans
    ADD CONSTRAINT pk_annual_rotation_plans PRIMARY KEY (id);


--
-- Name: api_keys pk_api_keys; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_keys
    ADD CONSTRAINT pk_api_keys PRIMARY KEY (id);


--
-- Name: application_settings pk_application_settings; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.application_settings
    ADD CONSTRAINT pk_application_settings PRIMARY KEY (id);


--
-- Name: approval_record pk_approval_record; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_record
    ADD CONSTRAINT pk_approval_record PRIMARY KEY (id);


--
-- Name: assignment_backups pk_assignment_backups; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.assignment_backups
    ADD CONSTRAINT pk_assignment_backups PRIMARY KEY (id);


--
-- Name: assignments_version pk_assignment_version; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.assignments_version
    ADD CONSTRAINT pk_assignment_version PRIMARY KEY (id, transaction_id);


--
-- Name: assignments pk_assignments; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.assignments
    ADD CONSTRAINT pk_assignments PRIMARY KEY (id);


--
-- Name: block_assignments pk_block_assignments; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.block_assignments
    ADD CONSTRAINT pk_block_assignments PRIMARY KEY (id);


--
-- Name: blocks pk_blocks; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.blocks
    ADD CONSTRAINT pk_blocks PRIMARY KEY (id);


--
-- Name: call_assignments pk_call_assignments; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.call_assignments
    ADD CONSTRAINT pk_call_assignments PRIMARY KEY (id);


--
-- Name: call_overrides pk_call_overrides; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.call_overrides
    ADD CONSTRAINT pk_call_overrides PRIMARY KEY (id);


--
-- Name: certification_types pk_certification_types; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.certification_types
    ADD CONSTRAINT pk_certification_types PRIMARY KEY (id);


--
-- Name: chaos_experiments pk_chaos_experiments; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chaos_experiments
    ADD CONSTRAINT pk_chaos_experiments PRIMARY KEY (id);


--
-- Name: clinic_sessions pk_clinic_sessions; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.clinic_sessions
    ADD CONSTRAINT pk_clinic_sessions PRIMARY KEY (id);


--
-- Name: cognitive_decisions pk_cognitive_decisions; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cognitive_decisions
    ADD CONSTRAINT pk_cognitive_decisions PRIMARY KEY (id);


--
-- Name: cognitive_sessions pk_cognitive_sessions; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cognitive_sessions
    ADD CONSTRAINT pk_cognitive_sessions PRIMARY KEY (id);


--
-- Name: compensation_records pk_compensation_records; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.compensation_records
    ADD CONSTRAINT pk_compensation_records PRIMARY KEY (id);


--
-- Name: conflict_alerts pk_conflict_alerts; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conflict_alerts
    ADD CONSTRAINT pk_conflict_alerts PRIMARY KEY (id);


--
-- Name: constraint_configurations pk_constraint_configurations; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.constraint_configurations
    ADD CONSTRAINT pk_constraint_configurations PRIMARY KEY (id);


--
-- Name: cross_training_recommendations pk_cross_training_recommendations; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cross_training_recommendations
    ADD CONSTRAINT pk_cross_training_recommendations PRIMARY KEY (id);


--
-- Name: email_logs pk_email_logs; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.email_logs
    ADD CONSTRAINT pk_email_logs PRIMARY KEY (id);


--
-- Name: email_templates pk_email_templates; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.email_templates
    ADD CONSTRAINT pk_email_templates PRIMARY KEY (id);


--
-- Name: equilibrium_shifts pk_equilibrium_shifts; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.equilibrium_shifts
    ADD CONSTRAINT pk_equilibrium_shifts PRIMARY KEY (id);


--
-- Name: faculty_activity_permissions pk_faculty_activity_permissions; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.faculty_activity_permissions
    ADD CONSTRAINT pk_faculty_activity_permissions PRIMARY KEY (id);


--
-- Name: faculty_centrality pk_faculty_centrality; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.faculty_centrality
    ADD CONSTRAINT pk_faculty_centrality PRIMARY KEY (id);


--
-- Name: faculty_preferences pk_faculty_preferences; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.faculty_preferences
    ADD CONSTRAINT pk_faculty_preferences PRIMARY KEY (id);


--
-- Name: faculty_schedule_preferences pk_faculty_schedule_preferences; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.faculty_schedule_preferences
    ADD CONSTRAINT pk_faculty_schedule_preferences PRIMARY KEY (id);


--
-- Name: faculty_weekly_overrides pk_faculty_weekly_overrides; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.faculty_weekly_overrides
    ADD CONSTRAINT pk_faculty_weekly_overrides PRIMARY KEY (id);


--
-- Name: faculty_weekly_templates pk_faculty_weekly_templates; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.faculty_weekly_templates
    ADD CONSTRAINT pk_faculty_weekly_templates PRIMARY KEY (id);


--
-- Name: fallback_activations pk_fallback_activations; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fallback_activations
    ADD CONSTRAINT pk_fallback_activations PRIMARY KEY (id);


--
-- Name: feature_flag_audit pk_feature_flag_audit; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feature_flag_audit
    ADD CONSTRAINT pk_feature_flag_audit PRIMARY KEY (id);


--
-- Name: feature_flag_evaluations pk_feature_flag_evaluations; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feature_flag_evaluations
    ADD CONSTRAINT pk_feature_flag_evaluations PRIMARY KEY (id);


--
-- Name: feature_flags pk_feature_flags; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feature_flags
    ADD CONSTRAINT pk_feature_flags PRIMARY KEY (id);


--
-- Name: feedback_loop_states pk_feedback_loop_states; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback_loop_states
    ADD CONSTRAINT pk_feedback_loop_states PRIMARY KEY (id);


--
-- Name: game_theory_evolution pk_game_theory_evolution; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game_theory_evolution
    ADD CONSTRAINT pk_game_theory_evolution PRIMARY KEY (id);


--
-- Name: game_theory_matches pk_game_theory_matches; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game_theory_matches
    ADD CONSTRAINT pk_game_theory_matches PRIMARY KEY (id);


--
-- Name: game_theory_strategies pk_game_theory_strategies; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game_theory_strategies
    ADD CONSTRAINT pk_game_theory_strategies PRIMARY KEY (id);


--
-- Name: game_theory_tournaments pk_game_theory_tournaments; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game_theory_tournaments
    ADD CONSTRAINT pk_game_theory_tournaments PRIMARY KEY (id);


--
-- Name: game_theory_validations pk_game_theory_validations; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game_theory_validations
    ADD CONSTRAINT pk_game_theory_validations PRIMARY KEY (id);


--
-- Name: graduation_requirements pk_graduation_requirements; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.graduation_requirements
    ADD CONSTRAINT pk_graduation_requirements PRIMARY KEY (id);


--
-- Name: half_day_assignments pk_half_day_assignments; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.half_day_assignments
    ADD CONSTRAINT pk_half_day_assignments PRIMARY KEY (id);


--
-- Name: hopfield_positions pk_hopfield_positions; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hopfield_positions
    ADD CONSTRAINT pk_hopfield_positions PRIMARY KEY (id);


--
-- Name: hub_protection_plans pk_hub_protection_plans; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hub_protection_plans
    ADD CONSTRAINT pk_hub_protection_plans PRIMARY KEY (id);


--
-- Name: idempotency_requests pk_idempotency_requests; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.idempotency_requests
    ADD CONSTRAINT pk_idempotency_requests PRIMARY KEY (id);


--
-- Name: import_batches pk_import_batches; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.import_batches
    ADD CONSTRAINT pk_import_batches PRIMARY KEY (id);


--
-- Name: import_staged_absences pk_import_staged_absences; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.import_staged_absences
    ADD CONSTRAINT pk_import_staged_absences PRIMARY KEY (id);


--
-- Name: import_staged_absences_version pk_import_staged_absences_version; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.import_staged_absences_version
    ADD CONSTRAINT pk_import_staged_absences_version PRIMARY KEY (id, transaction_id);


--
-- Name: import_staged_assignments pk_import_staged_assignments; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.import_staged_assignments
    ADD CONSTRAINT pk_import_staged_assignments PRIMARY KEY (id);


--
-- Name: inpatient_preloads pk_inpatient_preloads; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inpatient_preloads
    ADD CONSTRAINT pk_inpatient_preloads PRIMARY KEY (id);


--
-- Name: institutional_events pk_institutional_events; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.institutional_events
    ADD CONSTRAINT pk_institutional_events PRIMARY KEY (id);


--
-- Name: intern_stagger_patterns pk_intern_stagger_patterns; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.intern_stagger_patterns
    ADD CONSTRAINT pk_intern_stagger_patterns PRIMARY KEY (id);


--
-- Name: ip_blacklists pk_ip_blacklists; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ip_blacklists
    ADD CONSTRAINT pk_ip_blacklists PRIMARY KEY (id);


--
-- Name: ip_whitelists pk_ip_whitelists; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ip_whitelists
    ADD CONSTRAINT pk_ip_whitelists PRIMARY KEY (id);


--
-- Name: job_executions pk_job_executions; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.job_executions
    ADD CONSTRAINT pk_job_executions PRIMARY KEY (id);


--
-- Name: learner_assignments pk_learner_assignments; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learner_assignments
    ADD CONSTRAINT pk_learner_assignments PRIMARY KEY (id);


--
-- Name: learner_to_tracks pk_learner_to_tracks; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learner_to_tracks
    ADD CONSTRAINT pk_learner_to_tracks PRIMARY KEY (id);


--
-- Name: learner_tracks pk_learner_tracks; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learner_tracks
    ADD CONSTRAINT pk_learner_tracks PRIMARY KEY (id);


--
-- Name: metric_snapshots pk_metric_snapshots; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metric_snapshots
    ADD CONSTRAINT pk_metric_snapshots PRIMARY KEY (id);


--
-- Name: model_tiers pk_model_tiers; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_tiers
    ADD CONSTRAINT pk_model_tiers PRIMARY KEY (agent_name);


--
-- Name: notification_preferences pk_notification_preferences; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notification_preferences
    ADD CONSTRAINT pk_notification_preferences PRIMARY KEY (id);


--
-- Name: notifications pk_notifications; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT pk_notifications PRIMARY KEY (id);


--
-- Name: oauth2_clients pk_oauth2_clients; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.oauth2_clients
    ADD CONSTRAINT pk_oauth2_clients PRIMARY KEY (id);


--
-- Name: people pk_people; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.people
    ADD CONSTRAINT pk_people PRIMARY KEY (id);


--
-- Name: person_academic_years pk_person_academic_years; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.person_academic_years
    ADD CONSTRAINT pk_person_academic_years PRIMARY KEY (id);


--
-- Name: person_certifications pk_person_certifications; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.person_certifications
    ADD CONSTRAINT pk_person_certifications PRIMARY KEY (id);


--
-- Name: positive_feedback_alerts pk_positive_feedback_alerts; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.positive_feedback_alerts
    ADD CONSTRAINT pk_positive_feedback_alerts PRIMARY KEY (id);


--
-- Name: preference_trails pk_preference_trails; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.preference_trails
    ADD CONSTRAINT pk_preference_trails PRIMARY KEY (id);


--
-- Name: procedure_credentials pk_procedure_credentials; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.procedure_credentials
    ADD CONSTRAINT pk_procedure_credentials PRIMARY KEY (id);


--
-- Name: procedures pk_procedures; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.procedures
    ADD CONSTRAINT pk_procedures PRIMARY KEY (id);


--
-- Name: request_signatures pk_request_signatures; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.request_signatures
    ADD CONSTRAINT pk_request_signatures PRIMARY KEY (id);


--
-- Name: resident_call_preloads pk_resident_call_preloads; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resident_call_preloads
    ADD CONSTRAINT pk_resident_call_preloads PRIMARY KEY (id);


--
-- Name: resident_weekly_requirements pk_resident_weekly_requirements; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resident_weekly_requirements
    ADD CONSTRAINT pk_resident_weekly_requirements PRIMARY KEY (id);


--
-- Name: resilience_events pk_resilience_events; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resilience_events
    ADD CONSTRAINT pk_resilience_events PRIMARY KEY (id);


--
-- Name: resilience_health_checks pk_resilience_health_checks; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resilience_health_checks
    ADD CONSTRAINT pk_resilience_health_checks PRIMARY KEY (id);


--
-- Name: rotation_activity_requirements pk_rotation_activity_requirements; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rotation_activity_requirements
    ADD CONSTRAINT pk_rotation_activity_requirements PRIMARY KEY (id);


--
-- Name: rotation_halfday_requirements pk_rotation_halfday_requirements; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rotation_halfday_requirements
    ADD CONSTRAINT pk_rotation_halfday_requirements PRIMARY KEY (id);


--
-- Name: rotation_preferences pk_rotation_preferences; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rotation_preferences
    ADD CONSTRAINT pk_rotation_preferences PRIMARY KEY (id);


--
-- Name: rotation_templates pk_rotation_templates; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rotation_templates
    ADD CONSTRAINT pk_rotation_templates PRIMARY KEY (id);


--
-- Name: sacrifice_decisions pk_sacrifice_decisions; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sacrifice_decisions
    ADD CONSTRAINT pk_sacrifice_decisions PRIMARY KEY (id);


--
-- Name: schedule_diffs pk_schedule_diffs; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schedule_diffs
    ADD CONSTRAINT pk_schedule_diffs PRIMARY KEY (id);


--
-- Name: schedule_draft_assignments pk_schedule_draft_assignments; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schedule_draft_assignments
    ADD CONSTRAINT pk_schedule_draft_assignments PRIMARY KEY (id);


--
-- Name: schedule_draft_flags pk_schedule_draft_flags; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schedule_draft_flags
    ADD CONSTRAINT pk_schedule_draft_flags PRIMARY KEY (id);


--
-- Name: schedule_drafts pk_schedule_drafts; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schedule_drafts
    ADD CONSTRAINT pk_schedule_drafts PRIMARY KEY (id);


--
-- Name: schedule_drafts_version pk_schedule_drafts_version; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schedule_drafts_version
    ADD CONSTRAINT pk_schedule_drafts_version PRIMARY KEY (id, transaction_id);


--
-- Name: schedule_overrides pk_schedule_overrides; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schedule_overrides
    ADD CONSTRAINT pk_schedule_overrides PRIMARY KEY (id);


--
-- Name: schedule_runs_version pk_schedule_run_version; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schedule_runs_version
    ADD CONSTRAINT pk_schedule_run_version PRIMARY KEY (id, transaction_id);


--
-- Name: schedule_runs pk_schedule_runs; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schedule_runs
    ADD CONSTRAINT pk_schedule_runs PRIMARY KEY (id);


--
-- Name: schedule_versions pk_schedule_versions; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schedule_versions
    ADD CONSTRAINT pk_schedule_versions PRIMARY KEY (id);


--
-- Name: scheduled_jobs pk_scheduled_jobs; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scheduled_jobs
    ADD CONSTRAINT pk_scheduled_jobs PRIMARY KEY (id);


--
-- Name: scheduled_notifications pk_scheduled_notifications; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scheduled_notifications
    ADD CONSTRAINT pk_scheduled_notifications PRIMARY KEY (id);


--
-- Name: scheduling_zones pk_scheduling_zones; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scheduling_zones
    ADD CONSTRAINT pk_scheduling_zones PRIMARY KEY (id);


--
-- Name: survey_availability pk_survey_availability; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.survey_availability
    ADD CONSTRAINT pk_survey_availability PRIMARY KEY (id);


--
-- Name: survey_responses pk_survey_responses; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.survey_responses
    ADD CONSTRAINT pk_survey_responses PRIMARY KEY (id);


--
-- Name: surveys pk_surveys; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.surveys
    ADD CONSTRAINT pk_surveys PRIMARY KEY (id);


--
-- Name: swap_approvals pk_swap_approvals; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.swap_approvals
    ADD CONSTRAINT pk_swap_approvals PRIMARY KEY (id);


--
-- Name: swap_records pk_swap_records; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.swap_records
    ADD CONSTRAINT pk_swap_records PRIMARY KEY (id);


--
-- Name: system_stress_records pk_system_stress_records; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_stress_records
    ADD CONSTRAINT pk_system_stress_records PRIMARY KEY (id);


--
-- Name: token_blacklist pk_token_blacklist; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.token_blacklist
    ADD CONSTRAINT pk_token_blacklist PRIMARY KEY (id);


--
-- Name: trail_signals pk_trail_signals; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trail_signals
    ADD CONSTRAINT pk_trail_signals PRIMARY KEY (id);


--
-- Name: transaction pk_transaction; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transaction
    ADD CONSTRAINT pk_transaction PRIMARY KEY (id);


--
-- Name: users pk_users; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT pk_users PRIMARY KEY (id);


--
-- Name: users_version pk_users_version; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users_version
    ADD CONSTRAINT pk_users_version PRIMARY KEY (id, transaction_id);


--
-- Name: vulnerability_records pk_vulnerability_records; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vulnerability_records
    ADD CONSTRAINT pk_vulnerability_records PRIMARY KEY (id);


--
-- Name: weekly_patterns pk_weekly_patterns; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weekly_patterns
    ADD CONSTRAINT pk_weekly_patterns PRIMARY KEY (id);


--
-- Name: wellness_accounts pk_wellness_accounts; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wellness_accounts
    ADD CONSTRAINT pk_wellness_accounts PRIMARY KEY (id);


--
-- Name: wellness_leaderboard_snapshots pk_wellness_leaderboard_snapshots; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wellness_leaderboard_snapshots
    ADD CONSTRAINT pk_wellness_leaderboard_snapshots PRIMARY KEY (id);


--
-- Name: wellness_point_transactions pk_wellness_point_transactions; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wellness_point_transactions
    ADD CONSTRAINT pk_wellness_point_transactions PRIMARY KEY (id);


--
-- Name: zone_borrowing_records pk_zone_borrowing_records; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.zone_borrowing_records
    ADD CONSTRAINT pk_zone_borrowing_records PRIMARY KEY (id);


--
-- Name: zone_faculty_assignments pk_zone_faculty_assignments; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.zone_faculty_assignments
    ADD CONSTRAINT pk_zone_faculty_assignments PRIMARY KEY (id);


--
-- Name: zone_incidents pk_zone_incidents; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.zone_incidents
    ADD CONSTRAINT pk_zone_incidents PRIMARY KEY (id);


--
-- Name: procedures procedures_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.procedures
    ADD CONSTRAINT procedures_name_key UNIQUE (name);


--
-- Name: rag_documents rag_documents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rag_documents
    ADD CONSTRAINT rag_documents_pkey PRIMARY KEY (id);


--
-- Name: request_signatures request_signatures_signature_hash_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.request_signatures
    ADD CONSTRAINT request_signatures_signature_hash_key UNIQUE (signature_hash);


--
-- Name: scheduled_jobs scheduled_jobs_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scheduled_jobs
    ADD CONSTRAINT scheduled_jobs_name_key UNIQUE (name);


--
-- Name: task_history task_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task_history
    ADD CONSTRAINT task_history_pkey PRIMARY KEY (id);


--
-- Name: token_blacklist token_blacklist_jti_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.token_blacklist
    ADD CONSTRAINT token_blacklist_jti_key UNIQUE (jti);


--
-- Name: rotation_templates unique_abbreviation; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rotation_templates
    ADD CONSTRAINT unique_abbreviation UNIQUE (abbreviation);


--
-- Name: blocks unique_block_per_half_day; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.blocks
    ADD CONSTRAINT unique_block_per_half_day UNIQUE (date, time_of_day);


--
-- Name: call_assignments unique_call_per_day; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.call_assignments
    ADD CONSTRAINT unique_call_per_day UNIQUE (date, person_id, call_type);


--
-- Name: assignments unique_person_per_block; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.assignments
    ADD CONSTRAINT unique_person_per_block UNIQUE (block_id, person_id);


--
-- Name: activities uq_activity_code; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activities
    ADD CONSTRAINT uq_activity_code UNIQUE (code);


--
-- Name: activities uq_activity_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activities
    ADD CONSTRAINT uq_activity_name UNIQUE (name);


--
-- Name: annual_rotation_assignments uq_annual_rotation_assignments_plan_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.annual_rotation_assignments
    ADD CONSTRAINT uq_annual_rotation_assignments_plan_id UNIQUE (plan_id, person_id, block_number);


--
-- Name: api_keys uq_api_keys_key_hash; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_keys
    ADD CONSTRAINT uq_api_keys_key_hash UNIQUE (key_hash);


--
-- Name: approval_record uq_approval_record_chain_seq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_record
    ADD CONSTRAINT uq_approval_record_chain_seq UNIQUE (chain_id, sequence_num);


--
-- Name: academic_blocks uq_block_year; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.academic_blocks
    ADD CONSTRAINT uq_block_year UNIQUE (block_number, academic_year);


--
-- Name: certification_types uq_certification_types_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.certification_types
    ADD CONSTRAINT uq_certification_types_name UNIQUE (name);


--
-- Name: schedule_draft_assignments uq_draft_assignment_slot; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schedule_draft_assignments
    ADD CONSTRAINT uq_draft_assignment_slot UNIQUE (draft_id, person_id, assignment_date, time_of_day);


--
-- Name: email_templates uq_email_templates_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.email_templates
    ADD CONSTRAINT uq_email_templates_name UNIQUE (name);


--
-- Name: faculty_activity_permissions uq_faculty_activity_permission; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.faculty_activity_permissions
    ADD CONSTRAINT uq_faculty_activity_permission UNIQUE (faculty_role, activity_id);


--
-- Name: faculty_preferences uq_faculty_preferences_faculty_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.faculty_preferences
    ADD CONSTRAINT uq_faculty_preferences_faculty_id UNIQUE (faculty_id);


--
-- Name: faculty_schedule_preferences uq_faculty_schedule_preference_rank; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.faculty_schedule_preferences
    ADD CONSTRAINT uq_faculty_schedule_preference_rank UNIQUE (person_id, rank);


--
-- Name: faculty_weekly_overrides uq_faculty_weekly_override_slot; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.faculty_weekly_overrides
    ADD CONSTRAINT uq_faculty_weekly_override_slot UNIQUE (person_id, effective_date, day_of_week, time_of_day);


--
-- Name: faculty_weekly_templates uq_faculty_weekly_template_slot; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.faculty_weekly_templates
    ADD CONSTRAINT uq_faculty_weekly_template_slot UNIQUE (person_id, day_of_week, time_of_day, week_number);


--
-- Name: graduation_requirements uq_graduation_req_pgy_template; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.graduation_requirements
    ADD CONSTRAINT uq_graduation_req_pgy_template UNIQUE (pgy_level, rotation_template_id);


--
-- Name: half_day_assignments uq_half_day_assignment_person_date_time; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.half_day_assignments
    ADD CONSTRAINT uq_half_day_assignment_person_date_time UNIQUE (person_id, date, time_of_day);


--
-- Name: inpatient_preloads uq_inpatient_preload_person_start_type; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.inpatient_preloads
    ADD CONSTRAINT uq_inpatient_preload_person_start_type UNIQUE (person_id, start_date, rotation_type);


--
-- Name: intern_stagger_patterns uq_intern_stagger_patterns_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.intern_stagger_patterns
    ADD CONSTRAINT uq_intern_stagger_patterns_name UNIQUE (name);


--
-- Name: wellness_leaderboard_snapshots uq_leaderboard_snapshot; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wellness_leaderboard_snapshots
    ADD CONSTRAINT uq_leaderboard_snapshot UNIQUE (snapshot_date, snapshot_type);


--
-- Name: learner_assignments uq_learner_slot; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learner_assignments
    ADD CONSTRAINT uq_learner_slot UNIQUE (learner_id, block_id, day_of_week, time_of_day);


--
-- Name: learner_to_tracks uq_learner_start_date; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learner_to_tracks
    ADD CONSTRAINT uq_learner_start_date UNIQUE (learner_id, start_date);


--
-- Name: learner_tracks uq_learner_tracks_track_number; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learner_tracks
    ADD CONSTRAINT uq_learner_tracks_track_number UNIQUE (track_number);


--
-- Name: notification_preferences uq_notification_preferences_user_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notification_preferences
    ADD CONSTRAINT uq_notification_preferences_user_id UNIQUE (user_id);


--
-- Name: oauth2_clients uq_oauth2_clients_client_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.oauth2_clients
    ADD CONSTRAINT uq_oauth2_clients_client_id UNIQUE (client_id);


--
-- Name: people uq_people_email; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.people
    ADD CONSTRAINT uq_people_email UNIQUE (email);


--
-- Name: person_academic_years uq_person_academic_year; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.person_academic_years
    ADD CONSTRAINT uq_person_academic_year UNIQUE (person_id, academic_year);


--
-- Name: person_certifications uq_person_certification_type; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.person_certifications
    ADD CONSTRAINT uq_person_certification_type UNIQUE (person_id, certification_type_id);


--
-- Name: procedure_credentials uq_person_procedure_credential; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.procedure_credentials
    ADD CONSTRAINT uq_person_procedure_credential UNIQUE (person_id, procedure_id);


--
-- Name: procedures uq_procedures_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.procedures
    ADD CONSTRAINT uq_procedures_name UNIQUE (name);


--
-- Name: request_signatures uq_request_signatures_signature_hash; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.request_signatures
    ADD CONSTRAINT uq_request_signatures_signature_hash UNIQUE (signature_hash);


--
-- Name: resident_call_preloads uq_resident_call_person_date; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resident_call_preloads
    ADD CONSTRAINT uq_resident_call_person_date UNIQUE (person_id, call_date);


--
-- Name: resident_weekly_requirements uq_resident_weekly_requirement_template; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resident_weekly_requirements
    ADD CONSTRAINT uq_resident_weekly_requirement_template UNIQUE (rotation_template_id);


--
-- Name: rotation_activity_requirements uq_rotation_activity_req; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rotation_activity_requirements
    ADD CONSTRAINT uq_rotation_activity_req UNIQUE (rotation_template_id, activity_id, applicable_weeks_hash);


--
-- Name: scheduled_jobs uq_scheduled_jobs_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scheduled_jobs
    ADD CONSTRAINT uq_scheduled_jobs_name UNIQUE (name);


--
-- Name: survey_availability uq_survey_availability_person_survey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.survey_availability
    ADD CONSTRAINT uq_survey_availability_person_survey UNIQUE (person_id, survey_id);


--
-- Name: surveys uq_survey_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.surveys
    ADD CONSTRAINT uq_survey_name UNIQUE (name);


--
-- Name: token_blacklist uq_token_blacklist_jti; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.token_blacklist
    ADD CONSTRAINT uq_token_blacklist_jti UNIQUE (jti);


--
-- Name: users uq_users_email; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT uq_users_email UNIQUE (email);


--
-- Name: users uq_users_username; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT uq_users_username UNIQUE (username);


--
-- Name: weekly_patterns uq_weekly_pattern_slot_v2; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.weekly_patterns
    ADD CONSTRAINT uq_weekly_pattern_slot_v2 UNIQUE (rotation_template_id, day_of_week, time_of_day, week_number);


--
-- Name: wellness_accounts uq_wellness_account_person; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.wellness_accounts
    ADD CONSTRAINT uq_wellness_account_person UNIQUE (person_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: idx_absence_person_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_absence_person_id ON public.absences USING btree (person_id);


--
-- Name: idx_absence_version_end_transaction; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_absence_version_end_transaction ON public.absence_version USING btree (end_transaction_id);


--
-- Name: idx_absence_version_operation; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_absence_version_operation ON public.absence_version USING btree (operation_type);


--
-- Name: idx_absence_version_transaction; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_absence_version_transaction ON public.absence_version USING btree (transaction_id);


--
-- Name: idx_absences_dates; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_absences_dates ON public.absences USING btree (start_date, end_date);


--
-- Name: idx_absences_person; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_absences_person ON public.absences USING btree (person_id);


--
-- Name: idx_absences_person_dates; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_absences_person_dates ON public.absences USING btree (person_id, start_date, end_date);


--
-- Name: idx_absences_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_absences_status ON public.absences USING btree (status);


--
-- Name: idx_absences_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_absences_type ON public.absences USING btree (absence_type);


--
-- Name: idx_activities_procedure_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_activities_procedure_id ON public.activities USING btree (procedure_id);


--
-- Name: idx_activity_log_user_action_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_activity_log_user_action_created ON public.activity_log USING btree (user_id, action_type, created_at);


--
-- Name: idx_allostasis_calculated; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_allostasis_calculated ON public.allostasis_records USING btree (calculated_at);


--
-- Name: idx_allostasis_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_allostasis_entity ON public.allostasis_records USING btree (entity_id, entity_type);


--
-- Name: idx_allostasis_risk; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_allostasis_risk ON public.allostasis_records USING btree (risk_level);


--
-- Name: idx_api_key_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_api_key_active ON public.api_keys USING btree (is_active, expires_at);


--
-- Name: idx_api_key_owner; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_api_key_owner ON public.api_keys USING btree (owner_id, is_active);


--
-- Name: idx_assignment_backups_draft_assignment; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_assignment_backups_draft_assignment ON public.assignment_backups USING btree (draft_assignment_id);


--
-- Name: idx_assignment_backups_unrestored; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_assignment_backups_unrestored ON public.assignment_backups USING btree (draft_assignment_id) WHERE (restored_at IS NULL);


--
-- Name: idx_assignment_block_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_assignment_block_id ON public.assignments USING btree (block_id);


--
-- Name: idx_assignment_person_block; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_assignment_person_block ON public.assignments USING btree (person_id, block_id);


--
-- Name: idx_assignment_person_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_assignment_person_id ON public.assignments USING btree (person_id);


--
-- Name: idx_assignment_rotation_template_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_assignment_rotation_template_id ON public.assignments USING btree (rotation_template_id);


--
-- Name: idx_assignment_version_end_transaction; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_assignment_version_end_transaction ON public.assignments_version USING btree (end_transaction_id);


--
-- Name: idx_assignment_version_operation; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_assignment_version_operation ON public.assignments_version USING btree (operation_type);


--
-- Name: idx_assignment_version_transaction; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_assignment_version_transaction ON public.assignments_version USING btree (transaction_id);


--
-- Name: idx_assignments_block; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_assignments_block ON public.assignments USING btree (block_id);


--
-- Name: idx_assignments_block_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_assignments_block_role ON public.assignments USING btree (block_id, role);


--
-- Name: idx_assignments_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_assignments_created_at ON public.assignments USING btree (created_at);


--
-- Name: idx_assignments_person; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_assignments_person ON public.assignments USING btree (person_id);


--
-- Name: idx_assignments_person_block; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_assignments_person_block ON public.assignments USING btree (person_id, block_id);


--
-- Name: idx_assignments_person_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_assignments_person_created ON public.assignments USING btree (person_id, created_at);


--
-- Name: idx_assignments_schedule_run; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_assignments_schedule_run ON public.assignments USING btree (schedule_run_id);


--
-- Name: idx_assignments_version_end_transaction; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_assignments_version_end_transaction ON public.assignments_version USING btree (end_transaction_id);


--
-- Name: idx_assignments_version_operation; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_assignments_version_operation ON public.assignments_version USING btree (operation_type);


--
-- Name: idx_assignments_version_transaction; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_assignments_version_transaction ON public.assignments_version USING btree (transaction_id);


--
-- Name: idx_blacklist_expires; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_blacklist_expires ON public.token_blacklist USING btree (expires_at);


--
-- Name: idx_blacklist_jti; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_blacklist_jti ON public.token_blacklist USING btree (jti);


--
-- Name: idx_blacklist_jti_expires; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_blacklist_jti_expires ON public.token_blacklist USING btree (jti, expires_at);


--
-- Name: idx_block_assignments_block_year; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_block_assignments_block_year ON public.block_assignments USING btree (block_number, academic_year);


--
-- Name: idx_block_assignments_resident; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_block_assignments_resident ON public.block_assignments USING btree (resident_id);


--
-- Name: idx_block_assignments_rotation; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_block_assignments_rotation ON public.block_assignments USING btree (rotation_template_id);


--
-- Name: idx_block_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_block_date ON public.blocks USING btree (date);


--
-- Name: idx_block_date_time_of_day; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_block_date_time_of_day ON public.blocks USING btree (date, time_of_day);


--
-- Name: idx_blocks_block_number; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_blocks_block_number ON public.blocks USING btree (block_number);


--
-- Name: idx_blocks_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_blocks_date ON public.blocks USING btree (date);


--
-- Name: idx_borrowing_lending; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_borrowing_lending ON public.zone_borrowing_records USING btree (lending_zone_id);


--
-- Name: idx_borrowing_requested_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_borrowing_requested_at ON public.zone_borrowing_records USING btree (requested_at);


--
-- Name: idx_borrowing_requesting; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_borrowing_requesting ON public.zone_borrowing_records USING btree (requesting_zone_id);


--
-- Name: idx_borrowing_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_borrowing_status ON public.zone_borrowing_records USING btree (status);


--
-- Name: idx_call_assignment_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_call_assignment_date ON public.call_assignments USING btree (date);


--
-- Name: idx_call_assignment_person_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_call_assignment_person_id ON public.call_assignments USING btree (person_id);


--
-- Name: idx_call_assignments_person_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_call_assignments_person_date ON public.call_assignments USING btree (person_id, date);


--
-- Name: idx_call_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_call_date ON public.call_assignments USING btree (date);


--
-- Name: idx_call_overrides_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_call_overrides_active ON public.call_overrides USING btree (is_active);


--
-- Name: idx_call_overrides_call_assignment; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_call_overrides_call_assignment ON public.call_overrides USING btree (call_assignment_id);


--
-- Name: idx_call_overrides_effective; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_call_overrides_effective ON public.call_overrides USING btree (effective_date, call_type);


--
-- Name: idx_call_person; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_call_person ON public.call_assignments USING btree (person_id);


--
-- Name: idx_cert_types_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cert_types_active ON public.certification_types USING btree (is_active);


--
-- Name: idx_cert_types_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_cert_types_name ON public.certification_types USING btree (name);


--
-- Name: idx_compensation_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_compensation_active ON public.compensation_records USING btree (is_active);


--
-- Name: idx_compensation_initiated; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_compensation_initiated ON public.compensation_records USING btree (initiated_at);


--
-- Name: idx_compensation_stress; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_compensation_stress ON public.compensation_records USING btree (stress_id);


--
-- Name: idx_conflict_alerts_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conflict_alerts_created_at ON public.conflict_alerts USING btree (created_at);


--
-- Name: idx_conflict_alerts_faculty_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conflict_alerts_faculty_id ON public.conflict_alerts USING btree (faculty_id);


--
-- Name: idx_conflict_alerts_faculty_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conflict_alerts_faculty_status ON public.conflict_alerts USING btree (faculty_id, status);


--
-- Name: idx_conflict_alerts_fmit_week; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conflict_alerts_fmit_week ON public.conflict_alerts USING btree (fmit_week);


--
-- Name: idx_conflict_alerts_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_conflict_alerts_status ON public.conflict_alerts USING btree (status);


--
-- Name: idx_credentials_expiration; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_credentials_expiration ON public.procedure_credentials USING btree (expiration_date);


--
-- Name: idx_credentials_person; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_credentials_person ON public.procedure_credentials USING btree (person_id);


--
-- Name: idx_credentials_procedure; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_credentials_procedure ON public.procedure_credentials USING btree (procedure_id);


--
-- Name: idx_credentials_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_credentials_status ON public.procedure_credentials USING btree (status);


--
-- Name: idx_diffs_computed; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_diffs_computed ON public.schedule_diffs USING btree (computed_at);


--
-- Name: idx_diffs_from_to; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_diffs_from_to ON public.schedule_diffs USING btree (from_version_id, to_version_id);


--
-- Name: idx_diffs_from_version; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_diffs_from_version ON public.schedule_diffs USING btree (from_version_id);


--
-- Name: idx_diffs_to_version; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_diffs_to_version ON public.schedule_diffs USING btree (to_version_id);


--
-- Name: idx_draft_assignments_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_draft_assignments_date ON public.schedule_draft_assignments USING btree (assignment_date);


--
-- Name: idx_draft_assignments_draft; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_draft_assignments_draft ON public.schedule_draft_assignments USING btree (draft_id);


--
-- Name: idx_draft_assignments_person; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_draft_assignments_person ON public.schedule_draft_assignments USING btree (person_id);


--
-- Name: idx_draft_flags_acknowledged; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_draft_flags_acknowledged ON public.schedule_draft_flags USING btree (acknowledged_at);


--
-- Name: idx_draft_flags_draft; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_draft_flags_draft ON public.schedule_draft_flags USING btree (draft_id);


--
-- Name: idx_draft_flags_severity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_draft_flags_severity ON public.schedule_draft_flags USING btree (severity);


--
-- Name: idx_draft_flags_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_draft_flags_type ON public.schedule_draft_flags USING btree (flag_type);


--
-- Name: idx_equilibrium_calculated; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_equilibrium_calculated ON public.equilibrium_shifts USING btree (calculated_at);


--
-- Name: idx_equilibrium_state; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_equilibrium_state ON public.equilibrium_shifts USING btree (equilibrium_state);


--
-- Name: idx_equilibrium_sustainable; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_equilibrium_sustainable ON public.equilibrium_shifts USING btree (is_sustainable);


--
-- Name: idx_events_severity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_events_severity ON public.resilience_events USING btree (severity);


--
-- Name: idx_events_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_events_timestamp ON public.resilience_events USING btree ("timestamp");


--
-- Name: idx_events_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_events_type ON public.resilience_events USING btree (event_type);


--
-- Name: idx_fallback_activated_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fallback_activated_at ON public.fallback_activations USING btree (activated_at);


--
-- Name: idx_fallback_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fallback_active ON public.fallback_activations USING btree (deactivated_at);


--
-- Name: idx_fallback_scenario; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_fallback_scenario ON public.fallback_activations USING btree (scenario);


--
-- Name: idx_feature_flag_enabled; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_feature_flag_enabled ON public.feature_flags USING btree (enabled);


--
-- Name: idx_feature_flag_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_feature_flag_type ON public.feature_flags USING btree (flag_type);


--
-- Name: idx_feedback_loop_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_feedback_loop_name ON public.feedback_loop_states USING btree (loop_name);


--
-- Name: idx_feedback_loop_severity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_feedback_loop_severity ON public.feedback_loop_states USING btree (deviation_severity);


--
-- Name: idx_feedback_loop_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_feedback_loop_timestamp ON public.feedback_loop_states USING btree ("timestamp");


--
-- Name: idx_flag_audit_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_flag_audit_timestamp ON public.feature_flag_audit USING btree (created_at);


--
-- Name: idx_flag_audit_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_flag_audit_user ON public.feature_flag_audit USING btree (user_id);


--
-- Name: idx_flag_eval_flag_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_flag_eval_flag_user ON public.feature_flag_evaluations USING btree (flag_id, user_id);


--
-- Name: idx_flag_eval_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_flag_eval_timestamp ON public.feature_flag_evaluations USING btree (evaluated_at);


--
-- Name: idx_hda_activity_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hda_activity_id ON public.half_day_assignments USING btree (activity_id);


--
-- Name: idx_hda_block_assignment_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hda_block_assignment_id ON public.half_day_assignments USING btree (block_assignment_id);


--
-- Name: idx_hda_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hda_date ON public.half_day_assignments USING btree (date);


--
-- Name: idx_hda_date_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hda_date_time ON public.half_day_assignments USING btree (date, time_of_day);


--
-- Name: idx_hda_person_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hda_person_date ON public.half_day_assignments USING btree (person_id, date);


--
-- Name: idx_hda_person_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hda_person_id ON public.half_day_assignments USING btree (person_id);


--
-- Name: idx_hda_source; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hda_source ON public.half_day_assignments USING btree (source);


--
-- Name: idx_health_checks_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_health_checks_status ON public.resilience_health_checks USING btree (overall_status);


--
-- Name: idx_health_checks_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_health_checks_timestamp ON public.resilience_health_checks USING btree ("timestamp");


--
-- Name: idx_hopfield_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hopfield_created ON public.hopfield_positions USING btree (created_at);


--
-- Name: idx_hopfield_person; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hopfield_person ON public.hopfield_positions USING btree (person_id);


--
-- Name: idx_idempotency_expires; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_idempotency_expires ON public.idempotency_requests USING btree (expires_at);


--
-- Name: idx_idempotency_key_hash; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_idempotency_key_hash ON public.idempotency_requests USING btree (idempotency_key, body_hash);


--
-- Name: idx_idempotency_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_idempotency_status ON public.idempotency_requests USING btree (status);


--
-- Name: idx_import_batches_status_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_import_batches_status_created ON public.import_batches USING btree (status, created_at);


--
-- Name: idx_import_staged_asgn_batch_row; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_import_staged_asgn_batch_row ON public.import_staged_assignments USING btree (batch_id, row_number);


--
-- Name: idx_incidents_resolved; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_incidents_resolved ON public.zone_incidents USING btree (resolved_at);


--
-- Name: idx_incidents_severity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_incidents_severity ON public.zone_incidents USING btree (severity);


--
-- Name: idx_incidents_started; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_incidents_started ON public.zone_incidents USING btree (started_at);


--
-- Name: idx_incidents_zone; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_incidents_zone ON public.zone_incidents USING btree (zone_id);


--
-- Name: idx_inpatient_preload_dates; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_inpatient_preload_dates ON public.inpatient_preloads USING btree (start_date, end_date);


--
-- Name: idx_inpatient_preload_person_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_inpatient_preload_person_id ON public.inpatient_preloads USING btree (person_id);


--
-- Name: idx_inpatient_preload_rotation_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_inpatient_preload_rotation_type ON public.inpatient_preloads USING btree (rotation_type);


--
-- Name: idx_inpatient_preload_start_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_inpatient_preload_start_date ON public.inpatient_preloads USING btree (start_date);


--
-- Name: idx_ip_blacklist_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ip_blacklist_active ON public.ip_blacklists USING btree (is_active, expires_at);


--
-- Name: idx_ip_blacklist_detection; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ip_blacklist_detection ON public.ip_blacklists USING btree (detection_method, is_active);


--
-- Name: idx_ip_whitelist_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ip_whitelist_active ON public.ip_whitelists USING btree (is_active, expires_at);


--
-- Name: idx_ip_whitelist_applies_to; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ip_whitelist_applies_to ON public.ip_whitelists USING btree (applies_to, is_active);


--
-- Name: idx_leaderboard_snapshot_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_leaderboard_snapshot_date ON public.wellness_leaderboard_snapshots USING btree (snapshot_date);


--
-- Name: idx_metrics_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_metrics_category ON public.metric_snapshots USING btree (category);


--
-- Name: idx_notifications_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_notifications_created ON public.notifications USING btree (created_at);


--
-- Name: idx_notifications_is_read; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_notifications_is_read ON public.notifications USING btree (is_read);


--
-- Name: idx_notifications_recipient; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_notifications_recipient ON public.notifications USING btree (recipient_id);


--
-- Name: idx_notifications_recipient_read_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_notifications_recipient_read_created ON public.notifications USING btree (recipient_id, is_read, created_at);


--
-- Name: idx_notifications_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_notifications_type ON public.notifications USING btree (notification_type);


--
-- Name: idx_oauth2_client_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_oauth2_client_active ON public.oauth2_clients USING btree (is_active);


--
-- Name: idx_oauth2_client_owner; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_oauth2_client_owner ON public.oauth2_clients USING btree (owner_id, is_active);


--
-- Name: idx_people_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_people_type ON public.people USING btree (type);


--
-- Name: idx_person_certs_expiration; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_person_certs_expiration ON public.person_certifications USING btree (expiration_date);


--
-- Name: idx_person_certs_person; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_person_certs_person ON public.person_certifications USING btree (person_id);


--
-- Name: idx_person_certs_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_person_certs_status ON public.person_certifications USING btree (status);


--
-- Name: idx_person_certs_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_person_certs_type ON public.person_certifications USING btree (certification_type_id);


--
-- Name: idx_positive_feedback_detected; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_positive_feedback_detected ON public.positive_feedback_alerts USING btree (detected_at);


--
-- Name: idx_positive_feedback_resolved; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_positive_feedback_resolved ON public.positive_feedback_alerts USING btree (resolved_at);


--
-- Name: idx_positive_feedback_urgency; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_positive_feedback_urgency ON public.positive_feedback_alerts USING btree (urgency);


--
-- Name: idx_prefs_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_prefs_user ON public.notification_preferences USING btree (user_id);


--
-- Name: idx_proc_creds_person_status_exp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_proc_creds_person_status_exp ON public.procedure_credentials USING btree (person_id, status, expiration_date);


--
-- Name: idx_proc_creds_procedure_status_exp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_proc_creds_procedure_status_exp ON public.procedure_credentials USING btree (procedure_id, status, expiration_date);


--
-- Name: idx_proc_creds_status_expiration; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_proc_creds_status_expiration ON public.procedure_credentials USING btree (status, expiration_date);


--
-- Name: idx_procedures_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_procedures_active ON public.procedures USING btree (is_active);


--
-- Name: idx_procedures_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_procedures_category ON public.procedures USING btree (category);


--
-- Name: idx_procedures_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_procedures_name ON public.procedures USING btree (name);


--
-- Name: idx_procedures_specialty; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_procedures_specialty ON public.procedures USING btree (specialty);


--
-- Name: idx_request_signature_api_key; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_request_signature_api_key ON public.request_signatures USING btree (api_key_id, verified_at);


--
-- Name: idx_request_signature_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_request_signature_timestamp ON public.request_signatures USING btree (request_timestamp, verified_at);


--
-- Name: idx_resident_call_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_resident_call_date ON public.resident_call_preloads USING btree (call_date);


--
-- Name: idx_resident_call_person_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_resident_call_person_id ON public.resident_call_preloads USING btree (person_id);


--
-- Name: idx_rotation_halfday_template; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_rotation_halfday_template ON public.rotation_halfday_requirements USING btree (rotation_template_id);


--
-- Name: idx_rotation_templates_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rotation_templates_name ON public.rotation_templates USING btree (name);


--
-- Name: idx_rotation_templates_rotation_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rotation_templates_rotation_type ON public.rotation_templates USING btree (rotation_type);


--
-- Name: idx_sacrifice_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sacrifice_active ON public.sacrifice_decisions USING btree (recovered_at);


--
-- Name: idx_sacrifice_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sacrifice_timestamp ON public.sacrifice_decisions USING btree ("timestamp");


--
-- Name: idx_sched_draft_asgn_draft_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sched_draft_asgn_draft_id ON public.schedule_draft_assignments USING btree (draft_id);


--
-- Name: idx_sched_draft_asgn_person_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sched_draft_asgn_person_id ON public.schedule_draft_assignments USING btree (person_id);


--
-- Name: idx_sched_draft_flags_draft_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sched_draft_flags_draft_id ON public.schedule_draft_flags USING btree (draft_id);


--
-- Name: idx_schedule_drafts_block; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_schedule_drafts_block ON public.schedule_drafts USING btree (target_block);


--
-- Name: idx_schedule_drafts_dates; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_schedule_drafts_dates ON public.schedule_drafts USING btree (target_start_date, target_end_date);


--
-- Name: idx_schedule_drafts_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_schedule_drafts_status ON public.schedule_drafts USING btree (status);


--
-- Name: idx_schedule_drafts_status_dates; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_schedule_drafts_status_dates ON public.schedule_drafts USING btree (status, target_start_date, target_end_date);


--
-- Name: idx_schedule_overrides_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_schedule_overrides_active ON public.schedule_overrides USING btree (is_active);


--
-- Name: idx_schedule_overrides_assignment; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_schedule_overrides_assignment ON public.schedule_overrides USING btree (half_day_assignment_id);


--
-- Name: idx_schedule_overrides_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_schedule_overrides_created_by ON public.schedule_overrides USING btree (created_by_id);


--
-- Name: idx_schedule_overrides_effective; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_schedule_overrides_effective ON public.schedule_overrides USING btree (effective_date, time_of_day);


--
-- Name: idx_schedule_overrides_original; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_schedule_overrides_original ON public.schedule_overrides USING btree (original_person_id);


--
-- Name: idx_schedule_overrides_replacement; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_schedule_overrides_replacement ON public.schedule_overrides USING btree (replacement_person_id);


--
-- Name: idx_schedule_runs_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_schedule_runs_date ON public.schedule_runs USING btree (created_at);


--
-- Name: idx_schedule_runs_date_range; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_schedule_runs_date_range ON public.schedule_runs USING btree (start_date, end_date);


--
-- Name: idx_schedule_runs_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_schedule_runs_status ON public.schedule_runs USING btree (status);


--
-- Name: idx_schedule_runs_version_end_transaction; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_schedule_runs_version_end_transaction ON public.schedule_runs_version USING btree (end_transaction_id);


--
-- Name: idx_schedule_runs_version_operation; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_schedule_runs_version_operation ON public.schedule_runs_version USING btree (operation_type);


--
-- Name: idx_schedule_runs_version_transaction; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_schedule_runs_version_transaction ON public.schedule_runs_version USING btree (transaction_id);


--
-- Name: idx_schedule_versions_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_schedule_versions_created ON public.schedule_versions USING btree (created_at);


--
-- Name: idx_schedule_versions_parent; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_schedule_versions_parent ON public.schedule_versions USING btree (parent_version_id);


--
-- Name: idx_schedule_versions_run; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_schedule_versions_run ON public.schedule_versions USING btree (schedule_run_id);


--
-- Name: idx_schedule_versions_trigger; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_schedule_versions_trigger ON public.schedule_versions USING btree (trigger_type);


--
-- Name: idx_scheduled_recipient; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scheduled_recipient ON public.scheduled_notifications USING btree (recipient_id);


--
-- Name: idx_scheduled_send_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scheduled_send_at ON public.scheduled_notifications USING btree (send_at);


--
-- Name: idx_scheduled_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scheduled_status ON public.scheduled_notifications USING btree (status);


--
-- Name: idx_stress_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_stress_active ON public.system_stress_records USING btree (is_active);


--
-- Name: idx_stress_applied; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_stress_applied ON public.system_stress_records USING btree (applied_at);


--
-- Name: idx_stress_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_stress_type ON public.system_stress_records USING btree (stress_type);


--
-- Name: idx_survey_avail_person; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_survey_avail_person ON public.survey_availability USING btree (person_id);


--
-- Name: idx_survey_avail_survey; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_survey_avail_survey ON public.survey_availability USING btree (survey_id);


--
-- Name: idx_survey_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_survey_is_active ON public.surveys USING btree (is_active);


--
-- Name: idx_survey_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_survey_name ON public.surveys USING btree (name);


--
-- Name: idx_survey_response_person_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_survey_response_person_id ON public.survey_responses USING btree (person_id);


--
-- Name: idx_survey_response_submitted; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_survey_response_submitted ON public.survey_responses USING btree (submitted_at);


--
-- Name: idx_survey_response_survey_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_survey_response_survey_id ON public.survey_responses USING btree (survey_id);


--
-- Name: idx_survey_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_survey_type ON public.surveys USING btree (survey_type);


--
-- Name: idx_swap_approvals_faculty_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_swap_approvals_faculty_id ON public.swap_approvals USING btree (faculty_id);


--
-- Name: idx_swap_approvals_swap_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_swap_approvals_swap_id ON public.swap_approvals USING btree (swap_id);


--
-- Name: idx_swap_records_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_swap_records_status ON public.swap_records USING btree (status);


--
-- Name: idx_swap_records_status_requested; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_swap_records_status_requested ON public.swap_records USING btree (status, requested_at);


--
-- Name: idx_swap_records_target_faculty_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_swap_records_target_faculty_status ON public.swap_records USING btree (target_faculty_id, status);


--
-- Name: idx_swap_records_target_week; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_swap_records_target_week ON public.swap_records USING btree (target_week);


--
-- Name: idx_swap_source_faculty; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_swap_source_faculty ON public.swap_records USING btree (source_faculty_id);


--
-- Name: idx_swap_target_faculty; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_swap_target_faculty ON public.swap_records USING btree (target_faculty_id);


--
-- Name: idx_transaction_issued_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transaction_issued_at ON public.transaction USING btree (issued_at);


--
-- Name: idx_transaction_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transaction_user_id ON public.transaction USING btree (user_id);


--
-- Name: idx_users_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_is_active ON public.users USING btree (is_active);


--
-- Name: idx_users_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_role ON public.users USING btree (role);


--
-- Name: idx_users_version_end_txn; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_version_end_txn ON public.users_version USING btree (end_transaction_id);


--
-- Name: idx_users_version_op; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_version_op ON public.users_version USING btree (operation_type);


--
-- Name: idx_users_version_txn; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_version_txn ON public.users_version USING btree (transaction_id);


--
-- Name: idx_vulnerability_analyzed_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_vulnerability_analyzed_at ON public.vulnerability_records USING btree (analyzed_at);


--
-- Name: idx_vulnerability_n1_pass; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_vulnerability_n1_pass ON public.vulnerability_records USING btree (n1_pass);


--
-- Name: idx_vulnerability_n2_pass; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_vulnerability_n2_pass ON public.vulnerability_records USING btree (n2_pass);


--
-- Name: idx_weekly_patterns_template_day_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_weekly_patterns_template_day_time ON public.weekly_patterns USING btree (rotation_template_id, day_of_week, time_of_day);


--
-- Name: idx_wellness_account_person; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_wellness_account_person ON public.wellness_accounts USING btree (person_id);


--
-- Name: idx_wellness_txn_account; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_wellness_txn_account ON public.wellness_point_transactions USING btree (account_id);


--
-- Name: idx_wellness_txn_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_wellness_txn_created ON public.wellness_point_transactions USING btree (created_at);


--
-- Name: idx_zone_faculty_available; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_zone_faculty_available ON public.zone_faculty_assignments USING btree (is_available);


--
-- Name: idx_zone_faculty_faculty; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_zone_faculty_faculty ON public.zone_faculty_assignments USING btree (faculty_id);


--
-- Name: idx_zone_faculty_zone; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_zone_faculty_zone ON public.zone_faculty_assignments USING btree (zone_id);


--
-- Name: idx_zones_name; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_zones_name ON public.scheduling_zones USING btree (name);


--
-- Name: idx_zones_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_zones_status ON public.scheduling_zones USING btree (status);


--
-- Name: idx_zones_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_zones_type ON public.scheduling_zones USING btree (zone_type);


--
-- Name: ix_academic_blocks_year; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_academic_blocks_year ON public.academic_blocks USING btree (academic_year);


--
-- Name: ix_activities_activity_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_activities_activity_category ON public.activities USING btree (activity_category);


--
-- Name: ix_activities_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_activities_code ON public.activities USING btree (code);


--
-- Name: ix_activities_is_archived; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_activities_is_archived ON public.activities USING btree (is_archived);


--
-- Name: ix_activities_is_protected; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_activities_is_protected ON public.activities USING btree (is_protected);


--
-- Name: ix_activity_log_action_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_activity_log_action_type ON public.activity_log USING btree (action_type);


--
-- Name: ix_activity_log_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_activity_log_created_at ON public.activity_log USING btree (created_at DESC);


--
-- Name: ix_activity_log_failed_actions; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_activity_log_failed_actions ON public.activity_log USING btree (created_at DESC) WHERE (((details ->> 'success'::text) = 'false'::text) OR ((action_type)::text ~~ '%_FAILED'::text));


--
-- Name: ix_activity_log_target; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_activity_log_target ON public.activity_log USING btree (target_entity, target_id);


--
-- Name: ix_activity_log_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_activity_log_user_id ON public.activity_log USING btree (user_id);


--
-- Name: ix_ai_budget_config_budget_period; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_budget_config_budget_period ON public.ai_budget_config USING btree (budget_period);


--
-- Name: ix_ai_usage_log_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_usage_log_created_at ON public.ai_usage_log USING btree (created_at);


--
-- Name: ix_ai_usage_log_model_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_usage_log_model_id ON public.ai_usage_log USING btree (model_id);


--
-- Name: ix_ai_usage_log_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_usage_log_status ON public.ai_usage_log USING btree (status);


--
-- Name: ix_ai_usage_log_task_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_usage_log_task_name ON public.ai_usage_log USING btree (task_name);


--
-- Name: ix_api_keys_key_hash; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_api_keys_key_hash ON public.api_keys USING btree (key_hash);


--
-- Name: ix_api_keys_key_prefix; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_api_keys_key_prefix ON public.api_keys USING btree (key_prefix);


--
-- Name: ix_approval_record_acgme_overrides; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_approval_record_acgme_overrides ON public.approval_record USING btree (created_at DESC) WHERE ((action)::text ~~ 'ACGME_OVERRIDE%'::text);


--
-- Name: ix_approval_record_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_approval_record_action ON public.approval_record USING btree (action);


--
-- Name: ix_approval_record_actor_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_approval_record_actor_id ON public.approval_record USING btree (actor_id);


--
-- Name: ix_approval_record_chain_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_approval_record_chain_id ON public.approval_record USING btree (chain_id);


--
-- Name: ix_approval_record_chain_seq; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_approval_record_chain_seq ON public.approval_record USING btree (chain_id, sequence_num);


--
-- Name: ix_approval_record_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_approval_record_created_at ON public.approval_record USING btree (created_at DESC);


--
-- Name: ix_approval_record_seals; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_approval_record_seals ON public.approval_record USING btree (chain_id, sequence_num DESC) WHERE ((action)::text = 'DAY_SEALED'::text);


--
-- Name: ix_approval_record_target; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_approval_record_target ON public.approval_record USING btree (target_entity_type, target_entity_id);


--
-- Name: ix_assignment_backups_draft_assignment_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_assignment_backups_draft_assignment_id ON public.assignment_backups USING btree (draft_assignment_id);


--
-- Name: ix_block_assignments_academic_block_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_block_assignments_academic_block_id ON public.block_assignments USING btree (academic_block_id);


--
-- Name: ix_block_assignments_block_year; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_block_assignments_block_year ON public.block_assignments USING btree (block_number, academic_year);


--
-- Name: ix_block_assignments_resident_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_block_assignments_resident_id ON public.block_assignments USING btree (resident_id);


--
-- Name: ix_block_assignments_rotation_template_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_block_assignments_rotation_template_id ON public.block_assignments USING btree (rotation_template_id);


--
-- Name: ix_blocks_day_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_blocks_day_type ON public.blocks USING btree (day_type);


--
-- Name: ix_chaos_experiments_injector_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_chaos_experiments_injector_type ON public.chaos_experiments USING btree (injector_type);


--
-- Name: ix_chaos_experiments_scheduled_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_chaos_experiments_scheduled_at ON public.chaos_experiments USING btree (scheduled_at);


--
-- Name: ix_chaos_experiments_started_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_chaos_experiments_started_at ON public.chaos_experiments USING btree (started_at);


--
-- Name: ix_chaos_experiments_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_chaos_experiments_status ON public.chaos_experiments USING btree (status);


--
-- Name: ix_clinic_sessions_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_clinic_sessions_date ON public.clinic_sessions USING btree (date);


--
-- Name: ix_cognitive_decisions_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cognitive_decisions_category ON public.cognitive_decisions USING btree (category);


--
-- Name: ix_cognitive_decisions_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cognitive_decisions_created_at ON public.cognitive_decisions USING btree (created_at);


--
-- Name: ix_cognitive_decisions_outcome; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cognitive_decisions_outcome ON public.cognitive_decisions USING btree (outcome);


--
-- Name: ix_cognitive_decisions_session_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cognitive_decisions_session_id ON public.cognitive_decisions USING btree (session_id);


--
-- Name: ix_cognitive_sessions_started_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cognitive_sessions_started_at ON public.cognitive_sessions USING btree (started_at);


--
-- Name: ix_cognitive_sessions_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cognitive_sessions_user_id ON public.cognitive_sessions USING btree (user_id);


--
-- Name: ix_conflict_alerts_faculty_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_conflict_alerts_faculty_id ON public.conflict_alerts USING btree (faculty_id);


--
-- Name: ix_conflict_alerts_fmit_week; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_conflict_alerts_fmit_week ON public.conflict_alerts USING btree (fmit_week);


--
-- Name: ix_conflict_alerts_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_conflict_alerts_status ON public.conflict_alerts USING btree (status);


--
-- Name: ix_constraint_configurations_name; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_constraint_configurations_name ON public.constraint_configurations USING btree (name);


--
-- Name: ix_cross_training_priority; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cross_training_priority ON public.cross_training_recommendations USING btree (priority);


--
-- Name: ix_cross_training_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cross_training_status ON public.cross_training_recommendations USING btree (status);


--
-- Name: ix_email_logs_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_email_logs_created_at ON public.email_logs USING btree (created_at);


--
-- Name: ix_email_logs_notification_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_email_logs_notification_id ON public.email_logs USING btree (notification_id);


--
-- Name: ix_email_logs_recipient_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_email_logs_recipient_email ON public.email_logs USING btree (recipient_email);


--
-- Name: ix_email_logs_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_email_logs_status ON public.email_logs USING btree (status);


--
-- Name: ix_email_logs_template_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_email_logs_template_id ON public.email_logs USING btree (template_id);


--
-- Name: ix_email_templates_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_email_templates_is_active ON public.email_templates USING btree (is_active);


--
-- Name: ix_email_templates_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_email_templates_name ON public.email_templates USING btree (name);


--
-- Name: ix_email_templates_template_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_email_templates_template_type ON public.email_templates USING btree (template_type);


--
-- Name: ix_faculty_activity_permissions_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_faculty_activity_permissions_role ON public.faculty_activity_permissions USING btree (faculty_role);


--
-- Name: ix_faculty_centrality_composite_score; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_faculty_centrality_composite_score ON public.faculty_centrality USING btree (composite_score);


--
-- Name: ix_faculty_centrality_faculty_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_faculty_centrality_faculty_id ON public.faculty_centrality USING btree (faculty_id);


--
-- Name: ix_faculty_centrality_is_hub; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_faculty_centrality_is_hub ON public.faculty_centrality USING btree (is_hub);


--
-- Name: ix_faculty_preferences_faculty_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_faculty_preferences_faculty_id ON public.faculty_preferences USING btree (faculty_id);


--
-- Name: ix_faculty_schedule_preferences_direction; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_faculty_schedule_preferences_direction ON public.faculty_schedule_preferences USING btree (direction);


--
-- Name: ix_faculty_schedule_preferences_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_faculty_schedule_preferences_is_active ON public.faculty_schedule_preferences USING btree (is_active);


--
-- Name: ix_faculty_schedule_preferences_person_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_faculty_schedule_preferences_person_active ON public.faculty_schedule_preferences USING btree (person_id, is_active);


--
-- Name: ix_faculty_schedule_preferences_person_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_faculty_schedule_preferences_person_id ON public.faculty_schedule_preferences USING btree (person_id);


--
-- Name: ix_faculty_schedule_preferences_preference_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_faculty_schedule_preferences_preference_type ON public.faculty_schedule_preferences USING btree (preference_type);


--
-- Name: ix_faculty_weekly_overrides_effective_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_faculty_weekly_overrides_effective_date ON public.faculty_weekly_overrides USING btree (effective_date);


--
-- Name: ix_faculty_weekly_overrides_person_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_faculty_weekly_overrides_person_id ON public.faculty_weekly_overrides USING btree (person_id);


--
-- Name: ix_faculty_weekly_templates_activity_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_faculty_weekly_templates_activity_id ON public.faculty_weekly_templates USING btree (activity_id);


--
-- Name: ix_faculty_weekly_templates_person_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_faculty_weekly_templates_person_id ON public.faculty_weekly_templates USING btree (person_id);


--
-- Name: ix_feature_flag_audit_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_feature_flag_audit_created_at ON public.feature_flag_audit USING btree (created_at);


--
-- Name: ix_feature_flag_audit_flag_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_feature_flag_audit_flag_id ON public.feature_flag_audit USING btree (flag_id);


--
-- Name: ix_feature_flag_audit_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_feature_flag_audit_user_id ON public.feature_flag_audit USING btree (user_id);


--
-- Name: ix_feature_flag_evaluations_evaluated_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_feature_flag_evaluations_evaluated_at ON public.feature_flag_evaluations USING btree (evaluated_at);


--
-- Name: ix_feature_flag_evaluations_flag_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_feature_flag_evaluations_flag_id ON public.feature_flag_evaluations USING btree (flag_id);


--
-- Name: ix_feature_flag_evaluations_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_feature_flag_evaluations_user_id ON public.feature_flag_evaluations USING btree (user_id);


--
-- Name: ix_feature_flags_key; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_feature_flags_key ON public.feature_flags USING btree (key);


--
-- Name: ix_graduation_requirements_pgy_level; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_graduation_requirements_pgy_level ON public.graduation_requirements USING btree (pgy_level);


--
-- Name: ix_graduation_requirements_rotation_template_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_graduation_requirements_rotation_template_id ON public.graduation_requirements USING btree (rotation_template_id);


--
-- Name: ix_half_day_assignments_rotation_template_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_half_day_assignments_rotation_template_id ON public.half_day_assignments USING btree (rotation_template_id);


--
-- Name: ix_hopfield_positions_temporal; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_hopfield_positions_temporal ON public.hopfield_positions USING btree (person_id, block_number, academic_year);


--
-- Name: ix_hub_protection_plans_hub_faculty_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_hub_protection_plans_hub_faculty_id ON public.hub_protection_plans USING btree (hub_faculty_id);


--
-- Name: ix_hub_protection_plans_period; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_hub_protection_plans_period ON public.hub_protection_plans USING btree (period_start, period_end);


--
-- Name: ix_hub_protection_plans_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_hub_protection_plans_status ON public.hub_protection_plans USING btree (status);


--
-- Name: ix_import_batches_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_import_batches_created_at ON public.import_batches USING btree (created_at);


--
-- Name: ix_import_batches_file_hash; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_import_batches_file_hash ON public.import_batches USING btree (file_hash);


--
-- Name: ix_import_batches_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_import_batches_status ON public.import_batches USING btree (status);


--
-- Name: ix_import_staged_absences_batch_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_import_staged_absences_batch_id ON public.import_staged_absences USING btree (batch_id);


--
-- Name: ix_import_staged_absences_batch_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_import_staged_absences_batch_status ON public.import_staged_absences USING btree (batch_id, status);


--
-- Name: ix_import_staged_absences_date_range; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_import_staged_absences_date_range ON public.import_staged_absences USING btree (start_date, end_date);


--
-- Name: ix_import_staged_absences_matched_person_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_import_staged_absences_matched_person_id ON public.import_staged_absences USING btree (matched_person_id);


--
-- Name: ix_import_staged_absences_overlap_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_import_staged_absences_overlap_type ON public.import_staged_absences USING btree (overlap_type);


--
-- Name: ix_import_staged_absences_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_import_staged_absences_status ON public.import_staged_absences USING btree (status);


--
-- Name: ix_import_staged_absences_version_end_txn; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_import_staged_absences_version_end_txn ON public.import_staged_absences_version USING btree (end_transaction_id);


--
-- Name: ix_import_staged_absences_version_txn; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_import_staged_absences_version_txn ON public.import_staged_absences_version USING btree (transaction_id);


--
-- Name: ix_import_staged_assignments_assignment_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_import_staged_assignments_assignment_date ON public.import_staged_assignments USING btree (assignment_date);


--
-- Name: ix_import_staged_assignments_batch_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_import_staged_assignments_batch_id ON public.import_staged_assignments USING btree (batch_id);


--
-- Name: ix_import_staged_assignments_batch_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_import_staged_assignments_batch_status ON public.import_staged_assignments USING btree (batch_id, status);


--
-- Name: ix_import_staged_assignments_matched_person_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_import_staged_assignments_matched_person_id ON public.import_staged_assignments USING btree (matched_person_id);


--
-- Name: ix_import_staged_assignments_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_import_staged_assignments_status ON public.import_staged_assignments USING btree (status);


--
-- Name: ix_institutional_events_activity_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_institutional_events_activity_id ON public.institutional_events USING btree (activity_id);


--
-- Name: ix_institutional_events_applies_to; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_institutional_events_applies_to ON public.institutional_events USING btree (applies_to);


--
-- Name: ix_institutional_events_date_range; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_institutional_events_date_range ON public.institutional_events USING btree (start_date, end_date);


--
-- Name: ix_institutional_events_end_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_institutional_events_end_date ON public.institutional_events USING btree (end_date);


--
-- Name: ix_institutional_events_event_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_institutional_events_event_type ON public.institutional_events USING btree (event_type);


--
-- Name: ix_institutional_events_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_institutional_events_is_active ON public.institutional_events USING btree (is_active);


--
-- Name: ix_institutional_events_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_institutional_events_name ON public.institutional_events USING btree (name);


--
-- Name: ix_institutional_events_start_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_institutional_events_start_date ON public.institutional_events USING btree (start_date);


--
-- Name: ix_ip_blacklists_ip_address; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ip_blacklists_ip_address ON public.ip_blacklists USING btree (ip_address);


--
-- Name: ix_ip_whitelists_ip_address; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ip_whitelists_ip_address ON public.ip_whitelists USING btree (ip_address);


--
-- Name: ix_job_executions_job_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_job_executions_job_id ON public.job_executions USING btree (job_id);


--
-- Name: ix_job_executions_job_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_job_executions_job_name ON public.job_executions USING btree (job_name);


--
-- Name: ix_job_executions_started_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_job_executions_started_at ON public.job_executions USING btree (started_at);


--
-- Name: ix_job_executions_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_job_executions_status ON public.job_executions USING btree (status);


--
-- Name: ix_metrics_name_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_metrics_name_time ON public.metric_snapshots USING btree (metric_name, computed_at);


--
-- Name: ix_metrics_version_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_metrics_version_category ON public.metric_snapshots USING btree (schedule_version_id, category);


--
-- Name: ix_oauth2_clients_client_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_oauth2_clients_client_id ON public.oauth2_clients USING btree (client_id);


--
-- Name: ix_person_academic_years_academic_year; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_person_academic_years_academic_year ON public.person_academic_years USING btree (academic_year);


--
-- Name: ix_person_academic_years_person_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_person_academic_years_person_id ON public.person_academic_years USING btree (person_id);


--
-- Name: ix_preference_trails_faculty_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_preference_trails_faculty_id ON public.preference_trails USING btree (faculty_id);


--
-- Name: ix_preference_trails_slot_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_preference_trails_slot_type ON public.preference_trails USING btree (slot_type);


--
-- Name: ix_preference_trails_strength; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_preference_trails_strength ON public.preference_trails USING btree (strength);


--
-- Name: ix_preference_trails_trail_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_preference_trails_trail_type ON public.preference_trails USING btree (trail_type);


--
-- Name: ix_rag_documents_doc_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_rag_documents_doc_type ON public.rag_documents USING btree (doc_type);


--
-- Name: ix_rag_documents_embedding_hnsw; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_rag_documents_embedding_hnsw ON public.rag_documents USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: ix_rag_documents_metadata; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_rag_documents_metadata ON public.rag_documents USING gin (metadata_);


--
-- Name: ix_request_signatures_signature_hash; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_request_signatures_signature_hash ON public.request_signatures USING btree (signature_hash);


--
-- Name: ix_resident_weekly_requirements_template_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_resident_weekly_requirements_template_id ON public.resident_weekly_requirements USING btree (rotation_template_id);


--
-- Name: ix_rotation_activity_req_activity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_rotation_activity_req_activity ON public.rotation_activity_requirements USING btree (activity_id);


--
-- Name: ix_rotation_activity_req_template; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_rotation_activity_req_template ON public.rotation_activity_requirements USING btree (rotation_template_id);


--
-- Name: ix_rotation_preferences_rotation_template_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_rotation_preferences_rotation_template_id ON public.rotation_preferences USING btree (rotation_template_id);


--
-- Name: ix_rotation_templates_half_components; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_rotation_templates_half_components ON public.rotation_templates USING btree (first_half_component_id, second_half_component_id) WHERE (is_block_half_rotation = true);


--
-- Name: ix_rotation_templates_is_archived; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_rotation_templates_is_archived ON public.rotation_templates USING btree (is_archived);


--
-- Name: ix_rotation_templates_template_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_rotation_templates_template_category ON public.rotation_templates USING btree (template_category);


--
-- Name: ix_schedule_drafts_version_end_transaction_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_schedule_drafts_version_end_transaction_id ON public.schedule_drafts_version USING btree (end_transaction_id);


--
-- Name: ix_schedule_drafts_version_operation_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_schedule_drafts_version_operation_type ON public.schedule_drafts_version USING btree (operation_type);


--
-- Name: ix_schedule_drafts_version_transaction_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_schedule_drafts_version_transaction_id ON public.schedule_drafts_version USING btree (transaction_id);


--
-- Name: ix_scheduled_jobs_enabled; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_scheduled_jobs_enabled ON public.scheduled_jobs USING btree (enabled);


--
-- Name: ix_scheduled_jobs_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_scheduled_jobs_name ON public.scheduled_jobs USING btree (name);


--
-- Name: ix_scheduled_jobs_next_run_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_scheduled_jobs_next_run_time ON public.scheduled_jobs USING btree (next_run_time);


--
-- Name: ix_survey_availability_next; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_survey_availability_next ON public.survey_availability USING btree (next_available_at);


--
-- Name: ix_survey_responses_temporal; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_survey_responses_temporal ON public.survey_responses USING btree (survey_id, block_number, academic_year);


--
-- Name: ix_swap_approvals_swap_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_swap_approvals_swap_id ON public.swap_approvals USING btree (swap_id);


--
-- Name: ix_swap_records_source_faculty_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_swap_records_source_faculty_id ON public.swap_records USING btree (source_faculty_id);


--
-- Name: ix_swap_records_source_week; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_swap_records_source_week ON public.swap_records USING btree (source_week);


--
-- Name: ix_swap_records_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_swap_records_status ON public.swap_records USING btree (status);


--
-- Name: ix_swap_records_target_faculty_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_swap_records_target_faculty_id ON public.swap_records USING btree (target_faculty_id);


--
-- Name: ix_trail_signals_recorded_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_trail_signals_recorded_at ON public.trail_signals USING btree (recorded_at);


--
-- Name: ix_trail_signals_trail_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_trail_signals_trail_id ON public.trail_signals USING btree (trail_id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_person_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_person_id ON public.users USING btree (person_id);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: ix_weekly_patterns_activity_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_weekly_patterns_activity_id ON public.weekly_patterns USING btree (activity_id);


--
-- Name: ix_weekly_patterns_rotation_template_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_weekly_patterns_rotation_template_id ON public.weekly_patterns USING btree (rotation_template_id);


--
-- Name: task_history_agent_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX task_history_agent_idx ON public.task_history USING btree (agent_used, created_at DESC);


--
-- Name: task_history_embedding_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX task_history_embedding_idx ON public.task_history USING hnsw (embedding public.vector_cosine_ops);


--
-- Name: uq_call_overrides_active_assignment; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_call_overrides_active_assignment ON public.call_overrides USING btree (call_assignment_id) WHERE (is_active = true);


--
-- Name: uq_resident_block_half; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_resident_block_half ON public.block_assignments USING btree (block_number, academic_year, resident_id, block_half);


--
-- Name: uq_schedule_overrides_active_assignment; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_schedule_overrides_active_assignment ON public.schedule_overrides USING btree (half_day_assignment_id) WHERE (is_active = true);


--
-- Name: absence_version absence_version_end_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.absence_version
    ADD CONSTRAINT absence_version_end_transaction_id_fkey FOREIGN KEY (end_transaction_id) REFERENCES public.transaction(id);


--
-- Name: absence_version absence_version_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.absence_version
    ADD CONSTRAINT absence_version_transaction_id_fkey FOREIGN KEY (transaction_id) REFERENCES public.transaction(id);


--
-- Name: absences absences_person_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.absences
    ADD CONSTRAINT absences_person_id_fkey FOREIGN KEY (person_id) REFERENCES public.people(id) ON DELETE CASCADE;


--
-- Name: absences_version absences_version_end_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.absences_version
    ADD CONSTRAINT absences_version_end_transaction_id_fkey FOREIGN KEY (end_transaction_id) REFERENCES public.transaction(id);


--
-- Name: activity_log activity_log_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activity_log
    ADD CONSTRAINT activity_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: api_keys api_keys_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_keys
    ADD CONSTRAINT api_keys_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: api_keys api_keys_revoked_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_keys
    ADD CONSTRAINT api_keys_revoked_by_id_fkey FOREIGN KEY (revoked_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: api_keys api_keys_rotated_from_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_keys
    ADD CONSTRAINT api_keys_rotated_from_id_fkey FOREIGN KEY (rotated_from_id) REFERENCES public.api_keys(id) ON DELETE SET NULL;


--
-- Name: api_keys api_keys_rotated_to_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_keys
    ADD CONSTRAINT api_keys_rotated_to_id_fkey FOREIGN KEY (rotated_to_id) REFERENCES public.api_keys(id) ON DELETE SET NULL;


--
-- Name: approval_record approval_record_actor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_record
    ADD CONSTRAINT approval_record_actor_id_fkey FOREIGN KEY (actor_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: approval_record approval_record_prev_record_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.approval_record
    ADD CONSTRAINT approval_record_prev_record_id_fkey FOREIGN KEY (prev_record_id) REFERENCES public.approval_record(id) ON DELETE SET NULL;


--
-- Name: assignment_backups assignment_backups_draft_assignment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.assignment_backups
    ADD CONSTRAINT assignment_backups_draft_assignment_id_fkey FOREIGN KEY (draft_assignment_id) REFERENCES public.schedule_draft_assignments(id) ON DELETE CASCADE;


--
-- Name: assignments assignments_person_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.assignments
    ADD CONSTRAINT assignments_person_id_fkey FOREIGN KEY (person_id) REFERENCES public.people(id) ON DELETE CASCADE;


--
-- Name: assignments assignments_rotation_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.assignments
    ADD CONSTRAINT assignments_rotation_template_id_fkey FOREIGN KEY (rotation_template_id) REFERENCES public.rotation_templates(id);


--
-- Name: annual_rotation_assignments fk_annual_rotation_assignments_person_id_people; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.annual_rotation_assignments
    ADD CONSTRAINT fk_annual_rotation_assignments_person_id_people FOREIGN KEY (person_id) REFERENCES public.people(id);


--
-- Name: annual_rotation_assignments fk_annual_rotation_assignments_plan_id_annual_rotation_plans; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.annual_rotation_assignments
    ADD CONSTRAINT fk_annual_rotation_assignments_plan_id_annual_rotation_plans FOREIGN KEY (plan_id) REFERENCES public.annual_rotation_plans(id) ON DELETE CASCADE;


--
-- Name: annual_rotation_plans fk_annual_rotation_plans_created_by_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.annual_rotation_plans
    ADD CONSTRAINT fk_annual_rotation_plans_created_by_users FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: game_theory_matches fk_game_theory_matches_strategy1_id_game_theory_strategies; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game_theory_matches
    ADD CONSTRAINT fk_game_theory_matches_strategy1_id_game_theory_strategies FOREIGN KEY (strategy1_id) REFERENCES public.game_theory_strategies(id);


--
-- Name: game_theory_matches fk_game_theory_matches_strategy2_id_game_theory_strategies; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game_theory_matches
    ADD CONSTRAINT fk_game_theory_matches_strategy2_id_game_theory_strategies FOREIGN KEY (strategy2_id) REFERENCES public.game_theory_strategies(id);


--
-- Name: game_theory_matches fk_game_theory_matches_tournament_id_game_theory_tournaments; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game_theory_matches
    ADD CONSTRAINT fk_game_theory_matches_tournament_id_game_theory_tournaments FOREIGN KEY (tournament_id) REFERENCES public.game_theory_tournaments(id);


--
-- Name: game_theory_validations fk_game_theory_validations_strategy_id_game_theory_strategies; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.game_theory_validations
    ADD CONSTRAINT fk_game_theory_validations_strategy_id_game_theory_strategies FOREIGN KEY (strategy_id) REFERENCES public.game_theory_strategies(id);


--
-- Name: graduation_requirements fk_graduation_requirements_rotation_template_id_rotatio_9054; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.graduation_requirements
    ADD CONSTRAINT fk_graduation_requirements_rotation_template_id_rotatio_9054 FOREIGN KEY (rotation_template_id) REFERENCES public.rotation_templates(id) ON DELETE CASCADE;


--
-- Name: half_day_assignments fk_half_day_assignments_rotation_template_id_rotation_templates; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.half_day_assignments
    ADD CONSTRAINT fk_half_day_assignments_rotation_template_id_rotation_templates FOREIGN KEY (rotation_template_id) REFERENCES public.rotation_templates(id) ON DELETE SET NULL;


--
-- Name: import_batches fk_import_batches_parent_batch_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.import_batches
    ADD CONSTRAINT fk_import_batches_parent_batch_id FOREIGN KEY (parent_batch_id) REFERENCES public.import_batches(id) ON DELETE CASCADE;


--
-- Name: learner_assignments fk_learner_assignments_block_id_blocks; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learner_assignments
    ADD CONSTRAINT fk_learner_assignments_block_id_blocks FOREIGN KEY (block_id) REFERENCES public.blocks(id) ON DELETE CASCADE;


--
-- Name: learner_assignments fk_learner_assignments_learner_id_people; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learner_assignments
    ADD CONSTRAINT fk_learner_assignments_learner_id_people FOREIGN KEY (learner_id) REFERENCES public.people(id) ON DELETE CASCADE;


--
-- Name: learner_assignments fk_learner_assignments_parent_assignment_id_assignments; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learner_assignments
    ADD CONSTRAINT fk_learner_assignments_parent_assignment_id_assignments FOREIGN KEY (parent_assignment_id) REFERENCES public.assignments(id) ON DELETE CASCADE;


--
-- Name: learner_to_tracks fk_learner_to_tracks_learner_id_people; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learner_to_tracks
    ADD CONSTRAINT fk_learner_to_tracks_learner_id_people FOREIGN KEY (learner_id) REFERENCES public.people(id) ON DELETE CASCADE;


--
-- Name: learner_to_tracks fk_learner_to_tracks_track_id_learner_tracks; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learner_to_tracks
    ADD CONSTRAINT fk_learner_to_tracks_track_id_learner_tracks FOREIGN KEY (track_id) REFERENCES public.learner_tracks(id) ON DELETE CASCADE;


--
-- Name: person_academic_years fk_person_academic_years_person_id_people; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.person_academic_years
    ADD CONSTRAINT fk_person_academic_years_person_id_people FOREIGN KEY (person_id) REFERENCES public.people(id) ON DELETE CASCADE;


--
-- Name: users fk_users_person_id_people; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT fk_users_person_id_people FOREIGN KEY (person_id) REFERENCES public.people(id) ON DELETE SET NULL;


--
-- PostgreSQL database dump complete
--

\unrestrict UpHG3zmXP5cCveXS6gsH8Oaa22e3MPHmDJc42l7XBlTcetA26gaSEfMBYQVePFF
