-- Independent fresh-database import smoke check.
-- Fail fast if CSV import schema or derived-count expectations are wrong.

DO $$
DECLARE
    n_tickets BIGINT;
    n_intervals BIGINT;
    n_with_intervals BIGINT;
    n_breaches BIGINT;
    n_evaluable BIGINT;
    n_workflow_groups BIGINT;
    n_workflow_tickets BIGINT;
    n_invalid BIGINT;
BEGIN
    SELECT COUNT(*),
           COUNT(*) FILTER (WHERE b_confirmed_class = 'confirmed_breached'),
           COUNT(*) FILTER (WHERE b_confirmed_class IN ('confirmed_breached', 'closed_without_breach'))
      INTO n_tickets, n_breaches, n_evaluable
      FROM staging.ticket_outcomes;
    SELECT COUNT(*), COUNT(DISTINCT ticket_id)
      INTO n_intervals, n_with_intervals
      FROM staging.status_intervals;

    IF n_tickets <> 19714 OR n_breaches <> 8662 OR n_evaluable <> 19605 THEN
        RAISE EXCEPTION 'Unexpected ticket outcomes: tickets %, breached %, evaluable %',
            n_tickets, n_breaches, n_evaluable;
    END IF;
    IF n_intervals <> 81931 OR n_with_intervals <> 19711 THEN
        RAISE EXCEPTION 'Unexpected status intervals: rows %, tickets %',
            n_intervals, n_with_intervals;
    END IF;

    SELECT COUNT(*) INTO n_invalid
      FROM staging.status_intervals
     WHERE end_utc <= start_utc OR duration_seconds <= 0
        OR b_counted_seconds < 0 OR a_counted_seconds < 0
        OR (status IN ('closed', 'waiting', 'pending_customer_approval')
            AND b_counted_seconds > 0);
    IF n_invalid <> 0 THEN
        RAISE EXCEPTION 'Invalid or counted paused intervals: %', n_invalid;
    END IF;

    SELECT COUNT(*), COUNT(DISTINCT ticket_id)
      INTO n_workflow_groups, n_workflow_tickets
      FROM analytics.vw_ticket_workflow;
    IF n_workflow_groups <> 70009 OR n_workflow_tickets <> 19711 THEN
        RAISE EXCEPTION 'Unexpected workflow grouping: rows %, tickets %',
            n_workflow_groups, n_workflow_tickets;
    END IF;

    RAISE NOTICE 'PASS: tickets %, intervals %, evaluable %, breached %, workflow groups %',
        n_tickets, n_intervals, n_evaluable, n_breaches, n_workflow_groups;
END
$$;
