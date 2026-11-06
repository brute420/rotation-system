"""
KEBS JKIA Officer Rotation System — Seed Script (v2)
Based on questionnaire: 12 officers, 10 sheds, competence-based rotation.

Run from backend/ with venv active:
    python rotation/seed.py
"""
import os, sys, django
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from rotation.models import Officer, Shed, RotationHistory, RotationRun, LeaveRequest, SwapRequest

print("═" * 55)
print("  KEBS JKIA Rotation System — Seeding Database (v2)")
print("═" * 55)

# ── Clear all existing data ────────────────────────────────────────────────────
SwapRequest.objects.all().delete()
LeaveRequest.objects.all().delete()
RotationHistory.objects.all().delete()
RotationRun.objects.all().delete()
Officer.objects.all().delete()
Shed.objects.all().delete()
print("✓ Cleared existing data")

# ── Sheds (10, 2 per skill, with priority levels) ─────────────────────────────
# Priority: 3=High (perishables/hazardous), 2=Medium, 1=Low
sheds_data = [
    # name                    skill            location         priority min max
    ('Swissport Shed A',       'Inspection',   'Terminal 1A',   2,       1,  2),
    ('Swissport Shed B',       'Inspection',   'Terminal 1B',   2,       1,  2),
    ('Siginon Cold Storage',   'Fumigation',   'Cargo Village', 3,       1,  2),
    ('Siginon Express',        'Fumigation',   'Cargo Village', 3,       1,  2),
    ('KAHL Warehouse 1',       'Sampling',     'JKIA South',    2,       1,  2),
    ('KAHL Warehouse 2',       'Sampling',     'JKIA South',    2,       1,  2),
    ('KQ Cargo Gate',          'Clearance',    'Terminal 2',    1,       1,  2),
    ('Express Freight Gate',   'Clearance',    'Terminal 2',    1,       1,  2),
    ('Verification Bay Alpha', 'Verification', 'JKIA North',    2,       1,  2),
    ('Verification Bay Beta',  'Verification', 'JKIA North',    2,       1,  2),
]

sheds = []
for name, skill, location, priority, min_o, max_o in sheds_data:
    shed = Shed.objects.create(
        name=name, skill_required=skill, location=location,
        priority=priority, min_officers=min_o, max_officers=max_o
    )
    sheds.append(shed)
print(f"✓ Created {len(sheds)} sheds")

# ── Officers (12 total from questionnaire — 2-3 per skill) ───────────────────
# 2 Supervisors, 10 regular Officers
# Distribution: Inspection x3, Fumigation x3, Sampling x2, Clearance x2, Verification x2
officers_data = [
    # name                  badge       skill            role         email
    ('Alice Mwangi',       'KEBS-001', 'Inspection',   'Supervisor', 'alice.mwangi@kebs.go.ke'),
    ('Brian Otieno',       'KEBS-002', 'Inspection',   'Officer',    'brian.otieno@kebs.go.ke'),
    ('Carol Njeri',        'KEBS-003', 'Inspection',   'Officer',    'carol.njeri@kebs.go.ke'),
    ('David Kamau',        'KEBS-004', 'Fumigation',   'Supervisor', 'david.kamau@kebs.go.ke'),
    ('Esther Wanjiku',     'KEBS-005', 'Fumigation',   'Officer',    'esther.wanjiku@kebs.go.ke'),
    ('Francis Odhiambo',   'KEBS-006', 'Fumigation',   'Officer',    'francis.odhiambo@kebs.go.ke'),
    ('Grace Akinyi',       'KEBS-007', 'Sampling',     'Officer',    'grace.akinyi@kebs.go.ke'),
    ('Henry Mutua',        'KEBS-008', 'Sampling',     'Officer',    'henry.mutua@kebs.go.ke'),
    ('Irene Chebet',       'KEBS-009', 'Clearance',    'Officer',    'irene.chebet@kebs.go.ke'),
    ('James Kariuki',      'KEBS-010', 'Clearance',    'Officer',    'james.kariuki@kebs.go.ke'),
    ('Kevin Ndirangu',     'KEBS-011', 'Verification', 'Officer',    'kevin.ndirangu@kebs.go.ke'),
    ('Lucy Waithera',      'KEBS-012', 'Verification', 'Officer',    'lucy.waithera@kebs.go.ke'),
]

officers = []
for name, badge, skill, role, email in officers_data:
    officer = Officer.objects.create(
        name=name, badge_number=badge, skill=skill,
        role=role, email=email, workload_points=0.0, is_active=True
    )
    officers.append(officer)
print(f"✓ Created {len(officers)} officers  (2 Supervisors, 10 Officers)")

# ── RotationHistory: each officer ↔ each matching shed ───────────────────────
pair_count = 0
for shed in sheds:
    for officer in officers:
        if officer.skill == shed.skill_required:
            RotationHistory.objects.create(
                officer=officer, shed=shed, has_visited=False
            )
            pair_count += 1
print(f"✓ Created {pair_count} rotation history pairs")

# ── Sample leave requests (financial year planning) ───────────────────────────
sample_leaves = [
    ('KEBS-001', date(2025, 4, 1),  date(2025, 4, 14),  'Annual leave Q1', 'approved'),
    ('KEBS-005', date(2025, 7, 7),  date(2025, 7, 18),  'Annual leave Q2', 'approved'),
    ('KEBS-009', date(2025, 12, 22),date(2025, 12, 31), 'Festive season',  'approved'),
]
leave_count = 0
for badge, start, end, reason, status in sample_leaves:
    try:
        officer = Officer.objects.get(badge_number=badge)
        LeaveRequest.objects.create(
            officer=officer, start_date=start, end_date=end,
            reason=reason, status=status, approved_by='Operations Manager'
        )
        leave_count += 1
    except Officer.DoesNotExist:
        pass
print(f"✓ Created {leave_count} sample leave records")

# ── Summary ───────────────────────────────────────────────────────────────────
print()
print("═" * 55)
print("  Seeding Complete")
print("═" * 55)
print(f"  Sheds           : {len(sheds)}")
print(f"  Officers        : {len(officers)}")
print(f"  Rotation pairs  : {pair_count}")
print(f"  Leave records   : {leave_count}")
print()
print("  Skill breakdown:")
skills = ['Inspection', 'Fumigation', 'Sampling', 'Clearance', 'Verification']
for skill in skills:
    o = sum(1 for _,_,s,_,_ in officers_data if s == skill)
    s = sum(1 for _,sk,_,_,_,_ in sheds_data if sk == skill)
    print(f"    {skill:<14} {o} officers × {s} sheds = {o*s} pairs")
print()
print("  Next: python manage.py runserver")
