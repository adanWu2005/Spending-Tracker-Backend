# API Key Rate Limiting Implementation

## Overview

This application now implements comprehensive rate limiting for API keys using Redis, matching the architecture diagram that shows a Rate Limiter component.

## Features

### 1. API Key Authentication
- API keys can be used instead of JWT tokens for authentication
- Supports header format: `Api-Key: <key>` or `Authorization: Api-Key <key>`
- Each API key is associated with a user account
- API keys can be activated/deactivated and have expiration dates

### 2. Redis-Based Rate Limiting
- **Per-Minute Limits**: Configurable requests per minute
- **Per-Hour Limits**: Configurable requests per hour
- **Per-Day Limits**: Configurable requests per day
- All rate limiting data stored in Redis for fast access
- Works across multiple dynos (stateless)

### 3. Default Rate Limits
- **Anonymous Users**: 100 requests/hour
- **JWT Authenticated Users**: 1000 requests/hour
- **API Keys**: Customizable per key (default: 60/min, 1000/hour, 10000/day)

## API Key Management

### Create API Key
```bash
POST /api/api-keys/
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "name": "My API Key",
  "rate_limit_per_minute": 60,
  "rate_limit_per_hour": 1000,
  "rate_limit_per_day": 10000,
  "expires_at": "2025-12-31T23:59:59Z"  # Optional
}
```

Response:
```json
{
  "id": 1,
  "name": "My API Key",
  "key": "generated-api-key-here",
  "user": 1,
  "is_active": true,
  "rate_limit_per_minute": 60,
  "rate_limit_per_hour": 1000,
  "rate_limit_per_day": 10000,
  "last_used": null,
  "created_at": "2025-01-01T00:00:00Z",
  "expires_at": "2025-12-31T23:59:59Z",
  "is_expired": false,
  "is_valid": true
}
```

### List API Keys
```bash
GET /api/api-keys/
Authorization: Bearer <jwt_token>
```

### Get API Key Details
```bash
GET /api/api-keys/<id>/
Authorization: Bearer <jwt_token>
```

### Update API Key
```bash
PATCH /api/api-keys/<id>/
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "rate_limit_per_minute": 120,
  "is_active": true
}
```

### Delete/Deactivate API Key
```bash
DELETE /api/api-keys/<id>/
Authorization: Bearer <jwt_token>
```

Note: Deletion actually deactivates the key (soft delete) for audit trail.

### Get API Key Usage Statistics
```bash
GET /api/api-keys/<id>/stats/
Authorization: Bearer <jwt_token>
```

Response:
```json
{
  "api_key_id": 1,
  "name": "My API Key",
  "rate_limits": {
    "per_minute": {
      "limit": 60,
      "used": 5,
      "remaining": 55
    },
    "per_hour": {
      "limit": 1000,
      "used": 150,
      "remaining": 850
    },
    "per_day": {
      "limit": 10000,
      "used": 2000,
      "remaining": 8000
    }
  },
  "last_used": "2025-01-01T12:00:00Z",
  "is_active": true,
  "is_expired": false,
  "is_valid": true
}
```

## Using API Keys

### Authentication with API Key

**Option 1: Api-Key Header**
```bash
GET /api/transactions/
Api-Key: your-api-key-here
```

**Option 2: Authorization Header**
```bash
GET /api/transactions/
Authorization: Api-Key your-api-key-here
```

### Rate Limit Headers

When using API keys, the response includes rate limit information:

```
X-RateLimit-Limit-Minute: 60
X-RateLimit-Remaining-Minute: 55
X-RateLimit-Limit-Hour: 1000
X-RateLimit-Remaining-Hour: 850
X-RateLimit-Limit-Day: 10000
X-RateLimit-Remaining-Day: 8000
```

### Rate Limit Exceeded Response

When rate limit is exceeded:
```json
{
  "detail": "Request was throttled. Expected available in 60 seconds."
}
```

Status Code: `429 Too Many Requests`

## Architecture

### Rate Limiter Component
- **Location**: Between User and API Server (as shown in diagram)
- **Implementation**: Django REST Framework throttling classes
- **Storage**: Redis cache (shared across all dynos)
- **Scope**: Per API key, per user, or per anonymous user

### Flow
1. Request arrives with API key
2. `APIKeyAuthentication` validates the key
3. `APIKeyRateThrottle` checks Redis for rate limits
4. If within limits, request proceeds to API Server
5. If exceeded, returns 429 error

## Configuration

### Default Rate Limits (settings.py)
```python
"DEFAULT_THROTTLE_RATES": {
    "anon": "100/hour",      # Anonymous users
    "user": "1000/hour",      # JWT authenticated users
}
```

### Per-API-Key Rate Limits
Set when creating or updating an API key:
- `rate_limit_per_minute`: Default 60
- `rate_limit_per_hour`: Default 1000
- `rate_limit_per_day`: Default 10000

## Security Features

1. **API Key Generation**: Uses `secrets.token_urlsafe()` for cryptographically secure keys
2. **Key Storage**: Keys stored in database (hashed recommended for production)
3. **Expiration**: Optional expiration dates for keys
4. **Deactivation**: Keys can be deactivated without deletion (audit trail)
5. **User Isolation**: Each user can only manage their own API keys
6. **Rate Limit Isolation**: Each API key has independent rate limits

## Redis Storage

Rate limiting data is stored in Redis with keys:
- `throttle_apikey_{key}_minute` - Per-minute counter (TTL: 60s)
- `throttle_apikey_{key}_hour` - Per-hour counter (TTL: 3600s)
- `throttle_apikey_{key}_day` - Per-day counter (TTL: 86400s)

## Deployment

### Migrations Required
```bash
python manage.py makemigrations
python manage.py migrate
```

### Heroku Deployment
1. Ensure Redis addon is active (provides `REDIS_URL`)
2. Deploy code: `git push heroku main`
3. Run migrations: `heroku run python manage.py migrate`

### Testing
```bash
# Create an API key
curl -X POST https://your-app.herokuapp.com/api/api-keys/ \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Key"}'

# Use the API key
curl https://your-app.herokuapp.com/api/transactions/ \
  -H "Api-Key: <your-api-key>"
```

## Monitoring

- Check API key usage via `/api/api-keys/<id>/stats/` endpoint
- Monitor Redis memory usage for rate limiting data
- Track 429 responses in application logs
- Use Heroku metrics to monitor request rates

## Best Practices

1. **Rotate Keys Regularly**: Deactivate old keys and create new ones
2. **Set Appropriate Limits**: Match rate limits to expected usage
3. **Monitor Usage**: Regularly check usage statistics
4. **Use Expiration**: Set expiration dates for temporary keys
5. **Secure Storage**: Store API keys securely (never in code or logs)
