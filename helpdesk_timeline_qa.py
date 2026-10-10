"""Domain III: Reproducible, read-only ticket status-timeline & data-quality audit.

Does NOT calculate or certify an SLA/72h baseline. The original ZIP is untouched.
Usage: python helpdesk_timeline_qa.py [path/to/Help Desk Tickets.zip] [output_dir]
Requires: pandas. Output: aggregate JSON, targeted QA tickets CSV, sample status intervals CSV.
"""
from pathlib import Path
import io
import json
import sys
import zipfile
import pandas as pd

ARCHIVE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('/mnt/data/Help Desk Tickets.zip')
DEST = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('/mnt/data/helpdesk_domain3_qa')
PREFIX = 'Help Desk Tickets/'

def parse_timestamp(s):
    return pd.to_datetime(s, errors='coerce', format='mixed', utc=True)

def csv_in_zip(z, name):
    return pd.read_csv(io.BytesIO(z.read(PREFIX + name)),low_memory=False)

def build_intervals(issues, history):
    """Intervals [at, next_at), initial status 'open', changes ordered by time then event ID."""
    ids = set(issues.id)
    st = history.loc[history.issueid.isin(ids) & history.field.eq('status'), ['id','issueid','created','value']].copy()
    st['at'] = parse_timestamp(st.created)
    st = st.rename(columns={'issueid':'ticket_id', 'value':'status', 'id':'event_id'})
    st = st.merge(issues[['id','created_at','ended_at']].rename(columns={'id':'ticket_id'}), on='ticket_id', validate='many_to_one')
    bad_time = st['at'].isna() | st['at'].lt(st.created_at)
    later_than_ended = st['at'].gt(st.ended_at)
    usable = st.loc[~bad_time & ~later_than_ended, ['ticket_id','at','status','event_id']].copy()
    usable['kind'] = 1
    start = pd.DataFrame({'ticket_id':issues.id, 'at':issues.created_at,'status':'open','kind':0,'event_id':0})
    stop = pd.DataFrame({'ticket_id':issues.id, 'at':issues.ended_at,'status':'<END>','kind':2,'event_id':0})
    segments = pd.concat([start,usable,stop],ignore_index=True)
    segments.sort_values(['ticket_id','at','kind','event_id'],inplace=True,kind='mergesort')
    segments['next_at'] = segments.groupby('ticket_id')['at'].shift(-1)
    segments['duration_s'] = (segments.next_at-segments['at']).dt.total_seconds().fillna(0)
    assert not segments.duration_s.lt(-1e-6).any(), 'Negative segments'
    segments['is_closed'] = segments.status.eq('closed')
    segments['is_waiting'] = segments.status.eq('waiting')
    segments['is_provisionally_paused'] = segments.status.eq('pending_customer_approval')
    segments['is_active_counting_candidate'] = (~segments.status.isin(['<END>','closed','waiting','pending_customer_approval']))
    return segments, st, bad_time, later_than_ended, usable

def audit():
    with zipfile.ZipFile(ARCHIVE) as z:
        issues = csv_in_zip(z, 'issues.csv')
        history = csv_in_zip(z, 'issues_change_history.csv')
    issues['created_at'] = parse_timestamp(issues.issue_created)
    issues['ended_at'] = parse_timestamp(issues.ended)
    issues['last_change_at'] = parse_timestamp(issues.last_change_date)
    issues['resolved_at'] = parse_timestamp(issues.issue_resolution_date)
    scope = issues.loc[issues.issue_proj.astype('string').str.len().gt(6).fillna(False)
                       & issues.issue_type.isin(['Ticket','Service','HD Service'])
                       & issues.created_at.dt.year.between(2019,2022)].copy()
    assert len(scope)==19714 and scope.id.is_unique
    assert scope.created_at.notna().all() and scope.ended_at.notna().all()
    seg,st,bad_time,after_ended,events = build_intervals(scope,history)
    wf_cols=[x for x in scope.columns if x.startswith('wf_') and x != 'wf_total_time']
    provided=scope.set_index('id')[wf_cols].fillna(0)
    acc=seg.loc[seg.kind.ne(2)].groupby(['ticket_id','status']).duration_s.sum().unstack(fill_value=0).reindex(provided.index, fill_value=0)
    stage_diffs=pd.DataFrame({c:(acc.get(c[3:],pd.Series(0.0,index=provided.index))-provided[c]).abs() for c in wf_cols})
    max_err=stage_diffs.max(axis=1)
    bad_ids=list(max_err.index[max_err.gt(60)])
    assert len(bad_ids)==7, f'Unexpected # stage discrepancies: {len(bad_ids)}'
    reconstructed_total=seg.groupby('ticket_id').duration_s.sum().reindex(provided.index,fill_value=0)
    wall_s=(scope.ended_at-scope.created_at).dt.total_seconds().set_axis(scope.id)
    assert (reconstructed_total-wall_s).abs().lt(1e-5).all(), 'Timeline not complete'
    raw_total=(reconstructed_total-scope.set_index('id').wf_total_time).abs()
    # State transitions across all valid events including those past per-ticket ended
    st_all=st.loc[~bad_time].sort_values(['ticket_id','at','event_id']).copy()
    st_all['previous_status']=st_all.groupby('ticket_id').status.shift().fillna('open')
    departures=st_all[st_all.previous_status.eq('closed') & ~st_all.status.eq('closed')]
    direct_out=departures.loc[~departures.status.eq('reopened')]
    reopen=st_all.loc[st_all.status.eq('reopened')]
    # Working option B: only 'closed' stops the clock; 'resolved' periods COUNT.
    # Option A stops on 'resolved' for comparison only (see domain3_timeline_v2).
    # Strict closure rule: only 'closed' removes ticket from active-clock category.
    # 'done'/'cancelled' receive explicit uncertainty flag when final and no later closure.
    last_observed=events.sort_values(['ticket_id','at','event_id']).groupby('ticket_id').tail(1)[['ticket_id','status','at']]
    last_observed=last_observed.set_index('ticket_id').rename(columns={'status':'last_event_state','at':'last_status_event_at'})
    qa=scope[['id','issue_status','created_at','ended_at','last_change_at','resolved_at']].copy().set_index('id')
    qa['last_reconstructed_state_at_ended']=(events.sort_values(['ticket_id','at','event_id']).groupby('ticket_id').status.last().reindex(qa.index).fillna('open'))
    qa['status_mismatch_at_ended']=qa.issue_status.ne(qa.last_reconstructed_state_at_ended)
    qa['last_status_event_after_ended']=qa.index.isin(st.loc[after_ended, 'ticket_id'])
    qa['has_reopened_state']=qa.index.isin(reopen.ticket_id)
    qa['has_nonstandard_departure_from_closed']=qa.index.isin(direct_out.ticket_id)
    qa['final_done_or_cancelled']=qa.issue_status.isin(['done','cancelled'])
    qa['closed_missing_resolution_date']=qa.issue_status.eq('closed') & qa.resolved_at.isna()
    qa['workflow_stage_error_gt60s']=qa.index.isin(bad_ids)
    qa['stage_max_diff_s']=max_err
    qa['timeline_vs_total_abs_diff_s']=raw_total
    qa['last_change_after_ended']=qa.last_change_at.gt(qa.ended_at)
    qa['has_events_after_ended']=qa.index.isin(st.loc[after_ended,'ticket_id'])
    qa['reasons']=qa[['status_mismatch_at_ended','has_events_after_ended','has_nonstandard_departure_from_closed','final_done_or_cancelled','closed_missing_resolution_date','workflow_stage_error_gt60s']].apply(lambda r:';'.join(r.index[r.values]),axis=1)
    flagged=qa[qa.reasons.ne('')].copy()
    flagged.index.name='ticket_id'
    DEST.mkdir(parents=True,exist_ok=True)
    flagged.reset_index().to_csv(DEST/'timeline_qa_flags.csv',index=False)
    # Candidate stage: no per-ticket SLA result; never silently extend beyond ended_at.
    candidate=seg.loc[seg.kind.ne(2)&seg.duration_s.gt(0), ['ticket_id','status','at','next_at','duration_s','is_closed','is_waiting','is_provisionally_paused','is_active_counting_candidate']].copy()
    candidate=candidate.rename(columns={'at':'interval_start_utc','next_at':'interval_end_utc'})
    candidate['ticket_has_qa_flag']=candidate.ticket_id.isin(flagged.index)
    candidate.to_csv(DEST/'ticket_status_intervals_candidate.csv',index=False)
    sample_ids=sorted(set(bad_ids) | set(qa.index[qa.final_done_or_cancelled]) | set(qa.index[qa.status_mismatch_at_ended]))
    samples=seg.loc[seg.ticket_id.isin(sample_ids),['ticket_id','at','next_at','status','duration_s','is_active_counting_candidate']]
    samples.to_csv(DEST/'timeline_exception_intervals.csv',index=False)
    result={
      'scope_tickets':len(scope),
      'final_status_counts':{str(k):int(v) for k,v in scope.issue_status.value_counts().items()},
      'status_event_rows_inside_ended':len(events),
      'status_event_rows_after_ended':int(after_ended.sum()),
      'status_event_tickets_after_ended':int(st.loc[after_ended,'ticket_id'].nunique()),
      'status_events_before_created_or_invalid_timestamp':int(bad_time.sum()),
      'tickets_final_status_not_equal_asof_ended':int(qa.status_mismatch_at_ended.sum()),
      'final_status_mismatch_ids':[int(x) for x in qa.index[qa.status_mismatch_at_ended]],
      'final_done_or_cancelled_tickets':int(qa.final_done_or_cancelled.sum()),
      'unique_tickets_with_reopened_status':int(reopen.ticket_id.nunique()),
      'departures_from_closed_to_reopened_events':int(departures.status.eq('reopened').sum()),
      'departures_from_closed_other_than_reopened_events':len(direct_out),
      'unique_tickets_with_nonstandard_departure_from_closed':int(direct_out.ticket_id.nunique()),
      'closed_tickets_missing_resolution_date':int(qa.closed_missing_resolution_date.sum()),
      'workflow_stage_mismatch_over_60s':int(qa.workflow_stage_error_gt60s.sum()),
      'workflow_stage_mismatch_ids':[int(x) for x in bad_ids],
      'maximum_total_timeline_vs_wf_total_discrepancy_s':float(raw_total.max()),
      'last_change_date_later_than_ended_tickets':int(qa.last_change_after_ended.sum()),
      'candidate_interval_rows':len(candidate),
      'qa_flagged_unique_tickets':len(flagged),
      'unique_sample_tickets_exported':len(sample_ids),
      'checked_threshold_baseline':False,
      'notes':[
       'No ticket KPI outcomes or 72h baseline computed.',
       'An ended field is not by itself a proven observation cutoff for an unresolved ticket.',
       'Counting clock pauses in waiting; pending_customer_approval is provisional and unconfirmed.',
       'Last-change timestamps can be later than ended without a status transition; treat time fields separately.',
       'Multiple episodes: any exit from closed back to a non-closed state resumes the proposed counted clock; reset vs cumulative remains a policy choice unless validated.'
      ]
    }
    (DEST/'timeline_qa_summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':
    audit()
