from django.contrib import admin
from django.urls import path
from rotation.views import (
    # Rotation
    trigger_rotation, approve_run, reject_run, reset_rotation,
    get_runs,
    # Stats & lists
    get_dashboard_stats, get_officers, get_sheds,
    # Leave
    create_leave, get_leaves, action_leave,
    # Swaps
    create_swap, get_swaps, action_swap,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # ── Rotation
    path('api/rotate/',              trigger_rotation),
    path('api/rotate/reset/',        reset_rotation),
    path('api/runs/',                get_runs),
    path('api/runs/<int:run_id>/approve/', approve_run),
    path('api/runs/<int:run_id>/reject/',  reject_run),

    # ── Core data
    path('api/stats/',               get_dashboard_stats),
    path('api/officers/',            get_officers),
    path('api/sheds/',               get_sheds),

    # ── Leave management
    path('api/leave/',               create_leave),
    path('api/leave/list/',          get_leaves),
    path('api/leave/<int:leave_id>/action/', action_leave),

    # ── Swap requests
    path('api/swap/',                create_swap),
    path('api/swap/list/',           get_swaps),
    path('api/swap/<int:swap_id>/action/', action_swap),
]
