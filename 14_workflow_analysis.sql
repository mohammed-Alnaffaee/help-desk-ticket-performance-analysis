WITH ticket_status AS (
    SELECT
        i.ticket_id,
        i.status,
        SUM(i.b_counted_seconds) / 3600.0
            AS counted_hours
    FROM staging.status_intervals i
    JOIN staging.ticket_outcomes o
        ON i.ticket_id = o.ticket_id
    WHERE o.b_confirmed_class = 'confirmed_breached'
      AND i.b_counted_seconds > 0
    GROUP BY i.ticket_id, i.status
),

status_summary AS (
    SELECT
        status,
        COUNT(*) AS affected_tickets,
        SUM(counted_hours) AS total_counted_hours,
        PERCENTILE_CONT(0.5) WITHIN GROUP (
            ORDER BY counted_hours
        ) AS median_hours_per_ticket
    FROM ticket_status
    GROUP BY status
)

SELECT
    status,
    affected_tickets,
    ROUND(total_counted_hours::numeric, 2)
        AS total_counted_hours,
    ROUND(median_hours_per_ticket::numeric, 2)
        AS median_hours_per_ticket
FROM status_summary
ORDER BY total_counted_hours DESC
LIMIT 10;