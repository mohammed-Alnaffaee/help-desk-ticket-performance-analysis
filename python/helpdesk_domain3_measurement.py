#!/usr/bin/env python3
"""Conservative event-observed ticket-clock measurement for the Help Desk portfolio.
Does not update source CSV/ZIP. Re-run: python helpdesk_domain3_measurement.py [source_zip] [output_directory]
B counts 'resolved' until entering 'closed', excludes 'closed' and 'waiting', and
provisionally excludes 'pending_customer_approval'. A is comparison only.
Never stretches a nonclosed last-state to ended for primary estimates.
14 Mar 2023 23:59:59 UTC is an UNVERIFIED hypothetical censoring sensitivity only.
The 'ever breached' label remains durable after later closure; clock accumulated
across reopens (working convention). For ambiguous states / mismatches, a
conservative review disposition avoids claiming definite compliance.
"""
from pathlib import Path
import sys,zipfile,io,json,collections
import pandas as pd
import time
import numpy as np

SRC=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/mnt/data/Help Desk Tickets.zip')
OUT=Path(sys.argv[2]) if len(sys.argv)>2 else Path('/mnt/data/helpdesk_domain3_final')
OUT.mkdir(parents=True,exist_ok=True)
PAUSE={'waiting','pending_customer_approval'}
UNCERTAIN={'done','cancelled'}
THRESHOLD=72*3600
HYPOTHETICAL_CUTOFF=pd.Timestamp('2023-03-14T23:59:59Z')

def times(s): return pd.to_datetime(s,format='mixed',utc=True,errors='coerce')

def load():
    with zipfile.ZipFile(SRC) as z:
        a=pd.read_csv(io.BytesIO(z.read('Help Desk Tickets/issues.csv')),low_memory=False)
        h=pd.read_csv(io.BytesIO(z.read('Help Desk Tickets/issues_change_history.csv')),low_memory=False)
    for col in ['issue_created','ended','issue_resolution_date','last_change_date']:
        a[col+'_utc']=times(a[col])
    a=a.loc[a.issue_proj.astype('string').str.len().gt(6).fillna(False) &
            a.issue_type.isin(['Ticket','Service','HD Service']) &
            a.issue_created_utc.dt.year.between(2019,2022)].copy()
    a['id']=a.id.astype('int64'); assert len(a)==19714 and a.id.is_unique
    h=h.loc[h.issueid.isin(a.id) & h.field.eq('status')].copy()
    h['event_time_utc']=times(h.created)
    h['issueid']=h.issueid.astype('int64')
    h=h.sort_values(['issueid','event_time_utc','id'],kind='mergesort')
    return a,h

def one_ticket(row, events, wf_bad=False, export_intervals=True):
    tid=int(row['id']); start=row['issue_created_utc']; source_final=str(row['issue_status'])
    assert pd.notna(start)
    state='open'; at=start; clock_b=0.;clock_a=0.; a_live=True; cross_b=None;cross_a=None
    first_uncertain=None; prior='open'; n_close=0; n_reopen=0; abnormal_exit=False
    got_after_ended=False; interval_rows=[]; validity_error=False; prev_event=None; visited_special=False
    last_observed=start; n_events=0; segments_n=0; resolved_to_closed_seconds=0.
    initial_source_ended=row['ended_utc']
    for ev in events:
        to_state=str(ev['value']); t=ev['event_time_utc']; eid=int(ev['id'])
        if pd.isna(t) or t<start or (prev_event is not None and t<prev_event):
            validity_error=True;continue
        if pd.notna(initial_source_ended) and t>initial_source_ended: got_after_ended=True
        if t<at: validity_error=True;continue
        dur=(t-at).total_seconds(); assert dur>=0
        b_count=dur if state!='closed' and state not in PAUSE else 0.
        a_count=b_count if a_live else 0.
        if b_count>0 and cross_b is None and clock_b+b_count>THRESHOLD:
            cross_b=at+pd.to_timedelta(max(0.,THRESHOLD-clock_b),unit='s')
        if a_count>0 and cross_a is None and clock_a+a_count>THRESHOLD:
            cross_a=at+pd.to_timedelta(max(0.,THRESHOLD-clock_a),unit='s')
        if state=='resolved': resolved_to_closed_seconds+=dur
        if dur>0 and export_intervals:
            interval_rows.append({'ticket_id':tid,'start_utc':at,'end_utc':t,'status':state,'duration_seconds':dur,
                'B_counted_seconds':b_count,'A_counted_seconds':a_count,'is_after_source_ended': bool(pd.notna(initial_source_ended) and at>=initial_source_ended),
                'is_pause':state in PAUSE,'is_closed_excluded':state=='closed'})
        clock_b+=b_count;clock_a+=a_count
        if state=='closed' and to_state not in ('closed','reopened'):
            abnormal_exit=True
            if first_uncertain is None: first_uncertain=t
        if to_state in UNCERTAIN:
            visited_special=True
            if first_uncertain is None:first_uncertain=t
        if to_state=='closed': n_close+=1
        if to_state=='reopened':n_reopen+=1
        # Comparison A stops from resolved, until reopened or a departure from closed.
        if to_state in ('resolved','closed'):a_live=False
        elif to_state=='reopened' or (state=='closed' and to_state!='closed'): a_live=True
        state=to_state; at=t; last_observed=t;prev_event=t;n_events+=1; segments_n+=(dur>0)
    last_state=state
    mismatch=last_state!=source_final
    # Nothing is inferred about time AFTER last observed event for base measurements.
    has_closed_evidence=(state=='closed' and n_close>0)
    # If an uncertainty occurs AFTER threshold crossing, the historic breach is still provable.
    proven_before_uncertainty=(cross_b is not None and (first_uncertain is None or cross_b<first_uncertain))
    flags=[]
    if wf_bad:flags.append('workflow_aggregate_reconciliation_gt60s')
    if validity_error:flags.append('invalid_or_reversed_status_event')
    if mismatch:flags.append('source_final_status_mismatch')
    if abnormal_exit:flags.append('closed_departure_without_reopened')
    if first_uncertain is not None:flags.append('semantic_uncertainty_done_cancelled_or_implicit_reopen')
    if got_after_ended:flags.append('valid_status_event_after_ended_included')
    if source_final in UNCERTAIN:flags.append('terminal_done_cancelled_not_equivalent_closed')
    if str(row['issue_resolution_date_utc'])=='NaT': flags.append('missing_resolution_date_not_auto_error')
    # Structural contradictory events are excluded even if tentative breach found.
    if wf_bad or validity_error or mismatch:
        label='indeterminate_data_quality'
    elif proven_before_uncertainty:
        label='confirmed_breached'
    elif first_uncertain is not None:
        label='indeterminate_semantic'
    elif cross_b is not None:
        label='confirmed_breached'
    elif has_closed_evidence:
        label='closed_without_breach'
    elif source_final=='closed':
        label='indeterminate_missing_observed_closure'
    else:
        label='censored_no_proven_breach'
    # Sensitivity assumes last observed state remains unchanged to a made-up date.
    ext=0.
    if (last_state!='closed' and last_state not in PAUSE and source_final!='closed' and
        HYPOTHETICAL_CUTOFF>=last_observed):
        ext=(HYPOTHETICAL_CUTOFF-last_observed).total_seconds()
    hyp_b=clock_b+ext
    hyp_cross=(cross_b is not None or hyp_b>THRESHOLD)
    result={
        'ticket_id':tid,'created_utc':start,'source_ended_utc':row['ended_utc'],
        'source_resolution_utc':row['issue_resolution_date_utc'],
        'source_final_status':source_final,'last_observed_status':last_state,
        'last_observed_status_time_utc':last_observed,'observed_status_events':n_events,
        'observed_closed_entries':n_close,'observed_reopen_entries':n_reopen,
        'B_observed_counted_hours':clock_b/3600.,'A_observed_counted_hours':clock_a/3600.,
        'B_minus_A_observed_hours':(clock_b-clock_a)/3600.,
        'B_first_72h_boundary_utc':cross_b,'A_first_72h_boundary_utc':cross_a,
        'B_observed_threshold_exceeded':cross_b is not None,
        'A_observed_threshold_exceeded':cross_a is not None,
        'B_confirmed_class':label,'has_observed_closure_for_last_episode':has_closed_evidence,
        'has_valid_events_after_ended':got_after_ended,'has_abnormal_exit_from_closed':abnormal_exit,
        'has_special_done_cancelled':visited_special,
        'has_semantic_uncertainty':first_uncertain is not None,
        'stage_reconciliation_error_gt60s':wf_bad,'source_final_disagrees_with_last_observed_status':mismatch,
        'resolution_date_missing':pd.isna(row['issue_resolution_date_utc']),
        'hypothetical_2023_03_14_235959_UTC_extra_hours':ext/3600.,
        'hypothetical_B_counted_hours':hyp_b/3600.,
        'hypothetical_B_threshold_exceeded':hyp_cross,
        'quality_disposition':'confirmed' if label in ('confirmed_breached','closed_without_breach') else 'censored_or_review',
        'qa_flags':';'.join(flags),
        'issue_type':row['issue_type'],'issue_priority':row['issue_priority'],'issue_proj':row['issue_proj'],
        'creation_year':start.year
    }
    return result,interval_rows

def stage_qa(scope,h):
    """Reconcile original wf_* with independently reconstructed intervals bounded at ended only for QA.
    Unlike measurement, do NOT make ended an end of observation for nonclosed tickets.
    """
    stage_cols=[x for x in scope.columns if x.startswith('wf_') and x!='wf_total_time']
    wanted=scope.set_index('id')[stage_cols].fillna(0.)
    from helpdesk_timeline_qa import build_intervals
    source=scope.rename(columns={'issue_created_utc':'created_at','ended_utc':'ended_at'})
    s,_,_,_,_=build_intervals(source,h)
    inc=s.loc[s.kind.ne(2)].groupby(['ticket_id','status']).duration_s.sum().unstack(fill_value=0)
    err=pd.concat([(inc.get(c[3:],pd.Series(0.,index=inc.index)).reindex(wanted.index,fill_value=0.)-wanted[c]).abs().rename(c) for c in stage_cols],axis=1)
    return err.max(axis=1)

def produce():
    print("PROGRESS load",flush=True);scope,h=load(); print("PROGRESS stage_qa",flush=True);stage_error=stage_qa(scope,h);print("PROGRESS stage done",flush=True)
    assert int(stage_error.gt(60).sum())==7
    evt=collections.defaultdict(list)
    for e in h.itertuples(index=False):
        evt[int(e.issueid)].append({'value':e.value,'event_time_utc':e.event_time_utc,'id':e.id})

    records=[]; intervals=[]
    for j,(_,row) in enumerate(scope.iterrows()):
        r,ins=one_ticket(row,evt.get(int(row['id']),[]),bool(stage_error.loc[int(row['id'])]>60))
        records.append(r);intervals.extend(ins)
    d=pd.DataFrame(records).sort_values('ticket_id');di=pd.DataFrame(intervals)
    assert len(d)==19714 and d.ticket_id.is_unique
    assert d.B_observed_counted_hours.ge(d.A_observed_counted_hours-1e-7).all()
    assert d.B_minus_A_observed_hours.ge(-1e-7).all()
    assert di.duration_seconds.ge(0).all()
    assert di.loc[di.status.eq('closed')|di.status.isin(PAUSE),'B_counted_seconds'].eq(0).all()
    assert np.isclose(di.B_counted_seconds.sum()/3600,d.B_observed_counted_hours.sum())
    assert (d.B_confirmed_class.eq('confirmed_breached') & ~d.B_observed_threshold_exceeded).sum()==0
    counts=d.B_confirmed_class.value_counts().to_dict()
    numerator=int(counts.get('confirmed_breached',0)); without=int(counts.get('closed_without_breach',0))
    known=numerator+without
    uncertain=len(d)-known
    sensitivity_extra=int((d.hypothetical_B_threshold_exceeded & ~d.B_observed_threshold_exceeded).sum())
    a_only=int(d.A_observed_threshold_exceeded.sum()); b_obs=int(d.B_observed_threshold_exceeded.sum())
    summary={
      'status':'CONDITIONAL analytical baseline, not validated company SLA; no formal extraction timestamp',
      'population':len(d),
      'observed_valid_status_events':len(h),
      'status_events_after_source_ended_included':int((h.merge(scope[['id','ended_utc']],left_on='issueid',right_on='id').event_time_utc>h.merge(scope[['id','ended_utc']],left_on='issueid',right_on='id').ended_utc).sum()),
      'source_ended_used_as_observation_cutoff':False,
      'rule_B':'Count nonpaused, nonclosed state time from creation through consecutive observed transitions; resolved counts; cumulative across reopening; strict >72h',
      'rule_A_comparator':'Stop after resolved through reopen or nonclosed exit from closed; not selected policy',
      'waiting_pause':'included as project working rule','pending_approval_pause':'provisional; zero positive scoped duration in prior audit',
      'candidate_outcome_class_counts':{str(k):int(v) for k,v in counts.items()},
      'documented_denominator':'confirmed_breached + observed_closure_without_breach, excluding censored/indeterminate',
      'confirmed_breached_numerator':numerator,'closed_without_breach':without,
      'evaluable_denominator':known,'censored_and_indeterminate':uncertain,
      'conditional_breach_rate_pct':round(100*numerator/known,4) if known else None,
      'whole_population_confirmed_breach_lower_bound_pct':round(100*numerator/len(d),4),
      'whole_population_logical_upper_bound_pct':round(100*(numerator+uncertain)/len(d),4),
      'B_observed_threshold_exceeded_before_semantic_DQ_exclusions':b_obs,
      'A_observed_threshold_exceeded_before_semantic_DQ_exclusions':a_only,
      'B_minus_A_observed_positive_tickets':int(d.B_minus_A_observed_hours.gt(1e-8).sum()),
      'B_minus_A_total_observed_hours':round(float(d.B_minus_A_observed_hours.sum()),2),
      'B_minus_A_top10_share_of_delta_pct':round(100*d.B_minus_A_observed_hours.nlargest(10).sum()/d.B_minus_A_observed_hours.sum(),2),
      'B_minus_A_observed_hours_median_affected':float(d.loc[d.B_minus_A_observed_hours.gt(1e-8),'B_minus_A_observed_hours'].median()),
      'hypothetical_cutoff':'2023-03-14T23:59:59Z (assumption only, not extract date)',
      'hypothetical_additional_threshold_flags_among_not_observed_breached':sensitivity_extra,
      'hypothetical_total_B_threshold_flags_unadjusted_for_QA':int(d.hypothetical_B_threshold_exceeded.sum()),
      'additional_hypothetical_flags_by_original_label':{str(k):int(v) for k,v in d.loc[d.hypothetical_B_threshold_exceeded & ~d.B_observed_threshold_exceeded,'B_confirmed_class'].value_counts().items()},
      'seven_reconciliation_mismatches':int(d.stage_reconciliation_error_gt60s.sum()),
      'source_final_status_mismatches':int(d.source_final_disagrees_with_last_observed_status.sum()),
      'after_ended_tickets':int(d.has_valid_events_after_ended.sum()),
      'nonstandard_closed_departure_tickets':int(d.has_abnormal_exit_from_closed.sum()),
      'source_resolution_date_missing':int(d.resolution_date_missing.sum()),
      'samples_not_generalizable':'Reporter utterances not used to infer service quality or satisfaction.',
    }
    d.to_csv(OUT/'ticket_outcomes_conditional.csv',index=False)
    di.to_csv(OUT/'observed_status_intervals.csv',index=False)
    d.nlargest(30,'B_minus_A_observed_hours')[['ticket_id','created_utc','source_final_status','last_observed_status','B_observed_counted_hours','A_observed_counted_hours','B_minus_A_observed_hours','qa_flags']].to_csv(OUT/'top30_AB_outliers.csv',index=False)
    d.loc[~d.B_confirmed_class.isin(['confirmed_breached','closed_without_breach']) | d.qa_flags.ne('')].to_csv(OUT/'exceptions_and_censored.csv',index=False)
    # Segment comparison by year without implying present operations or casual attribution.
    groups=d.groupby('creation_year').agg(tickets=('ticket_id','size'),confirmed_breached=('B_confirmed_class',lambda v:int(v.eq('confirmed_breached').sum())),
        closed_without_breach=('B_confirmed_class',lambda v:int(v.eq('closed_without_breach').sum())),
        censored_or_review=('B_confirmed_class',lambda v:int((~v.isin(['confirmed_breached','closed_without_breach'])).sum())))
    groups['conditional_share_pct']=100*groups.confirmed_breached/(groups.confirmed_breached+groups.closed_without_breach)
    groups.to_csv(OUT/'conditional_annual_counts.csv')
    (OUT/'validation_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    return summary

if __name__=='__main__': produce()
