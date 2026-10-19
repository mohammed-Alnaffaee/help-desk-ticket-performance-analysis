SELECT
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
        WHERE b_confirmed_class IN (
            'censored_no_proven_breach',
            'indeterminate_semantic',
            'indeterminate_data_quality'
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
        ),
        2
    ) AS breach_rate_pct

FROM staging.ticket_outcomes
GROUP BY creation_year
ORDER BY creation_year;