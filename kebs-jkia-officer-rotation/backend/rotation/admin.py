from django.contrib import admin
from .models import Officer, Shed, RotationHistory, RotationRun, LeaveRequest, SwapRequest


@admin.register(Shed)
class ShedAdmin(admin.ModelAdmin):
    list_display  = ('name', 'skill_required', 'location', 'priority', 'min_officers', 'max_officers')
    list_filter   = ('skill_required', 'priority')
    search_fields = ('name',)
    list_editable = ('priority',)


@admin.register(Officer)
class OfficerAdmin(admin.ModelAdmin):
    list_display  = ('name', 'badge_number', 'role', 'skill', 'workload_points', 'is_active', 'email')
    list_filter   = ('role', 'skill', 'is_active')
    search_fields = ('name', 'badge_number')
    list_editable = ('is_active', 'role')


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display  = ('officer', 'start_date', 'end_date', 'status', 'approved_by')
    list_filter   = ('status',)
    search_fields = ('officer__name',)
    list_editable = ('status',)


@admin.register(RotationHistory)
class RotationHistoryAdmin(admin.ModelAdmin):
    list_display  = ('officer', 'shed', 'has_visited', 'start_date', 'end_date')
    list_filter   = ('has_visited', 'shed__skill_required')
    search_fields = ('officer__name', 'shed__name')
    list_editable = ('has_visited',)


@admin.register(RotationRun)
class RotationRunAdmin(admin.ModelAdmin):
    list_display    = ('id', 'run_at', 'status', 'total_assigned', 'total_unassigned', 'approved_by', 'week_start')
    list_filter     = ('status',)
    readonly_fields = ('run_at', 'assignments_json', 'total_assigned', 'total_unassigned')
    list_editable   = ('status',)


@admin.register(SwapRequest)
class SwapRequestAdmin(admin.ModelAdmin):
    list_display  = ('requester', 'target_officer', 'requester_shed', 'target_shed', 'status', 'created_at')
    list_filter   = ('status',)
    search_fields = ('requester__name', 'target_officer__name')
