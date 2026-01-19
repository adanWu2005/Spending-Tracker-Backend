# Fix for Missing Token Blacklist Tables

## Problem
The error shows that the `token_blacklist_outstandingtoken` table doesn't exist. This is because migrations for the `rest_framework_simplejwt.token_blacklist` app haven't been run on Heroku.

## Solution

Run migrations on Heroku:

```bash
heroku run python manage.py migrate
```

This will create all the necessary tables for the token blacklist feature.

## Alternative: If migrations fail

If you get errors, you may need to create migrations first:

```bash
# Create migrations locally first
python manage.py makemigrations

# Then commit and push
git add .
git commit -m "Add token blacklist migrations"
git push heroku main

# Then run migrations on Heroku
heroku run python manage.py migrate
```

## Verify

After running migrations, check that the tables exist:

```bash
heroku run python manage.py shell
>>> from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
>>> OutstandingToken.objects.count()
```

If this doesn't error, the tables are created successfully.
