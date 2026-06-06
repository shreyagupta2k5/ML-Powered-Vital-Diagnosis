# API Reference

## Authentication

### POST /login

User authentication endpoint.

---

## WebSocket Alerts

### WS /ws/alerts/{patient_id}

Real-time patient alert stream.

Example:

ws://localhost:8000/ws/alerts/123

---

## Alert Types

HIGH_RISK

DRIFT_DETECTED

MODEL_UPDATED

---

## Error Codes

400 Bad Request

401 Unauthorized

404 Not Found

500 Internal Server Error