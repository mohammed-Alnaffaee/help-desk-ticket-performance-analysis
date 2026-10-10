import unittest
import pandas as pd
from helpdesk_domain3_measurement import one_ticket,THRESHOLD
BASE=pd.Timestamp('2022-01-01T00:00:00Z')
def H(hours):return BASE+pd.Timedelta(hours=hours)
def ticket(changes,final='closed',end_hours=5, resolution=None, stage=False):
    row=pd.Series({'id':1,'issue_created_utc':H(0),'ended_utc':H(end_hours),
                   'issue_resolution_date_utc':H(resolution) if resolution is not None else pd.NaT,
                   'issue_status':final,'issue_type':'Ticket','issue_priority':'Medium','issue_proj':'abcdefg'})
    events=[{'id':i+1,'value':status,'event_time_utc':H(t)} for i,(t,status) in enumerate(changes)]
    return one_ticket(row,events,wf_bad=stage)[0]
class MeasurementTests(unittest.TestCase):
    def test_B_resolved_counts_until_closed(self):
        x=ticket([(2,'resolved'),(7,'closed')],end_hours=7)
        self.assertEqual(x['B_observed_counted_hours'],7)
        self.assertEqual(x['A_observed_counted_hours'],2)
    def test_waiting_pause(self):
        x=ticket([(2,'waiting'),(60,'resolved'),(80,'closed')],end_hours=80)
        self.assertEqual(x['B_observed_counted_hours'],22)
        self.assertEqual(x['B_confirmed_class'],'closed_without_breach')
    def test_pending_pause_provisional(self):
        x=ticket([(2,'pending_customer_approval'),(60,'in_progress'),(70,'closed')],end_hours=70)
        self.assertEqual(x['B_observed_counted_hours'],12)
    def test_exact_threshold_is_not_breach(self):
        self.assertEqual(ticket([(72,'closed')],end_hours=72)['B_confirmed_class'],'closed_without_breach')
        self.assertEqual(ticket([(73,'closed')],end_hours=73)['B_confirmed_class'],'confirmed_breached')
    def test_reopen_resumes_cumulative(self):
        x=ticket([(40,'closed'),(60,'reopened'),(100,'closed')],end_hours=100)
        self.assertEqual(x['B_observed_counted_hours'],80)
        self.assertEqual(x['B_confirmed_class'],'confirmed_breached')
    def test_closed_interval_not_counted(self):
        x=ticket([(1,'closed'),(1000,'closed')],end_hours=1000)
        self.assertEqual(x['B_observed_counted_hours'],1)
        self.assertEqual(x['B_confirmed_class'],'closed_without_breach')
    def test_events_after_ended_included(self):
        x=ticket([(80,'closed')],end_hours=5)
        self.assertEqual(x['B_observed_counted_hours'],80)
        self.assertTrue(x['has_valid_events_after_ended'])
    def test_censored_not_automatically_compliant(self):
        x=ticket([(2,'in_progress')],final='in_progress',end_hours=200)
        self.assertEqual(x['B_observed_counted_hours'],2)
        self.assertEqual(x['B_confirmed_class'],'censored_no_proven_breach')
        self.assertTrue(x['hypothetical_B_threshold_exceeded'])
    def test_open_confirmed_breach(self):
        x=ticket([(80,'waiting')],final='waiting',end_hours=100)
        self.assertEqual(x['B_confirmed_class'],'confirmed_breached')
    def test_special_state_indeterminate_not_closed(self):
        x=ticket([(2,'done'),(80,'closed')],end_hours=80)
        self.assertEqual(x['B_confirmed_class'],'indeterminate_semantic')
    def test_prior_breach_survives_special_state(self):
        x=ticket([(80,'done'),(90,'closed')],end_hours=90)
        self.assertEqual(x['B_confirmed_class'],'confirmed_breached')
    def test_implicit_reopen_reviewer_gate(self):
        x=ticket([(2,'closed'),(4,'in_progress'),(100,'closed')],end_hours=100)
        self.assertEqual(x['B_confirmed_class'],'indeterminate_semantic')
        self.assertTrue(x['has_abnormal_exit_from_closed'])
    def test_dq_mismatch_excluded(self):
        x=ticket([(80,'closed')],end_hours=80,stage=True)
        self.assertEqual(x['B_confirmed_class'],'indeterminate_data_quality')
    def test_source_status_mismatch_excluded(self):
        x=ticket([(2,'in_progress')],final='closed',end_hours=5)
        self.assertEqual(x['B_confirmed_class'],'indeterminate_data_quality')
if __name__=='__main__':unittest.main(verbosity=2)
