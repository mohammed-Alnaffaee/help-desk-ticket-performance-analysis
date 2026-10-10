SELECT
    issue_proj,

    COUNT(*) AS evaluable_tickets,

    COUNT(*) FILTER (
        WHERE a_observed_threshold_exceeded = TRUE
    ) AS a_breaches,

    COUNT(*) FILTER (
        WHERE b_observed_threshold_exceeded = TRUE
    ) AS b_breaches,

    COUNT(*) FILTER (
        WHERE b_observed_threshold_exceeded = TRUE
          AND a_observed_threshold_exceeded IS NOT TRUE
    ) AS b_only_breaches,

    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE a_observed_threshold_exceeded = TRUE
        ) / NULLIF(COUNT(*), 0), 2
    ) AS a_rate_pct,

    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE b_observed_threshold_exceeded = TRUE
        ) / NULLIF(COUNT(*), 0), 2
    ) AS b_rate_pct

FROM staging.ticket_outcomes

WHERE issue_proj IN (
    'C06hg2xcu',
    'C06hgfz_x',
    'C06hqzcz0'
)
AND b_confirmed_class IN (
    'confirmed_breached',
    'closed_without_breach'
)

GROUP BY issue_proj
ORDER BY b_only_breaches DESC;