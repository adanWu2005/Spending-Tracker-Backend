# Deployment Notes for Distributed Auth Architecture

## Quick Deploy Checklist

Your authentication system now matches the distributed architecture diagram. To deploy:

### 1. Update Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Run Migrations
The new `token_blacklist` app needs migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Heroku Configuration

#### Required Addons
1. **Heroku Postgres** (provides `DATABASE_URL`)
   ```bash
   heroku addons:create heroku-postgresql:standard-0
   ```

2. **Heroku Redis** (provides `REDIS_URL`)
   ```bash
   heroku addons:create heroku-redis:premium-0
   ```

#### Optional: Read Replica
To enable read replicas (matches the architecture diagram):
```bash
heroku addons:create heroku-postgresql:standard-0 --follow DATABASE_URL --as DATABASE_REPLICA
```
This automatically sets `DATABASE_REPLICA_URL` config var.

### 4. Environment Variables

The following are automatically set by Heroku addons:
- `DATABASE_URL` - Set by Heroku Postgres
- `REDIS_URL` - Set by Heroku Redis
- `DATABASE_REPLICA_URL` - Set if you create a follower database

You still need to set:
- `SECRET_KEY` - Django secret key
- `ALLOWED_HOSTS` - Your Heroku app domain
- Other API keys (Plaid, OpenAI, etc.)

### 5. Deploy to Heroku

```bash
git add .
git commit -m "Implement distributed auth architecture with Redis and read replicas"
git push heroku main
```

### 6. Run Migrations on Heroku

**IMPORTANT**: You MUST run migrations after deploying, especially for the token_blacklist app:

```bash
heroku run python manage.py migrate
```

If you see errors about missing `token_blacklist_*` tables, this means migrations haven't been run. Run the command above.

**Note**: The token_blacklist app requires database tables. If migrations fail, you may need to create migrations locally first:

```bash
# Locally
python manage.py makemigrations
git add .
git commit -m "Add token blacklist migrations"
git push heroku main

# Then on Heroku
heroku run python manage.py migrate
```

### 7. Scale Dynos (Optional)

To match the architecture with multiple auth services:
```bash
heroku ps:scale web=2
```

This creates 2 web dynos (Auth Service 1 & Auth Service 2 in the diagram).

## Architecture Verification

After deployment, verify:

1. **Redis is working**: Check Heroku logs for Redis connection
2. **Sessions in Redis**: Login and verify session is stored in Redis (not database)
3. **Read Replicas**: If configured, verify reads go to replica
4. **Load Balancing**: Heroku router automatically balances across dynos
5. **Token Blacklist**: Logout should blacklist tokens in Redis

## What Changed

### New Files
- `backend/db_router.py` - Database routing for read/write splitting
- `backend/AUTH_ARCHITECTURE.md` - Architecture documentation
- `backend/DEPLOYMENT_NOTES.md` - This file

### Modified Files
- `backend/requirements.txt` - Added `django-redis`
- `backend/backend/settings.py` - Redis configuration, database routing, JWT blacklist
- `backend/api/views.py` - Redis caching for user lookups, logout endpoint
- `backend/api/urls.py` - Added logout endpoint

### New Features
1. **Redis Session Storage**: Sessions stored in Redis (stateless)
2. **JWT Token Blacklist**: Tokens can be revoked on logout
3. **User Lookup Caching**: User data cached in Redis
4. **Database Read Replicas**: Automatic read/write splitting
5. **Logout Endpoint**: `/api/logout/` to blacklist tokens

## Testing

### Test Redis Connection
```bash
heroku run python manage.py shell
>>> from django.core.cache import cache
>>> cache.set('test', 'value', 60)
>>> cache.get('test')
'value'
```

### Test Database Routing
```bash
heroku run python manage.py shell
>>> from django.contrib.auth.models import User
>>> # Read should go to replica (if configured)
>>> user = User.objects.first()
>>> # Write should go to primary
>>> user.save()
```

### Test Logout
```bash
curl -X POST https://your-app.herokuapp.com/api/logout/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"refresh": "YOUR_REFRESH_TOKEN"}'
```

## Rollback Plan

If you need to rollback:
1. Remove `django-redis` from requirements.txt
2. Change `SESSION_ENGINE` back to `'django.contrib.sessions.backends.db'`
3. Remove database router configuration
4. Remove token blacklist app from INSTALLED_APPS
5. Deploy again

## Monitoring

Monitor these in Heroku dashboard:
- **Redis Metrics**: Memory usage, connections
- **Database Metrics**: Primary and replica connections
- **Dyno Metrics**: CPU, memory, response time
- **Logs**: Check for Redis connection errors

## Support

If you encounter issues:
1. Check Heroku logs: `heroku logs --tail`
2. Verify Redis addon is active: `heroku addons`
3. Verify environment variables: `heroku config`
4. Test Redis connection (see Testing section above)
