SELECT
    COUNT(*) AS total_intervals,

    COUNT(DISTINCT ticket_id) AS unique_tickets,

    COUNT(*) FILTER (
        WHERE ticket_id IS NULL
           OR start_utc IS NULL
           OR end_utc IS NULL
           OR status IS NULL
    ) AS missing_required_fields,

    COUNT(*) FILTER (
        WHERE end_utc <= start_utc
           OR duration_seconds <= 0
           OR b_counted_seconds < 0
           OR a_counted_seconds < 0
    ) AS invalid_durations

FROM staging.status_intervals;