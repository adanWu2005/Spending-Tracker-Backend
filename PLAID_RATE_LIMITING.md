# Plaid API Rate Limiting Implementation

## Overview

Rate limiting has been implemented for all Plaid API calls to protect against exceeding Plaid's API rate limits and improve security. This matches the "Rate Limiter" component shown in the architecture diagram.

## Implementation

### Components

1. **PlaidRateLimiter Class** (`api/plaid_rate_limiter.py`)
   - Token bucket algorithm using Redis
   - Tracks requests per hour and per minute
   - Stores rate limit data in Redis for distributed access

2. **Integration in PlaidService** (`api/plaid_service.py`)
   - All Plaid API methods check rate limits before making calls
   - Automatic rate limit enforcement
   - Environment-based rate limit configuration

3. **Error Handling** (`api/views.py`)
   - Rate limit errors return HTTP 429 (Too Many Requests)
   - Clear error messages with reset times
   - Graceful degradation for non-critical operations

## Rate Limits

### Default Limits (Configurable via Environment Variables)

- **Sandbox/Development**: 500 requests/hour, 50 requests/minute
- **Production**: 2000 requests/hour (default, configurable), 50 requests/minute

### Plaid's Actual Limits

- **Sandbox**: 500 requests/hour per client_id
- **Development**: 500 requests/hour per client_id
- **Production**: Varies by plan (typically 500-2000 requests/hour)

## Configuration

### Environment Variables

Set these in Heroku config vars or `.env` file:

```bash
# Optional: Override default rate limits
PLAID_RATE_LIMIT_HOUR=500      # Requests per hour
PLAID_RATE_LIMIT_MINUTE=50     # Requests per minute (burst protection)
```

### Automatic Configuration

The rate limiter automatically adjusts based on `PLAID_ENV`:
- **Sandbox**: 500 requests/hour
- **Development**: 500 requests/hour
- **Production**: 2000 requests/hour (or value from `PLAID_RATE_LIMIT_HOUR`)

## How It Works

1. **Before Each Plaid API Call**:
   - Rate limiter checks Redis for current request count
   - Compares against configured limits (hour and minute)
   - If limit exceeded, raises exception with reset time

2. **Rate Limit Storage**:
   - Uses Redis cache with TTL matching the time window
   - Keys: `plaid_rate_limit:{client_id}:{window}`
   - Distributed across all dynos (shared Redis)

3. **Error Response**:
   - HTTP 429 (Too Many Requests) status code
   - Error message with reset time
   - `rate_limit_exceeded: true` flag in response

## API Endpoints Protected

All Plaid-related endpoints are protected:

1. `/api/plaid/create-link-token/` - Creating link tokens
2. `/api/plaid/exchange-token/` - Exchanging public tokens
3. `/api/plaid/sync-transactions/` - Syncing transactions
   - Also protects balance updates during sync

## Error Handling

### Rate Limit Exceeded Response

```json
{
  "error": "Plaid API rate limit exceeded",
  "message": "Too many requests. Please try again in 3600 seconds.",
  "rate_limit_exceeded": true
}
```

Status Code: `429 Too Many Requests`

### Graceful Degradation

- **Balance Updates**: If rate limit hit during balance update, sync continues without balance update
- **Transaction Sync**: Rate limit errors are caught and returned with clear messages
- **Other Operations**: All operations return proper error responses

## Monitoring

### Check Rate Limit Status

You can check current rate limit status programmatically:

```python
from api.plaid_rate_limiter import PlaidRateLimiter
import os

limiter = PlaidRateLimiter()
client_id = os.getenv('PLAID_CLIENT_ID')
status = limiter.get_rate_limit_info(client_id)

print(f"Hour: {status['hour_used']}/{status['hour_limit']}")
print(f"Minute: {status['minute_used']}/{status['minute_limit']}")
```

## Benefits

1. **Prevents API Key Abuse**: Protects against exceeding Plaid's rate limits
2. **Cost Control**: Prevents unexpected charges from excessive API calls
3. **Improved Security**: Rate limiting is a security best practice
4. **Better Error Handling**: Clear error messages when limits are hit
5. **Distributed**: Works across multiple dynos using shared Redis
6. **Configurable**: Easy to adjust limits per environment

## Architecture Match

This implementation matches the "Rate Limiter" component in the architecture diagram:
- ✅ Rate Limiter component implemented
- ✅ Uses Redis for distributed rate limiting
- ✅ Protects API Server (Django) from excessive Plaid API calls
- ✅ Integrates with OAuth Gateway (JWT authentication)

## Deployment

No additional configuration needed! The rate limiter:
- Uses existing Redis addon
- Automatically detects Plaid environment
- Works with existing authentication system

Just deploy and it works:

```bash
git add .
git commit -m "Add Plaid API rate limiting"
git push heroku main
```

## Testing

### Test Rate Limiting

1. Make rapid requests to Plaid endpoints
2. After exceeding limit, you'll receive 429 responses
3. Wait for reset time and try again

### Monitor in Heroku

```bash
# Check logs for rate limit messages
heroku logs --tail | grep "rate limit"

# Check Redis usage
heroku redis:info
```

## Troubleshooting

### Rate Limits Too Restrictive

Increase limits via environment variables:
```bash
heroku config:set PLAID_RATE_LIMIT_HOUR=2000
heroku config:set PLAID_RATE_LIMIT_MINUTE=100
```

### Rate Limits Not Working

1. Verify Redis is connected: `heroku redis:info`
2. Check environment variables: `heroku config`
3. Check logs: `heroku logs --tail`

### Need Different Limits Per Environment

Set different values in Heroku config vars per app/environment.
