from django.db import models
from django.contrib.auth.models import User


# ── Choices ───────────────────────────────────────────────────────────────────
SKILL_CHOICES = [
    ('Inspection',   'Inspection'),
    ('Fumigation',   'Fumigation'),
    ('Sampling',     'Sampling'),
    ('Clearance',    'Clearance'),
    ('Verification', 'Verification'),
]

ROLE_CHOICES = [
    ('Supervisor', 'Supervisor'),
    ('Officer',    'Officer'),
]

SCHEDULE_STATUS = [
    ('draft',     'Draft'),
    ('pending',   'Pending Approval'),
    ('approved',  'Approved'),
    ('rejected',  'Rejected'),
]

SWAP_STATUS = [
    ('pending',  'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
]

LEAVE_STATUS = [
    ('pending',  'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
]


# ── Core models ───────────────────────────────────────────────────────────────

class Shed(models.Model):
    name           = models.CharField(max_length=100)
    skill_required = models.CharField(max_length=100, choices=SKILL_CHOICES)
    location       = models.CharField(max_length=200, blank=True, default='JKIA')
    priority       = models.IntegerField(default=1, help_text='1=Low, 2=Medium, 3=High')
    min_officers   = models.IntegerField(default=1)
    max_officers   = models.IntegerField(default=2)

    def __str__(self): return self.name
    class Meta: ordering = ['-priority', 'name']


class Officer(models.Model):
    name            = models.CharField(max_length=100)
    badge_number    = models.CharField(max_length=20, unique=True, blank=True, default='')
    skill           = models.CharField(max_length=100, choices=SKILL_CHOICES)
    role            = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Officer')
    workload_points = models.FloatField(default=0.0)
    is_active       = models.BooleanField(default=True)
    email           = models.EmailField(blank=True, default='')

    def __str__(self): return f'{self.name} ({self.role} · {self.skill})'
    class Meta: ordering = ['-role', 'workload_points', 'name']


class LeaveRequest(models.Model):
    """Annual leave — scheduled at start of financial year."""
    officer    = models.ForeignKey(Officer, on_delete=models.CASCADE, related_name='leaves')
    start_date = models.DateField()
    end_date   = models.DateField()
    reason     = models.TextField(blank=True)
    status     = models.CharField(max_length=20, choices=LEAVE_STATUS, default='pending')
    approved_by = models.CharField(max_length=100, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.officer.name}: {self.start_date} to {self.end_date} [{self.status}]'

    class Meta: ordering = ['start_date']


class RotationHistory(models.Model):
    """Tracks each officer→shed assignment with 2-week duration."""
    officer     = models.ForeignKey(Officer, on_delete=models.CASCADE)
    shed        = models.ForeignKey(Shed, on_delete=models.CASCADE)
    has_visited = models.BooleanField(default=False)
    start_date  = models.DateField(null=True, blank=True)
    end_date    = models.DateField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    assigned_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        s = '+' if self.has_visited else 'o'
        return f'[{s}] {self.officer.name} -> {self.shed.name}'

    class Meta:
        unique_together = ('officer', 'shed')
        ordering = ['-assigned_at']


class RotationRun(models.Model):
    """One full rotation generation — requires OIC approval before live."""
    run_at           = models.DateTimeField(auto_now_add=True)
    assignments_json = models.TextField()
    total_assigned   = models.IntegerField(default=0)
    total_unassigned = models.IntegerField(default=0)
    status           = models.CharField(max_length=20, choices=SCHEDULE_STATUS, default='draft')
    approved_by      = models.CharField(max_length=100, blank=True)
    approved_at      = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    week_start       = models.DateField(null=True, blank=True)

    def __str__(self):
        return f'Run #{self.id} [{self.status}] — {self.run_at.strftime("%Y-%m-%d %H:%M")}'

    class Meta: ordering = ['-run_at']


class SwapRequest(models.Model):
    """Officer A requests to swap shed with Officer B."""
    requester       = models.ForeignKey(Officer, on_delete=models.CASCADE, related_name='swap_requests_made')
    target_officer  = models.ForeignKey(Officer, on_delete=models.CASCADE, related_name='swap_requests_received')
    requester_shed  = models.ForeignKey(Shed, on_delete=models.CASCADE, related_name='swap_from')
    target_shed     = models.ForeignKey(Shed, on_delete=models.CASCADE, related_name='swap_to')
    reason          = models.TextField(blank=True)
    status          = models.CharField(max_length=20, choices=SWAP_STATUS, default='pending')
    approved_by     = models.CharField(max_length=100, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    resolved_at     = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return (f'{self.requester.name} ↔ {self.target_officer.name} '
                f'({self.requester_shed.name} ↔ {self.target_shed.name}) [{self.status}]')

    class Meta: ordering = ['-created_at']
