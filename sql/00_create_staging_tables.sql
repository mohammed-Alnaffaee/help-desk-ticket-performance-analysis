-- Fresh-database staging schema for the two project-generated CSV files.
-- Run once in an empty database before importing records.
-- Column order in staging.ticket_outcomes matches python/prepare_postgres_csv.py TARGET.
-- Column order in staging.status_intervals matches the exporter in helpdesk_domain3_measurement.py.
-- Does not drop, overwrite, or truncate any existing data.

CREATE SCHEMA IF NOT EXISTS staging;

CREATE TABLE IF NOT EXISTS staging.ticket_outcomes (
    ticket_id BIGINT PRIMARY KEY,
    created_utc TIMESTAMPTZ NOT NULL,
    source_ended_utc TIMESTAMPTZ,
    source_resolution_utc TIMESTAMPTZ,
    source_final_status TEXT,
    last_observed_status TEXT,
    last_observed_status_time_utc TIMESTAMPTZ,
    observed_status_events INTEGER,
    observed_closed_entries INTEGER,
    observed_reopen_entries INTEGER,
    b_observed_counted_hours DOUBLE PRECISION,
    a_observed_counted_hours DOUBLE PRECISION,
    b_minus_a_observed_hours DOUBLE PRECISION,
    b_first_72h_boundary_utc TIMESTAMPTZ,
    a_first_72h_boundary_utc TIMESTAMPTZ,
    b_observed_threshold_exceeded BOOLEAN,
    a_observed_threshold_exceeded BOOLEAN,
    b_confirmed_class TEXT NOT NULL,
    has_observed_closure_for_last_episode BOOLEAN,
    has_valid_events_after_ended BOOLEAN,
    has_abnormal_exit_from_closed BOOLEAN,
    has_semantic_uncertainty BOOLEAN,
    stage_reconciliation_error_gt60s BOOLEAN,
    source_final_disagrees_with_last_observed_status BOOLEAN,
    resolution_date_missing BOOLEAN,
    hypothetical_2023_03_14_235959_utc_extra_hours DOUBLE PRECISION,
    hypothetical_b_counted_hours DOUBLE PRECISION,
    hypothetical_b_threshold_exceeded BOOLEAN,
    quality_disposition TEXT,
    qa_flags TEXT,
    issue_type TEXT,
    issue_priority TEXT,
    issue_proj TEXT,
    creation_year INTEGER,
    has_special_done_cancelled BOOLEAN
);

CREATE TABLE IF NOT EXISTS staging.status_intervals (
    ticket_id BIGINT NOT NULL REFERENCES staging.ticket_outcomes(ticket_id),
    start_utc TIMESTAMPTZ NOT NULL,
    end_utc TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL,
    duration_seconds DOUBLE PRECISION NOT NULL,
    b_counted_seconds DOUBLE PRECISION NOT NULL,
    a_counted_seconds DOUBLE PRECISION NOT NULL,
    is_after_source_ended BOOLEAN,
    is_pause BOOLEAN,
    is_closed_excluded BOOLEAN,
    CONSTRAINT status_intervals_positive CHECK (
        end_utc > start_utc AND duration_seconds > 0
        AND b_counted_seconds >= 0 AND a_counted_seconds >= 0
    )
);

CREATE INDEX IF NOT EXISTS idx_status_intervals_ticket_id
    ON staging.status_intervals (ticket_id);

CREATE INDEX IF NOT EXISTS idx_status_intervals_status
    ON staging.status_intervals (status);
