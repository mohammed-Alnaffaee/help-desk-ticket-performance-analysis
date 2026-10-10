"""Independent, fast checks of already-exported ticket and interval CSVs.
Usage: python verify_exported_results.py [export_dir]
"""
from pathlib import Path
import sys,json
import numpy as np,pandas as pd
D=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent
c=pd.read_csv(D/'ticket_outcomes_conditional.csv')
i=pd.read_csv(D/'observed_status_intervals.csv')
s=json.loads((D/'validation_summary.json').read_text())
assert len(c)==19714 and c.ticket_id.nunique()==19714
assert len(i)==81931
assert (c.B_observed_counted_hours+1e-8>=c.A_observed_counted_hours).all()
assert i.duration_seconds.ge(0).all()
assert i.loc[i.status.isin(['closed','waiting','pending_customer_approval']),'B_counted_seconds'].eq(0).all()
agg=i.groupby('ticket_id').B_counted_seconds.sum()/3600
assert np.allclose(agg.reindex(c.ticket_id,fill_value=0).values,c.B_observed_counted_hours.values,rtol=0,atol=1e-5)
cnt=c.B_confirmed_class.value_counts()
assert int(cnt.confirmed_breached)==8662 and int(cnt.closed_without_breach)==10943
assert int((~c.B_confirmed_class.isin(['confirmed_breached','closed_without_breach'])).sum())==109
assert cnt.sum()==19714
assert int(c.stage_reconciliation_error_gt60s.sum())==7
assert int(c.source_final_disagrees_with_last_observed_status.sum())==2
assert int(c.has_valid_events_after_ended.sum())==111
assert int(c.has_semantic_uncertainty.sum())==119
assert int(c.has_special_done_cancelled.sum())==69
assert int(c.resolution_date_missing.sum())==254
assert int((c.hypothetical_B_threshold_exceeded&~c.B_observed_threshold_exceeded).sum())==32
assert s['conditional_breach_rate_pct']==round(100*8662/19605,4)
print('RESULT: PASS 16 structural/reconciliation/denominator/censoring validation assertions')
print('N=19,714; intervals=81,931; confirmed_breached=8,662; closed_without=10,943; withheld=109')
print('Conditional rate=44.1826%; hypothetical added flags=32, not certified breaches')
