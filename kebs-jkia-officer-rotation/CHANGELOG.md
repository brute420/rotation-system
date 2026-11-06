# Changelog

## v2.1
### Fixed
- **Roster results were never shown in the interface.** The API returned the roster run's status
  (`"pending"`) in the same `status` field that the front end reads to detect success, so every
  roster was treated as an error. The run status is now returned as `run_status`.
- **An officer could be assigned to two sheds in the same run.** Added constraint C7
  (one shed per officer per run).
- Unassigned sheds now report a clear reason when the remaining eligible officers are already
  assigned in the same run.
### Changed
- `settings.py` reads `DJANGO_SECRET_KEY`, `DJANGO_DEBUG` and `DJANGO_ALLOWED_HOSTS` from the
  environment (safe defaults for local development).
- Added `backend/experiments.py` (functional tests, accuracy, performance, fairness and
  optimality experiments) and the initial database migration.

## v2.0
- Leave management, shed swap requests, supervisor priority, two-week assignment windows and
  an approval workflow for roster runs.

## v1.0
- First prototype: skill-matched rotation with rotation-history tracking.
