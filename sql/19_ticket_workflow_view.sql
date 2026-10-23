CREATE OR REPLACE VIEW analytics.vw_ticket_workflow AS
SELECT
    ticket_id,
    status,
    COUNT(*) AS interval_count,

    SUM(duration_seconds) / 3600.0
        AS observed_hours,

    SUM(b_counted_seconds) / 3600.0
        AS b_counted_hours,

    SUM(a_counted_seconds) / 3600.0
        AS a_counted_hours

FROM staging.status_intervals

GROUP BY ticket_id, status;


-- Validate the View
SELECT
    COUNT(*) AS ticket_status_rows,

    COUNT(DISTINCT ticket_id)
        AS unique_tickets,

    COUNT(*) FILTER (
        WHERE b_counted_hours < 0
           OR a_counted_hours < 0
    ) AS negative_hours,

    COUNT(*) FILTER (
        WHERE status IN (
            'closed',
            'waiting',
            'pending_customer_approval'
        )
        AND b_counted_hours > 0
    ) AS invalid_pause_hours

FROM analytics.vw_ticket_workflow;