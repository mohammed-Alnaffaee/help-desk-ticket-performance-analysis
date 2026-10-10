WITH ticket_status AS (
    SELECT
        o.issue_proj,
        i.ticket_id,
        i.status,
        SUM(i.b_counted_seconds) / 3600.0 AS counted_hours

    FROM staging.status_intervals i
    JOIN staging.ticket_outcomes o
        ON i.ticket_id = o.ticket_id

    WHERE o.b_confirmed_class = 'confirmed_breached'
      AND o.issue_proj IN (
          'C06hg2xcu',
          'C06hgfz_x',
          'C06hqzcz0'
      )
      AND i.b_counted_seconds > 0
      AND i.status IN (
          'in_progress',
          'validation',
          'pending_deployment',
          'resolved',
          'resolved_under_monitoring'
      )

    GROUP BY o.issue_proj, i.ticket_id, i.status
)

SELECT
    issue_proj,
    status,
    COUNT(*) AS affected_tickets,

    ROUND(
        PERCENTILE_CONT(0.5) WITHIN GROUP (
            ORDER BY counted_hours
        )::numeric, 2
    ) AS median_hours,

    ROUND(
        PERCENTILE_CONT(0.9) WITHIN GROUP (
            ORDER BY counted_hours
        )::numeric, 2
    ) AS p90_hours

FROM ticket_status
GROUP BY issue_proj, status
HAVING COUNT(*) >= 10
ORDER BY issue_proj, affected_tickets DESC;