SELECT
    (
        SELECT COUNT(*)
        FROM staging.status_intervals
        WHERE b_counted_seconds > 0
          AND (
              status IN (
                  'closed',
                  'waiting',
                  'pending_customer_approval'
              )
              OR is_pause IS TRUE
              OR is_closed_excluded IS TRUE
          )
    ) AS invalid_counted_intervals,

    (
        SELECT COUNT(*)
        FROM staging.ticket_outcomes
        WHERE b_confirmed_class = 'confirmed_breached'
          AND b_observed_threshold_exceeded IS DISTINCT FROM TRUE
    ) AS breach_flag_mismatches,

    (
        SELECT COUNT(*)
        FROM staging.ticket_outcomes
        WHERE b_confirmed_class = 'closed_without_breach'
          AND b_observed_threshold_exceeded IS TRUE
    ) AS closed_class_conflicts,

    (
        SELECT COUNT(*)
        FROM staging.ticket_outcomes
        WHERE b_confirmed_class = 'confirmed_breached'
          AND has_semantic_uncertainty IS TRUE
    ) AS confirmed_breaches_with_semantic_flags;
	