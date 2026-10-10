WITH project_summary AS (
    SELECT
        issue_proj,
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
    GROUP BY issue_proj
)

SELECT
    issue_proj,
    total_tickets,
    breached_tickets,
    evaluable_tickets,
    total_tickets - evaluable_tickets AS excluded_tickets,

    ROUND(
        100.0 * breached_tickets
        / NULLIF(evaluable_tickets, 0), 2
    ) AS breach_rate_pct

FROM project_summary
ORDER BY breached_tickets DESC, issue_proj
LIMIT 10;