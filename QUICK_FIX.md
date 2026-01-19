# Quick Fix for Token Blacklist Error

## Immediate Fix

**Step 1: Run migrations on Heroku**

```bash
heroku run python manage.py migrate
```

This will create all necessary tables and fix the login error.

**Step 2: Enable blacklist features**

After migrations complete, update `backend/settings.py` to enable blacklist:

Change these lines:
```python
"ROTATE_REFRESH_TOKENS": False,  # Set to True after migrations
"BLACKLIST_AFTER_ROTATION": False,  # Set to True after migrations
```

To:
```python
"ROTATE_REFRESH_TOKENS": True,  # Enabled after migrations
"BLACKLIST_AFTER_ROTATION": True,  # Enabled after migrations
```

Then deploy:
```bash
git add backend/backend/settings.py
git commit -m "Enable token blacklist after migrations"
git push heroku main
```

## What Changed

I've updated the code to:
1. **Disable blacklist features** by default (prevents errors before migrations)
2. **Graceful logout** - logout works even without blacklist tables
3. **Clear instructions** to enable after migrations

## After Running Migrations

Once migrations are run and settings updated, blacklist features will enable:
- Token rotation on refresh
- Token blacklisting on logout
- Secure token revocation

## Verify It's Fixed

After running migrations, check logs:

```bash
heroku logs --tail
```

You should see:
```
✅ Token blacklist tables found. Blacklist features enabled.
```

Instead of:
```
⚠️  WARNING: Token blacklist tables not found...
```

## If Migrations Fail

If you get errors during migration, you may need to create migrations locally first:

```bash
# Locally
python manage.py makemigrations
git add .
git commit -m "Add token blacklist migrations"
git push heroku main

# Then on Heroku
heroku run python manage.py migrate
```

## Memory Issue (R14)

The memory warning (R14) is separate. If it persists:
1. Check worker dyno memory usage
2. Consider upgrading dyno size
3. Review Celery worker configuration

But first, fix the migration issue above - that's causing the immediate error.
