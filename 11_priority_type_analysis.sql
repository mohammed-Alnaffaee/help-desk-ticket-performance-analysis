WITH priority_type AS (
    SELECT
        issue_type,
        issue_priority,
        COUNT(*) AS total_tickets,
        COUNT(*) FILTER (
            WHERE b_confirmed_class = 'confirmed_breached'
        ) AS breached_tickets,
        COUNT(*) FILTER (
            WHERE b_confirmed_class IN (
                'confirmed_breached',
                'closed_without_breach'
            )
        ) AS evaluable_tickets
    FROM staging.ticket_outcomes
    GROUP BY issue_type, issue_priority
)
SELECT
    issue_type,
    issue_priority,
    total_tickets,
    breached_tickets,
    evaluable_tickets,
    total_tickets - evaluable_tickets AS excluded_tickets,
    CASE
        WHEN evaluable_tickets >= 50 THEN
            ROUND(
                100.0 * breached_tickets
                / NULLIF(evaluable_tickets, 0), 2
            )
        ELSE NULL
    END AS breach_rate_pct
FROM priority_type
ORDER BY issue_type, evaluable_tickets DESC;