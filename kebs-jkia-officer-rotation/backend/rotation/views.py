import json
from datetime import date
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .logic import (
    run_rotation, approve_rotation, reject_rotation,
    reset_all_rotations, process_swap, get_stats
)
from .models import Officer, Shed, LeaveRequest, SwapRequest, RotationRun


# ── Rotation ──────────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['POST'])
def trigger_rotation(request):
    try:
        body = json.loads(request.body or '{}')
        week_start_str = body.get('week_start')
        week_start = date.fromisoformat(week_start_str) if week_start_str else None
        return JsonResponse({'status': 'success', **run_rotation(week_start)})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_http_methods(['POST'])
def approve_run(request, run_id):
    try:
        body = json.loads(request.body or '{}')
        approved_by = body.get('approved_by', 'Officer in Charge')
        result = approve_rotation(run_id, approved_by)
        status = 'success' if result['success'] else 'error'
        return JsonResponse({'status': status, **result})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_http_methods(['POST'])
def reject_run(request, run_id):
    try:
        body = json.loads(request.body or '{}')
        reason      = body.get('reason', '')
        rejected_by = body.get('rejected_by', 'Officer in Charge')
        result = reject_rotation(run_id, reason, rejected_by)
        status = 'success' if result['success'] else 'error'
        return JsonResponse({'status': status, **result})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_http_methods(['POST'])
def reset_rotation(request):
    try:
        return JsonResponse({'status': 'success', **reset_all_rotations()})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# ── Stats & Lists ─────────────────────────────────────────────────────────────

@require_http_methods(['GET'])
def get_dashboard_stats(request):
    try:
        return JsonResponse({'status': 'success', **get_stats()})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@require_http_methods(['GET'])
def get_officers(request):
    try:
        data = list(Officer.objects.filter(is_active=True).values(
            'id', 'name', 'badge_number', 'skill', 'role', 'workload_points', 'email'
        ))
        return JsonResponse({'status': 'success', 'officers': data})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@require_http_methods(['GET'])
def get_sheds(request):
    try:
        data = list(Shed.objects.values(
            'id', 'name', 'skill_required', 'location', 'priority', 'min_officers', 'max_officers'
        ))
        return JsonResponse({'status': 'success', 'sheds': data})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@require_http_methods(['GET'])
def get_runs(request):
    """List all rotation runs with their approval status."""
    try:
        runs = RotationRun.objects.all()[:20]
        data = [
            {
                'id':               r.id,
                'run_at':           r.run_at.strftime('%Y-%m-%d %H:%M'),
                'status':           r.status,
                'total_assigned':   r.total_assigned,
                'total_unassigned': r.total_unassigned,
                'approved_by':      r.approved_by,
                'week_start':       r.week_start.strftime('%Y-%m-%d') if r.week_start else '',
                'assignments':      json.loads(r.assignments_json),
            }
            for r in runs
        ]
        return JsonResponse({'status': 'success', 'runs': data})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# ── Leave Management ──────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['POST'])
def create_leave(request):
    try:
        body = json.loads(request.body)
        officer    = Officer.objects.get(id=body['officer_id'])
        start_date = date.fromisoformat(body['start_date'])
        end_date   = date.fromisoformat(body['end_date'])
        leave = LeaveRequest.objects.create(
            officer=officer,
            start_date=start_date,
            end_date=end_date,
            reason=body.get('reason', ''),
            status='pending',
        )
        return JsonResponse({'status': 'success', 'leave_id': leave.id,
                             'message': 'Leave request submitted for approval'})
    except Officer.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Officer not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@require_http_methods(['GET'])
def get_leaves(request):
    try:
        leaves = LeaveRequest.objects.select_related('officer').all()
        data = [
            {
                'id':           l.id,
                'officer':      l.officer.name,
                'officer_id':   l.officer.id,
                'start_date':   l.start_date.strftime('%Y-%m-%d'),
                'end_date':     l.end_date.strftime('%Y-%m-%d'),
                'reason':       l.reason,
                'status':       l.status,
                'approved_by':  l.approved_by,
            }
            for l in leaves
        ]
        return JsonResponse({'status': 'success', 'leaves': data})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_http_methods(['POST'])
def action_leave(request, leave_id):
    """Approve or reject a leave request."""
    try:
        body        = json.loads(request.body)
        action      = body.get('action')        # 'approve' or 'reject'
        approved_by = body.get('approved_by', 'Officer in Charge')
        leave = LeaveRequest.objects.get(id=leave_id)
        leave.status      = 'approved' if action == 'approve' else 'rejected'
        leave.approved_by = approved_by
        leave.save()
        return JsonResponse({'status': 'success',
                             'message': f'Leave {leave.status} for {leave.officer.name}'})
    except LeaveRequest.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Leave not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# ── Swap Requests ─────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(['POST'])
def create_swap(request):
    try:
        body           = json.loads(request.body)
        requester      = Officer.objects.get(id=body['requester_id'])
        target_officer = Officer.objects.get(id=body['target_officer_id'])
        requester_shed = Shed.objects.get(id=body['requester_shed_id'])
        target_shed    = Shed.objects.get(id=body['target_shed_id'])
        swap = SwapRequest.objects.create(
            requester=requester,
            target_officer=target_officer,
            requester_shed=requester_shed,
            target_shed=target_shed,
            reason=body.get('reason', ''),
        )
        return JsonResponse({'status': 'success', 'swap_id': swap.id,
                             'message': 'Swap request submitted'})
    except (Officer.DoesNotExist, Shed.DoesNotExist) as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@require_http_methods(['GET'])
def get_swaps(request):
    try:
        swaps = SwapRequest.objects.select_related(
            'requester', 'target_officer', 'requester_shed', 'target_shed'
        ).all()
        data = [
            {
                'id':              s.id,
                'requester':       s.requester.name,
                'target_officer':  s.target_officer.name,
                'requester_shed':  s.requester_shed.name,
                'target_shed':     s.target_shed.name,
                'reason':          s.reason,
                'status':          s.status,
                'created_at':      s.created_at.strftime('%Y-%m-%d %H:%M'),
            }
            for s in swaps
        ]
        return JsonResponse({'status': 'success', 'swaps': data})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_http_methods(['POST'])
def action_swap(request, swap_id):
    """Approve or reject a swap request."""
    try:
        body        = json.loads(request.body)
        action      = body.get('action')       # 'approve' or 'reject'
        approved_by = body.get('approved_by', 'Officer in Charge')
        result = process_swap(swap_id, action, approved_by)
        status = 'success' if result['success'] else 'error'
        return JsonResponse({'status': status, **result})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
