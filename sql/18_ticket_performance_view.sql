CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE VIEW analytics.vw_ticket_performance AS
SELECT
    ticket_id,
    created_utc,
    creation_year,
    issue_proj,
    issue_type,
    issue_priority,
    b_confirmed_class,
    b_observed_counted_hours,
    a_observed_counted_hours,
    qa_flags,

    CASE
        WHEN b_confirmed_class IN (
            'confirmed_breached',
            'closed_without_breach'
        ) THEN 1
        ELSE 0
    END AS evaluable_flag,

    CASE
        WHEN b_confirmed_class = 'confirmed_breached'
        THEN 1
        ELSE 0
    END AS breached_flag

FROM staging.ticket_outcomes;

-- Verify the view
SELECT
    COUNT(*) AS total_tickets,
    SUM(evaluable_flag) AS evaluable_tickets,
    SUM(breached_flag) AS breached_tickets
FROM analytics.vw_ticket_performance;