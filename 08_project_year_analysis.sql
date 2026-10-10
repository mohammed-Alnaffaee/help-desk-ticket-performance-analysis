SELECT
    issue_proj,
    creation_year,

    COUNT(*) AS total_tickets,

    COUNT(*) FILTER (
        WHERE b_confirmed_class = 'confirmed_breached'
    ) AS breached_tickets,

    COUNT(*) FILTER (
        WHERE b_confirmed_class IN (
            'confirmed_breached',
            'closed_without_breach'
        )
    ) AS evaluable_tickets,

    COUNT(*) FILTER (
        WHERE b_confirmed_class NOT IN (
            'confirmed_breached',
            'closed_without_breach'
        )
    ) AS excluded_tickets,

    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE b_confirmed_class = 'confirmed_breached'
        )
        / NULLIF(
            COUNT(*) FILTER (
                WHERE b_confirmed_class IN (
                    'confirmed_breached',
                    'closed_without_breach'
                )
            ), 0
        ), 2
    ) AS breach_rate_pct

FROM staging.ticket_outcomes

WHERE issue_proj IN (
    'C06hg2xcu',
    'C06hgfz_x',
    'C06hqzcz0'
)

GROUP BY issue_proj, creation_year

ORDER BY issue_proj, creation_year;