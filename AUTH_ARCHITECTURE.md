# Distributed Authentication Architecture

This document describes the distributed authentication system architecture that matches the design shown in the architecture diagram.

## Architecture Overview

The authentication system is designed for scalability and resilience with the following components:

```
Login Form → Load Balancer (Heroku Router) → Auth Service 1 & Auth Service 2 (Django Dynos)
                                                      ↓
                                    ┌────────────────┴────────────────┐
                                    ↓                                 ↓
                            Redis Cluster                    Primary DB
                            (Sessions, Cache,                 (User Data)
                             Token Blacklist)
                                    ↓
                            Replica DB
                            (Read Operations)
```

## Components

### 1. Load Balancer
- **Heroku Router**: Automatically handles load balancing across multiple dynos
- Routes requests to available Django instances
- No configuration needed - Heroku handles this automatically

### 2. Auth Services (Django Dynos)
- Multiple Django application instances running on Heroku dynos
- Stateless design using JWT tokens (no server-side session storage needed)
- Each dyno can handle authentication independently
- **Scaling**: Increase dynos in Heroku to scale horizontally

### 3. Redis Cluster
Used for multiple purposes in the distributed architecture:

#### a) Session Storage
- Sessions stored in Redis instead of database
- Makes the app stateless - any dyno can handle any request
- Configuration: `SESSION_ENGINE = 'django.contrib.sessions.backends.cache'`

#### b) JWT Token Blacklist
- Blacklisted tokens stored in Redis
- Enables secure logout and token revocation
- Uses `rest_framework_simplejwt.token_blacklist`

#### c) User Data Caching
- User lookups cached in Redis to reduce database load
- Cache key: `user_lookup:{username_or_email}`
- TTL: 5 minutes
- Reduces database queries during authentication

#### d) Celery Task Queue
- Background tasks (email sending, etc.) use Redis as broker
- Enables async processing across dynos

### 4. Primary Database (PostgreSQL)
- Stores all persistent user data:
  - User accounts
  - User profiles
  - Bank accounts
  - Transactions
  - Verification codes
- Handles all write operations
- **Heroku**: Uses `DATABASE_URL` environment variable

### 5. Replica Database (Read Replica)
- Read-only copy of Primary DB
- Handles read operations to reduce load on primary
- Automatically replicates from Primary DB
- **Heroku**: Set `DATABASE_REPLICA_URL` environment variable to enable
- **Database Router**: Automatically routes reads to replica, writes to primary

## Configuration

### Environment Variables (Heroku Config Vars)

Required:
- `DATABASE_URL` - Primary PostgreSQL database
- `REDIS_URL` - Redis connection string (from Heroku Redis addon)
- `SECRET_KEY` - Django secret key

Optional (for read replicas):
- `DATABASE_REPLICA_URL` - Read replica database URL

### Redis Configuration

Redis is configured for:
1. **Sessions**: `SESSION_ENGINE = 'django.contrib.sessions.backends.cache'`
2. **Caching**: Django cache framework with Redis backend
3. **Celery**: Task queue broker and result backend
4. **JWT Blacklist**: Token blacklist storage

### Database Routing

The `DatabaseRouter` class automatically:
- Routes **read** operations to replica (if configured) or primary
- Routes **write** operations to primary
- Prevents migrations on replica

## Deployment on Heroku

### Prerequisites
1. Heroku Postgres addon (provides `DATABASE_URL`)
2. Heroku Redis addon (provides `REDIS_URL`)
3. Optional: Heroku Postgres follower for read replica (provides `DATABASE_REPLICA_URL`)

### Scaling
- **Horizontal Scaling**: Increase web dynos: `heroku ps:scale web=2`
- **Load Balancing**: Automatic via Heroku router
- **Database Scaling**: Add read replica by creating a follower database

### Stateless Design
- All sessions stored in Redis (not database)
- JWT tokens are stateless (no server storage needed)
- Any dyno can handle any request
- Perfect for Heroku's ephemeral filesystem

## Security Features

1. **JWT Token Blacklist**: Tokens can be revoked on logout
2. **Redis-backed Sessions**: Secure session storage
3. **Database Read/Write Splitting**: Reduces load and improves performance
4. **Cached User Lookups**: Reduces database queries while maintaining security

## Benefits

1. **Scalability**: Easy horizontal scaling by adding dynos
2. **Resilience**: Multiple dynos provide redundancy
3. **Performance**: Redis caching and read replicas reduce database load
4. **Stateless**: Works seamlessly with Heroku's architecture
5. **Cost-effective**: Can scale up/down based on traffic

## Monitoring

- Monitor Redis usage in Heroku dashboard
- Monitor database connections (primary and replica)
- Monitor dyno performance and scaling
- Track authentication success/failure rates

## Migration from Old Architecture

If upgrading from a single-database setup:
1. Add Heroku Redis addon: `heroku addons:create heroku-redis`
2. Deploy updated code (Redis configuration is automatic)
3. Optional: Add read replica: `heroku addons:create heroku-postgresql:standard-0 --follow DATABASE_URL --as DATABASE_REPLICA`
4. Set `DATABASE_REPLICA_URL` config var if using replica

The system will automatically:
- Use Redis for sessions
- Cache user lookups
- Route reads to replica (if configured)
- Blacklist JWT tokens on logout
