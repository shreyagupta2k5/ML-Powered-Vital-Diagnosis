# Release Notes: v1.0.0

## Overview
The ML-Powered Vital Diagnosis System v1.0.0 is now ready for frontend integration. This release provides a unified, secure, and real-time capable backend for ICU mortality and multimorbidity prediction.

## Key Features for Frontend Team
1. **Single Endpoint for All Predictions:** Use `/api/v1/ensemble/predict` to get a unified risk score from all three models simultaneously.
2. **Live Dashboard Support:** Connect to `ws://.../ws/alerts/{patient_id}` to receive instant alerts when a patient's risk tier escalates to CRITICAL or HIGH.
3. **Comprehensive Documentation:** All endpoints are fully documented in the interactive Swagger UI at `/docs`.

## Breaking Changes
- None. This is the initial stable release.

## Known Issues
- The `/health` endpoint may report tracks as "unreachable" if individual track servers are not running on separate ports, but internal routing via the main gateway remains fully functional.

## How to Start
1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Run the server: `uvicorn backend_main.main:app --reload --port 8000`
4. Visit `http://localhost:8000/docs` to test endpoints.

## Support
For API contract questions, refer to the "Frontend API Contract" document provided by the backend team.