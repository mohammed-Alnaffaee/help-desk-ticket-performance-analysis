WITH interval_totals AS (
    SELECT
        ticket_id,
        SUM(b_counted_seconds) / 3600.0 AS b_hours,
        SUM(a_counted_seconds) / 3600.0 AS a_hours
    FROM staging.status_intervals
    GROUP BY ticket_id
)

SELECT
    COUNT(*) AS total_tickets,

    COUNT(*) FILTER (
        WHERE i.ticket_id IS NULL
    ) AS tickets_without_intervals,

    COUNT(*) FILTER (
        WHERE ABS(
            COALESCE(i.b_hours, 0)
            - o.b_observed_counted_hours
        ) > 1.0 / 3600
    ) AS b_mismatches,

    COUNT(*) FILTER (
        WHERE ABS(
            COALESCE(i.a_hours, 0)
            - o.a_observed_counted_hours
        ) > 1.0 / 3600
    ) AS a_mismatches

FROM staging.ticket_outcomes o
LEFT JOIN interval_totals i
    ON o.ticket_id = i.ticket_id;