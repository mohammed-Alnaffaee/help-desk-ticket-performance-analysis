WITH resolved_tickets AS (
    SELECT
        ticket_id,
        SUM(b_counted_seconds) / 3600.0
            AS resolved_hours
    FROM staging.status_intervals
    WHERE status = 'resolved'
    GROUP BY ticket_id
)

SELECT
    o.ticket_id,
    o.issue_proj,
    ROUND(r.resolved_hours::numeric, 2)
        AS resolved_hours,
    ROUND(o.b_observed_counted_hours::numeric, 2)
        AS total_b_hours,
    o.b_confirmed_class,
    o.qa_flags

FROM resolved_tickets r
JOIN staging.ticket_outcomes o
    ON r.ticket_id = o.ticket_id

WHERE o.issue_proj = 'C06hqzcz0'
  AND o.b_confirmed_class = 'confirmed_breached'

ORDER BY r.resolved_hours DESC
LIMIT 10;