import os, sys, json, time, random, statistics as st
from datetime import date, timedelta
import django
sys.path.insert(0, '.')
os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
django.setup()

from django.test import Client
from rotation.models import (Officer, Shed, RotationHistory, RotationRun,
                             LeaveRequest, SwapRequest)
from rotation.logic import run_rotation, reset_all_rotations
import numpy as np
from scipy.optimize import linear_sum_assignment

SKILLS = ['Inspection', 'Fumigation', 'Sampling', 'Clearance', 'Verification']
SHEDS = [('Swissport Shed A', 'Inspection', 2), ('Swissport Shed B', 'Inspection', 2),
         ('Siginon Cold Storage', 'Fumigation', 3), ('Siginon Express', 'Fumigation', 3),
         ('KAHL Warehouse 1', 'Sampling', 2), ('KAHL Warehouse 2', 'Sampling', 2),
         ('KQ Cargo Gate', 'Clearance', 1), ('Express Freight Gate', 'Clearance', 1),
         ('Verification Bay Alpha', 'Verification', 2), ('Verification Bay Beta', 'Verification', 2)]
OFFICERS = [('Alice Mwangi', 'Inspection', 'Supervisor'), ('Brian Otieno', 'Inspection', 'Officer'),
            ('Carol Njeri', 'Inspection', 'Officer'), ('David Kamau', 'Fumigation', 'Supervisor'),
            ('Esther Wanjiku', 'Fumigation', 'Officer'), ('Francis Odhiambo', 'Fumigation', 'Officer'),
            ('Grace Akinyi', 'Sampling', 'Officer'), ('Henry Mutua', 'Sampling', 'Officer'),
            ('Irene Chebet', 'Clearance', 'Officer'), ('James Kariuki', 'Clearance', 'Officer'),
            ('Kevin Ndirangu', 'Verification', 'Officer'), ('Lucy Waithera', 'Verification', 'Officer')]


def wipe():
    SwapRequest.objects.all().delete(); LeaveRequest.objects.all().delete()
    RotationHistory.objects.all().delete(); RotationRun.objects.all().delete()
    Officer.objects.all().delete(); Shed.objects.all().delete()


def seed(mult=1):
    """Seed the KEBS data set; mult>1 scales officers and sheds for the scalability test."""
    wipe()
    sheds, officers = [], []
    n = 0
    for m in range(mult):
        for name, sk, pr in SHEDS:
            sheds.append(Shed(name=(name if mult==1 else f'{name} {m}'), skill_required=sk, location='JKIA', priority=pr))
    Shed.objects.bulk_create(sheds)
    for m in range(mult):
        for name, sk, role in OFFICERS:
            n += 1
            officers.append(Officer(name=(name if mult==1 else f'{name} {m}'), badge_number=f'K-{n:04d}', skill=sk, role=role,
                                    email=f'o{n}@kebs.go.ke'))
    Officer.objects.bulk_create(officers)
    sh = list(Shed.objects.all()); of = list(Officer.objects.all())
    RotationHistory.objects.bulk_create(
        [RotationHistory(officer=o, shed=s) for s in sh for o in of if o.skill == s.skill_required])
    return len(of), len(sh), RotationHistory.objects.count()


R = {}
c = Client(HTTP_HOST='localhost')
W0 = date(2026, 10, 23)

# --------------------------------------------------------------------- E1 functional tests
tests = []
def rec(i, name, ok, detail):
    tests.append({'id': i, 'test': name, 'passed': bool(ok), 'detail': detail})

seed()
d = c.get('/api/stats/').json()
rec('TC1', 'Open the dashboard (statistics endpoint)',
    d['status'] == 'success' and (d['total_officers'], d['total_sheds'], d['pending_assignments']) == (12, 10, 24),
    f"officers={d['total_officers']}, sheds={d['total_sheds']}, pending pairs={d['pending_assignments']}")

r = c.post('/api/rotate/', data=json.dumps({'week_start': '2026-10-23'}), content_type='application/json').json()
rec('TC2', 'Generate a roster (API contract and result)',
    r['status'] == 'success' and r['run_status'] == 'pending' and r['total_assigned'] == 10 and r['total_unassigned'] == 0,
    f"status={r['status']}, run_status={r['run_status']}, assigned={r['total_assigned']}, unassigned={r['total_unassigned']}")

s = c.get('/api/stats/').json(); runs = c.get('/api/runs/').json()
rec('TC3', 'Pending run is listed for approval',
    s['pending_approvals'] == 1 and runs['runs'][0]['status'] == 'pending',
    f"pending_approvals={s['pending_approvals']}, latest run status={runs['runs'][0]['status']}")

rec('TC6a', 'Every assignment matches officer competence to shed requirement',
    all(a['skill'] == Officer.objects.get(badge_number=a['badge']).skill for a in r['assignments']),
    'skill of every assigned officer equals skill required by the shed')

names = [a['officer'] for a in r['assignments']]
rec('TC11', 'No officer is assigned to two sheds in one run',
    len(names) == len(set(names)), f"{len(names)} assignments, {len(set(names))} distinct officers")

fum = [a for a in r['assignments'] if a['skill'] == 'Fumigation']
ins = [a for a in r['assignments'] if a['skill'] == 'Inspection']
rec('TC12', 'Supervisory officers receive priority when eligible and equal in workload',
    any(a['role'] == 'Supervisor' for a in fum) and any(a['role'] == 'Supervisor' for a in ins),
    'a supervisor was selected for one shed in each of the Fumigation and Inspection groups')

rid = r['run_id']
ap = c.post(f'/api/runs/{rid}/approve/', data=json.dumps({'approved_by': 'OIC'}), content_type='application/json').json()
rec('TC8', 'Approve a pending run', ap['status'] == 'success' and RotationRun.objects.get(id=rid).status == 'approved',
    f"run {rid} status={RotationRun.objects.get(id=rid).status}")

r2 = c.post('/api/rotate/', data=json.dumps({'week_start': '2026-11-06'}), content_type='application/json').json()
rj = c.post(f"/api/runs/{r2['run_id']}/reject/", data=json.dumps({'reason': 'test', 'rejected_by': 'OIC'}),
            content_type='application/json').json()
rec('TC13', 'Reject a pending run with a reason',
    rj['status'] == 'success' and RotationRun.objects.get(id=r2['run_id']).status == 'rejected',
    f"run {r2['run_id']} status={RotationRun.objects.get(id=r2['run_id']).status}")

# cycle exhaustion (TC5)
exhaust = None
for k in range(6):
    rr = c.post('/api/rotate/', data=json.dumps({'week_start': '2026-12-04'}), content_type='application/json').json()
    if rr['total_unassigned'] > 0:
        exhaust = rr; break
cyc_ok = exhaust is not None and exhaust['status'] == 'success' and any('reset cycle' in u['reason'] for u in exhaust['unassigned'])
rec('TC5', 'Generate repeatedly until pairs are used: clear cycle-complete reason returned',
    cyc_ok, f"after {k + 3} runs: status={exhaust['status']}, unassigned={exhaust['total_unassigned']}, "
            f"reason='{exhaust['unassigned'][0]['reason']}'" if exhaust else 'no exhaustion observed')

rs = c.post('/api/rotate/reset/', data='{}', content_type='application/json').json()
rec('TC4', 'Reset the cycle',
    rs['status'] == 'success' and RotationHistory.objects.filter(has_visited=True).count() == 0
    and Officer.objects.filter(workload_points__gt=0).count() == 0,
    f"visited pairs={RotationHistory.objects.filter(has_visited=True).count()}, officers with workload>0="
    f"{Officer.objects.filter(workload_points__gt=0).count()}")
r3 = c.post('/api/rotate/', data=json.dumps({'week_start': '2027-01-01'}), content_type='application/json').json()
rec('TC4b', 'A full roster can be generated again after reset', r3['total_assigned'] == 10, f"assigned={r3['total_assigned']}")

# leave (TC7)
seed()
alice = Officer.objects.get(name='Alice Mwangi'); david = Officer.objects.get(name='David Kamau')
for o in (alice, david):
    LeaveRequest.objects.create(officer=o, start_date=date(2026, 10, 20), end_date=date(2026, 11, 10), status='approved')
LeaveRequest.objects.create(officer=Officer.objects.get(name='Brian Otieno'), start_date=date(2026, 10, 20),
                            end_date=date(2026, 11, 10), status='pending')
rl = c.post('/api/rotate/', data=json.dumps({'week_start': '2026-10-23'}), content_type='application/json').json()
asg = {a['officer'] for a in rl['assignments']}
rec('TC7', 'Officers on approved leave are not assigned (pending leave is ignored)',
    ('Alice Mwangi' not in asg) and ('David Kamau' not in asg) and (('Brian Otieno' in asg) or ('Carol Njeri' in asg)),
    f"on approved leave: Alice, David; assigned={sorted(asg)}")

# swap (TC9) and workload (TC10)
seed()
a = Officer.objects.get(name='Brian Otieno'); b = Officer.objects.get(name='Carol Njeri')
sa, sb = Shed.objects.filter(skill_required='Inspection')[:2]
sw = c.post('/api/swap/', data=json.dumps({'requester_id': a.id, 'target_officer_id': b.id,
            'requester_shed_id': sa.id, 'target_shed_id': sb.id, 'reason': 'test'}), content_type='application/json').json()
lst = c.get('/api/swap/list/').json()
rec('TC9', 'Create and list a swap request',
    sw['status'] == 'success' and len(lst['swaps']) == 1 and lst['swaps'][0]['status'] == 'pending',
    f"swaps listed={len(lst['swaps'])}, status={lst['swaps'][0]['status']}")
c.post('/api/rotate/', data='{}', content_type='application/json')
wl = c.get('/api/stats/').json()['workload_distribution']
rec('TC10', 'Workload view lists every officer with points', len(wl) == 12 and sum(o['workload_points'] for o in wl) == 10,
    f"officers listed={len(wl)}, total points={sum(o['workload_points'] for o in wl)}")

order = ['TC1', 'TC2', 'TC3', 'TC4', 'TC4b', 'TC5', 'TC6a', 'TC7', 'TC8', 'TC9', 'TC10', 'TC11', 'TC12', 'TC13']
tests.sort(key=lambda t: order.index(t['id']))
R['tests'] = tests

# --------------------------------------------------------------------- E2 performance
perf = {}
seed(); times = []
for i in range(30):
    reset_all_rotations()
    t = time.perf_counter()
    c.post('/api/rotate/', data=json.dumps({'week_start': '2026-10-23'}), content_type='application/json')
    times.append((time.perf_counter() - t) * 1000)
ts = sorted(times)
perf['kebs_station'] = {'runs': 30, 'mean_ms': st.mean(times), 'median_ms': st.median(times),
                        'p95_ms': ts[int(0.95 * len(ts)) - 1], 'max_ms': max(times)}
scal = []
for m in (1, 2, 5, 10, 20):
    no, ns, npairs = seed(m); tt = []
    for _ in range(5):
        reset_all_rotations()
        t = time.perf_counter(); run_rotation(W0); tt.append((time.perf_counter() - t) * 1000)
    scal.append({'multiplier': m, 'officers': no, 'sheds': ns, 'pairs': npairs, 'median_ms': st.median(tt)})
perf['scalability'] = scal
R['performance'] = perf

# --------------------------------------------------------------------- E3 constraint accuracy
seed(); rng = random.Random(2026)
offs = list(Officer.objects.all())
for o in rng.sample(offs, 3):  # approved leave for three officers across the test window
    LeaveRequest.objects.create(officer=o, start_date=date(2026, 1, 1), end_date=date(2040, 12, 31), status='approved')
leave_ids = set(LeaveRequest.objects.values_list('officer_id', flat=True))
tot = viol_skill = viol_leave = viol_dup = viol_pair = 0; runs_done = 0; cyc_seen = set()
for i in range(200):
    res = run_rotation(W0 + timedelta(weeks=2 * i))
    runs_done += 1
    seen_run = set()
    for a in res['assignments']:
        o = Officer.objects.get(badge_number=a['badge']); s = Shed.objects.get(name=a['shed'])
        tot += 1
        viol_skill += o.skill != s.skill_required
        viol_leave += o.id in leave_ids
        viol_dup += o.id in seen_run; seen_run.add(o.id)
        viol_pair += (o.id, s.id) in cyc_seen; cyc_seen.add((o.id, s.id))
    if res['total_unassigned'] > 0:
        reset_all_rotations(); cyc_seen = set()
R['accuracy'] = {'runs': runs_done, 'assignments': tot, 'skill_violations': int(viol_skill),
                 'leave_violations': int(viol_leave), 'duplicate_in_run': int(viol_dup),
                 'repeated_pair_in_cycle': int(viol_pair)}

# --------------------------------------------------------------------- E4 fairness vs baselines
def jain(xs):
    xs = list(xs); s = sum(xs)
    return (s * s) / (len(xs) * sum(x * x for x in xs)) if s else 1.0

elig = {}  # shed name -> list of officer names
def structures():
    sheds = list(Shed.objects.order_by('-priority', 'name')); offs = list(Officer.objects.all())
    return sheds, offs

def evaluate(policy, nruns=24, seedv=1):
    seed(); sheds, offs = structures(); rng = random.Random(seedv)
    cnt = {o.id: 0 for o in offs}; visited = set(); firsts = 0; premature = 0; resets = 0
    pairs_all = {(o.id, s.id) for s in sheds for o in offs if o.skill == s.skill_required}
    for run in range(nruns):
        used = set(); res = []
        if policy == 'system':
            out = run_rotation(W0 + timedelta(weeks=2 * run))
            if out['total_unassigned'] > 0 and any('reset cycle' in u['reason'] for u in out['unassigned']):
                reset_all_rotations(); resets += 1; out = run_rotation(W0 + timedelta(weeks=2 * run))
            for a in out['assignments']:
                res.append((Officer.objects.get(badge_number=a['badge']).id, Shed.objects.get(name=a['shed']).id))
        else:
            for s in sheds:
                cand = [o for o in offs if o.skill == s.skill_required and o.id not in used]
                if not cand: continue
                o = cand[0] if policy == 'fixed' else rng.choice(cand)
                used.add(o.id); res.append((o.id, s.id))
        for oid, sid in res:
            others_never = any((o.id, sid) not in visited for o in offs if o.skill == next(x.skill_required for x in sheds if x.id == sid) and o.id != oid)
            if (oid, sid) in visited and others_never: premature += 1
            visited.add((oid, sid)); cnt[oid] += 1
    groups = {}
    for o in offs: groups.setdefault(o.skill, []).append(cnt[o.id])
    return {'jain_within_skill': st.mean(jain(g) for g in groups.values()),
            'spread_within_skill': st.mean(max(g) - min(g) for g in groups.values()),
            'pair_coverage_pct': 100 * len(visited & pairs_all) / len(pairs_all),
            'premature_repeats': premature, 'resets': resets,
            'counts': {o.name: cnt[o.id] for o in offs}}

fair = {}
for pol in ('system', 'random', 'fixed'):
    rs_ = [evaluate(pol, 24, sv) for sv in (1, 2, 3, 4, 5)] if pol == 'random' else [evaluate(pol, 24, 1)]
    fair[pol] = {k: st.mean(x[k] for x in rs_) for k in rs_[0] if k != 'counts'}
    fair[pol]['counts_example'] = rs_[0]['counts']
R['fairness'] = fair

# --------------------------------------------------------------------- E5 greedy rule vs exact optimisation
def snapshot_state(rng, visited_p, supervisors=True):
    seed(); offs = list(Officer.objects.all())
    for o in offs:
        o.workload_points = float(rng.randint(0, 5))
        if not supervisors: o.role = 'Officer'
    Officer.objects.bulk_update(offs, ['workload_points', 'role'])
    hs = list(RotationHistory.objects.all())
    for h in hs: h.has_visited = rng.random() < visited_p
    RotationHistory.objects.bulk_update(hs, ['has_visited'])

def exact(state_sheds, state_offs, unvisited):
    BIG = 10_000
    cost = np.full((len(state_sheds), len(state_offs)), BIG, dtype=float)
    for i, s in enumerate(state_sheds):
        for j, o in enumerate(state_offs):
            if o.skill == s.skill_required and (o.id, s.id) in unvisited:
                cost[i, j] = o.workload_points
    ri, ci = linear_sum_assignment(cost)
    ok = [(i, j) for i, j in zip(ri, ci) if cost[i, j] < BIG]
    return len(ok), sum(cost[i, j] for i, j in ok)

e5 = {}
for label, sup, vp in (('no_supervisor_priority', False, 0.0), ('with_supervisor_priority', True, 0.0),
                       ('partly_used_cycle', False, 0.4)):
    rng = random.Random(7); trials = 300; full_g = full_e = same_cost = 0; gaps = []; fill_gap = 0
    for t in range(trials):
        snapshot_state(rng, vp, sup)
        sheds = list(Shed.objects.all()); offs = list(Officer.objects.all())
        unv = {(h.officer_id, h.shed_id) for h in RotationHistory.objects.filter(has_visited=False)}
        n_e, c_e = exact(sheds, offs, unv)
        # cost of the system's choice is measured on the workloads before the run
        wl = {o.id: o.workload_points for o in offs}
        out = run_rotation(W0)
        n_g = out['total_assigned']
        c_g = sum(wl[Officer.objects.get(badge_number=a['badge']).id] for a in out['assignments'])
        full_g += n_g == 10; full_e += n_e == 10
        fill_gap += (n_e - n_g)
        if n_g == n_e: gaps.append(c_g - c_e); same_cost += (c_g == c_e)
    e5[label] = {'trials': trials, 'greedy_fills_all': full_g, 'exact_fills_all': full_e,
                 'sheds_missed_by_greedy_total': int(fill_gap),
                 'cost_equal_pct': 100 * same_cost / max(1, len(gaps)),
                 'mean_extra_workload_points_per_run': st.mean(gaps) if gaps else 0.0}
R['optimisation'] = e5

seed()
json.dump(R, open('results.json', 'w'), indent=2)
print(json.dumps(R, indent=1)[:6000])
