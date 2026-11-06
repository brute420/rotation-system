"""
KEBS JKIA Officer Rotation — CSP Logic (v2.1, corrected)

Constraints enforced per shed:
  C1: officer.skill == shed.skill_required
  C2: has_visited == False (pair not yet used in this cycle)
  C3: Supervisor role gets priority over regular Officer
  C4: Lowest workload_points first (fairness)
  C5: Officer must not be on approved leave during assignment window
  C6: officer.is_active == True
  C7: An officer is assigned to at most ONE shed per roster run   (added in v2.1)

Corrections in v2.1
  * The run status is returned as "run_status" so that it no longer overwrites
    the API-level "status": "success" field that the front end checks.
  * Constraint C7 added so that no officer appears twice in the same run.
"""
import json
from datetime import date, timedelta
from django.utils import timezone
from .models import Officer, Shed, RotationHistory, RotationRun, LeaveRequest


def _on_leave(officer, start, end):
    if not start or not end:
        return False
    return LeaveRequest.objects.filter(
        officer=officer,
        status='approved',
        start_date__lte=end,
        end_date__gte=start,
    ).exists()


def run_rotation(week_start=None):
    if week_start is None:
        week_start = date.today()
    week_end = week_start + timedelta(weeks=2)

    sheds = Shed.objects.all().order_by('-priority', 'name')
    assignments, unassigned = [], []
    assigned_officer_ids = set()          # C7: one shed per officer per run

    for shed in sheds:
        pending = (
            RotationHistory.objects
            .filter(shed=shed, has_visited=False, officer__is_active=True)
            .select_related('officer')
            .order_by('officer__workload_points')
        )

        supervisors, regulars = [], []
        blocked_by_c7 = 0
        for h in pending:
            if h.officer.skill != shed.skill_required:
                continue
            if _on_leave(h.officer, week_start, week_end):
                continue
            if h.officer_id in assigned_officer_ids:
                blocked_by_c7 += 1
                continue
            if h.officer.role == 'Supervisor':
                supervisors.append(h)
            else:
                regulars.append(h)

        supervisors.sort(key=lambda h: h.officer.workload_points)
        regulars.sort(key=lambda h: h.officer.workload_points)
        candidates = supervisors + regulars
        matched = candidates[0] if candidates else None

        if matched:
            matched.has_visited = True
            matched.start_date  = week_start
            matched.end_date    = week_end
            matched.save()

            officer = matched.officer
            officer.workload_points += 1.0
            officer.save()
            assigned_officer_ids.add(officer.id)

            assignments.append({
                'officer':    officer.name,
                'badge':      officer.badge_number,
                'role':       officer.role,
                'shed':       shed.name,
                'skill':      shed.skill_required,
                'workload':   officer.workload_points,
                'start_date': week_start.strftime('%Y-%m-%d'),
                'end_date':   week_end.strftime('%Y-%m-%d'),
                'priority':   shed.priority,
            })
        else:
            all_h = RotationHistory.objects.filter(
                shed=shed, officer__skill=shed.skill_required)
            on_leave_count = sum(
                1 for h in all_h if _on_leave(h.officer, week_start, week_end))

            if all_h.exists() and not all_h.filter(has_visited=False).exists():
                reason = 'All eligible officers completed this shed — reset cycle'
            elif blocked_by_c7:
                reason = 'Remaining eligible officers are already assigned to another shed in this run'
            elif on_leave_count:
                reason = f'{on_leave_count} officer(s) on leave, no substitute available'
            elif not all_h.exists():
                reason = 'No rotation history — run seed.py first'
            else:
                reason = 'No active officer with matching skill available'

            unassigned.append({
                'shed': shed.name,
                'required_skill': shed.skill_required,
                'priority': shed.priority,
                'reason': reason,
            })

    run = RotationRun.objects.create(
        assignments_json=json.dumps(assignments),
        total_assigned=len(assignments),
        total_unassigned=len(unassigned),
        status='pending',
        week_start=week_start,
    )

    return {
        'assignments':      assignments,
        'unassigned':       unassigned,
        'total_assigned':   len(assignments),
        'total_unassigned': len(unassigned),
        'run_id':           run.id,
        'run_at':           run.run_at.strftime('%Y-%m-%d %H:%M:%S'),
        'run_status':       run.status,          # was "status" (collided with API status)
        'week_start':       week_start.strftime('%Y-%m-%d'),
        'week_end':         week_end.strftime('%Y-%m-%d'),
    }


def approve_rotation(run_id, approved_by):
    try:
        run = RotationRun.objects.get(id=run_id)
        run.status = 'approved'
        run.approved_by = approved_by
        run.approved_at = timezone.now()
        run.save()
        return {'success': True, 'message': f'Run #{run_id} approved by {approved_by}'}
    except RotationRun.DoesNotExist:
        return {'success': False, 'message': f'Run #{run_id} not found'}


def reject_rotation(run_id, reason, rejected_by):
    try:
        run = RotationRun.objects.get(id=run_id)
        run.status = 'rejected'
        run.rejection_reason = reason
        run.approved_by = rejected_by
        run.save()
        return {'success': True, 'message': f'Run #{run_id} rejected'}
    except RotationRun.DoesNotExist:
        return {'success': False, 'message': f'Run #{run_id} not found'}


def reset_all_rotations():
    RotationHistory.objects.all().update(
        has_visited=False, start_date=None, end_date=None)
    Officer.objects.all().update(workload_points=0.0)
    return {'message': 'All rotation history reset. Ready for new cycle.'}


def process_swap(swap_id, action, approved_by):
    from .models import SwapRequest
    try:
        swap = SwapRequest.objects.get(id=swap_id)
    except SwapRequest.DoesNotExist:
        return {'success': False, 'message': 'Swap request not found'}

    if action == 'approve':
        try:
            h1 = RotationHistory.objects.get(officer=swap.requester, shed=swap.requester_shed)
            h2 = RotationHistory.objects.get(officer=swap.target_officer, shed=swap.target_shed)
            h1.shed = swap.target_shed
            h2.shed = swap.requester_shed
            h1.save()
            h2.save()
            swap.status = 'approved'
            swap.approved_by = approved_by
            swap.resolved_at = timezone.now()
            swap.save()
            return {'success': True, 'message': 'Swap approved and executed'}
        except RotationHistory.DoesNotExist:
            return {'success': False, 'message': 'Could not find assignment records to swap'}
    else:
        swap.status = 'rejected'
        swap.approved_by = approved_by
        swap.resolved_at = timezone.now()
        swap.save()
        return {'success': True, 'message': 'Swap rejected'}


def get_stats():
    total_officers = Officer.objects.filter(is_active=True).count()
    total_sheds    = Shed.objects.count()
    completed      = RotationHistory.objects.filter(has_visited=True).count()
    pending_assign = RotationHistory.objects.filter(has_visited=False).count()
    pending_runs   = RotationRun.objects.filter(status='pending').count()
    on_leave_now   = LeaveRequest.objects.filter(
        status='approved',
        start_date__lte=date.today(),
        end_date__gte=date.today(),
    ).count()

    workload_data = list(
        Officer.objects.filter(is_active=True)
        .values('name', 'skill', 'role', 'workload_points', 'badge_number')
        .order_by('-workload_points')
    )

    recent_runs = RotationRun.objects.all()[:5]
    history = [{
        'run_id':           r.id,
        'run_at':           r.run_at.strftime('%Y-%m-%d %H:%M'),
        'total_assigned':   r.total_assigned,
        'total_unassigned': r.total_unassigned,
        'status':           r.status,
        'week_start':       r.week_start.strftime('%Y-%m-%d') if r.week_start else '',
    } for r in recent_runs]

    return {
        'total_officers':        total_officers,
        'total_sheds':           total_sheds,
        'completed_assignments': completed,
        'pending_assignments':   pending_assign,
        'pending_approvals':     pending_runs,
        'officers_on_leave':     on_leave_now,
        'workload_distribution': workload_data,
        'recent_runs':           history,
    }
