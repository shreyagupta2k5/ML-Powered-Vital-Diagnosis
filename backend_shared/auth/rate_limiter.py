# backend_shared/auth/rate_limiter.py
"""Token bucket rate limiter with Redis-like in-memory storage."""
import time
from collections import defaultdict
from typing import Dict, Optional
from fastapi import HTTPException, status, Request

class TokenBucket:
    """Simple in-memory token bucket rate limiter."""
    
    def __init__(
        self,
        rate: float,  # tokens per second
        capacity: float,  # max bucket size
        key_func: callable = lambda req: req.client.host if req.client else "unknown"
    ):
        self.rate = rate
        self.capacity = capacity
        self.key_func = key_func
        self.buckets: Dict[str, Dict] = defaultdict(
            lambda: {"tokens": capacity, "last_update": time.time()}
        )
    
    def _refill(self, key: str) -> None:
        """Refill tokens based on elapsed time."""
        bucket = self.buckets[key]
        now = time.time()
        elapsed = now - bucket["last_update"]
        bucket["tokens"] = min(self.capacity, bucket["tokens"] + elapsed * self.rate)
        bucket["last_update"] = now
    
    def consume(self, key: str, tokens: float = 1.0) -> bool:
        """Try to consume tokens. Returns True if successful."""
        self._refill(key)
        bucket = self.buckets[key]
        if bucket["tokens"] >= tokens:
            bucket["tokens"] -= tokens
            return True
        return False
    
    def get_retry_after(self, key: str) -> float:
        """Get seconds until next token is available."""
        bucket = self.buckets[key]
        if bucket["tokens"] >= 1:
            return 0.0
        tokens_needed = 1 - bucket["tokens"]
        return tokens_needed / self.rate

# Global rate limiters (configure per endpoint type)
# Default: 100 requests/minute per IP
default_limiter = TokenBucket(rate=100/60, capacity=100)

# Stricter limiter for prediction endpoints (10 req/min to prevent abuse)
prediction_limiter = TokenBucket(rate=10/60, capacity=10)

async def rate_limit_middleware(
    request: Request,
    limiter: Optional[TokenBucket] = None,
    tokens: float = 1.0
):
    """
    FastAPI dependency to enforce rate limiting.
    Usage: dependencies=[Depends(lambda: rate_limit_middleware(request))]
    """
    limiter = limiter or default_limiter
    key = limiter.key_func(request)
    
    if not limiter.consume(key, tokens):
        retry_after = limiter.get_retry_after(key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please slow down.",
            headers={"Retry-After": str(int(retry_after) + 1)}
        )
    
    return True