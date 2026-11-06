# KEBS JKIA Officer Rotation System

A web-based, skill-based officer rotation and roster management system, developed as a final-year
research project for the Kenya Bureau of Standards (KEBS) station at Jomo Kenyatta International
Airport (JKIA). It assigns officers to cargo sheds by competence, tracks rotation history, respects
approved leave, and requires the Officer in Charge to approve each generated roster.

> **Sample data only.** All officer names, badge numbers and e-mail addresses in `seed.py` are
> fictional placeholders. Do not commit real personal data to this repository.
>
> **Development build.** The API has no authentication and CSRF is disabled on POST endpoints.
> Do not expose it to the internet. See *Security notes* below.

## Features

| Area | What it does |
|---|---|
| Roster generation | Assigns one officer to each shed for a two-week window using rules C1 to C7 |
| Approval workflow | A generated roster is *pending* until the Officer in Charge approves or rejects it |
| Leave management | Officers on approved leave in the window are never assigned |
| Swap requests | Record, list, approve or reject an exchange of sheds between two officers |
| Rotation history | Each officer-shed pair is used once per cycle; the cycle can be reset |
| Dashboard | Officers, sheds, completed and pending pairs, runs awaiting approval, workload view |

## Assignment rules

| ID | Rule | Type |
|---|---|---|
| C1 | Officer competence equals the competence the shed requires | Hard |
| C2 | The officer-shed pair has not been used in the current cycle | Hard |
| C3 | Supervisors are preferred when eligible | Priority |
| C4 | Among the same role, the officer with the fewest workload points is chosen | Fairness |
| C5 | No approved leave overlapping the two-week window | Hard |
| C6 | Officer is active | Hard |
| C7 | An officer works at one shed per roster run | Hard |

## Tech stack

Python, Django, Django REST Framework, django-cors-headers, SQLite, React 18, Vite.

## Quick start

Requirements: Python 3.10+ and Node.js 18+.

### Backend (port 8000)

```bash
cd backend
python -m venv venv
# Windows:   venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r ../requirements.txt
python manage.py migrate
python rotation/seed.py          # 12 officers, 10 sheds, 24 rotation pairs
python manage.py createsuperuser # optional, for /admin
python manage.py runserver
```

### Frontend (port 5173)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Generate a roster, approve it on the **Approvals** tab, and use
**Reset Cycle** when every pair has been used.

## API

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/rotate/` | Generate a roster (`status: "success"`, `run_status: "pending"`) |
| POST | `/api/rotate/reset/` | Start a new cycle |
| GET | `/api/runs/` | List roster runs |
| POST | `/api/runs/<id>/approve/` · `/reject/` | Approve or reject a run |
| GET | `/api/stats/` · `/api/officers/` · `/api/sheds/` | Dashboard data |
| POST | `/api/leave/` · GET `/api/leave/list/` · POST `/api/leave/<id>/action/` | Leave requests |
| POST | `/api/swap/` · GET `/api/swap/list/` · POST `/api/swap/<id>/action/` | Swap requests |

## Evaluation scripts

`backend/experiments.py` runs the functional tests, constraint-accuracy check, response-time and
scalability measurements, fairness comparison with baseline policies, and a comparison of the
greedy rule with an exact assignment (Hungarian method). It **wipes and reseeds the database**, so
run it only on a development copy:

```bash
pip install -r requirements-dev.txt
cd backend && python experiments.py   # writes results.json
```

## Known limitations

- One cycle is shared by all competence groups, so groups with two officers exhaust their pairs
  sooner than groups with three, and a reset clears the visit history.
- Supervisor priority (C3) means supervisors are chosen in every run when eligible.
- Greedy selection can leave a shed unassigned when a complete assignment exists and the cycle is
  partly used; an exact matching step would remove this.
- Roster generation time grows with the number of officer-shed pairs (about 46 ms at 12 officers,
  about 5 s at 240 officers in the test environment).
- Not yet implemented: role-based login, e-mail notification, PDF/Excel/calendar export, integration
  with the Norming system.

## Security notes

- Set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0` and `DJANGO_ALLOWED_HOSTS` before any deployment.
- Add authentication and re-enable CSRF protection before real use.

## Repository layout

```
backend/    Django project (core/) and rotation app (models, logic, views, seed, experiments)
frontend/   React + Vite single-page application
```
