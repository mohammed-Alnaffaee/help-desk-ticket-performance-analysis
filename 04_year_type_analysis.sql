WITH yearly_types AS (
    SELECT
        creation_year,
        issue_type,
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
    GROUP BY creation_year, issue_type
)

SELECT
    creation_year,
    issue_type,
    total_tickets,

    ROUND(
        100.0 * total_tickets
        / SUM(total_tickets) OVER (
            PARTITION BY creation_year
        ), 2
    ) AS type_share_pct,

    breached_tickets,
    evaluable_tickets,
    total_tickets - evaluable_tickets AS excluded_tickets,

    ROUND(
        100.0 * breached_tickets
        / NULLIF(evaluable_tickets, 0), 2
    ) AS breach_rate_pct

FROM yearly_types
ORDER BY creation_year, issue_type;