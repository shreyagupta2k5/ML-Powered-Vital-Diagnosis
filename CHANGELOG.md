# Changelog

All notable changes to the ML-Powered Vital Diagnosis System will be documented in this file.

## [1.0.0] - 2026-06-08

### Added
- **Unified FastAPI Gateway:** Single entry point (`backend_main`) orchestrating all track services.
- **Ensemble Layer:** Weighted fusion logic combining eICU, MIMIC, and VitalDB predictions with safety-first conflict resolution.
- **Real-Time Alerts:** WebSocket integration for instant HIGH_RISK notifications to frontend dashboards.
- **MLOps Suite:** 
  - Automated Drift Detection (PSI/KS tests) for all three tracks.
  - Model Registry with hot-swap capabilities.
  - Telemetry logging for audit-compliant inference tracking.
- **Authentication:** JWT-based auth with API key fallback and scope-based permissions.
- **Rate Limiting:** Token bucket algorithm to prevent API abuse.

### Changed
- **Track Mapping:** Standardized internal routing to align Pydantic schemas with backend folder structures (Track 1=eICU, Track 2=MIMIC, Track 3=VitalDB).
- **Drift Monitor:** Updated to use explicit feature lists for robust detection across different data schemas.

### Fixed
- Resolved 502 errors in ensemble routing by implementing graceful degradation wrappers.
- Fixed Swagger UI tagging for Track 3 endpoints.
- Corrected mathematical weighting in ensemble aggregator to reflect clinical priorities.

### Security
- Added global exception handlers for 401, 403, and 429 errors.
- Implemented PHI sanitization in telemetry logs.