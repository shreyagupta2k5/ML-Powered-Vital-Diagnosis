# Authentication & Rate Limiting

## JWT Authentication
- Tokens issued via `/auth/token` endpoint (to be implemented)
- Bearer token in `Authorization` header
- Claims: `sub` (user ID), `scopes` (permissions), `exp` (expiry)

## API Key Fallback
- For service-to-service communication
- Keys configured via `API_KEYS` env var (comma-separated)
- Send via `X-API-Key` header

## Rate Limiting
- Default: 100 requests/minute per IP
- Prediction endpoints: 10 requests/minute (configurable)
- Returns `429 Too Many Requests` with `Retry-After` header


## Environment Variables
```env
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
API_KEYS=key1,key2,key3
```

## Usage Example
```python
from fastapi import Depends
from backend_shared.auth import get_current_user, require_scope, rate_limit_middleware

@app.post("/predict")
async def predict(
    user = Depends(get_current_user),
    _ = Depends(lambda: rate_limit_middleware(request, prediction_limiter))
):
    # Only users with 'predict' scope can call this
    if "predict" not in user.scopes:
        raise HTTPException(403, "Predict scope required")
    ...
```

---