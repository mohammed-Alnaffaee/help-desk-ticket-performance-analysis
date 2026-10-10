WITH type_summary AS (
    SELECT
        creation_year,
        issue_type,
        COUNT(*) FILTER (
            WHERE b_confirmed_class IN (
                'confirmed_breached',
                'closed_without_breach'
            )
        ) AS evaluable,
        COUNT(*) FILTER (
            WHERE b_confirmed_class = 'confirmed_breached'
        ) AS breached
    FROM staging.ticket_outcomes
    WHERE creation_year IN (2021, 2022)
    GROUP BY creation_year, issue_type
),

mix_2021 AS (
    SELECT
        issue_type,
        evaluable::numeric
            / SUM(evaluable) OVER () AS weight_2021
    FROM type_summary
    WHERE creation_year = 2021
),

rates_2022 AS (
    SELECT
        issue_type,
        breached::numeric
            / NULLIF(evaluable, 0) AS rate_2022
    FROM type_summary
    WHERE creation_year = 2022
)

SELECT
    ROUND(
        100 * SUM(m.weight_2021 * r.rate_2022), 2
    ) AS adjusted_2022_breach_rate_pct
FROM mix_2021 m
JOIN rates_2022 r USING (issue_type);