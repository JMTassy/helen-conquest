# STEP_4A_LIVE_CHECKLIST_V1

## Purpose
Run live /do_next conformance checks against the running API server.

## Prerequisites
- Server running at `http://localhost:8000`
- Storage directory exists: `storage/do_next_sessions`

## Run Script
From repo root:

```
python3 scripts/step_4a_live_conformance.py
```

## Output
Report written to:

`GOVERNANCE/STEP_4_CONFORMANCE/conformance_reports/STEP_4A_LIVE_CONFORMANCE_REPORT_V1.md`

## If You Need Custom Base URL
```
HELEN_BASE_URL=http://localhost:8000 python3 scripts/step_4a_live_conformance.py
```

## If Storage Directory Differs
```
HELEN_DO_NEXT_STORAGE=/absolute/path/to/storage/do_next_sessions \
python3 scripts/step_4a_live_conformance.py
```
