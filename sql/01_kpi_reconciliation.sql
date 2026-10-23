SELECT
    COUNT(*) FILTER (
        WHERE b_confirmed_class = 'confirmed_breached'
    ) AS breached_tickets,

    COUNT(*) FILTER (
        WHERE b_confirmed_class IN (
            'confirmed_breached',
            'closed_without_breach'
        )
    ) AS evaluable_tickets,

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
        4
    ) AS conditional_breach_rate_pct

FROM staging.ticket_outcomes;