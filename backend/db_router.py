"""
Database router for read/write splitting between primary and replica databases.
This enables the distributed architecture with Primary DB and Replica DB.
"""
from django.conf import settings


class DatabaseRouter:
    """
    Routes database operations to primary (write) or replica (read) databases.
    This enables horizontal scaling with read replicas.
    """
    
    def db_for_read(self, model, **hints):
        """Route read operations to replica database if available."""
        # Check if replica database is configured
        if 'replica' in settings.DATABASES:
            # Route read operations to replica
            return 'replica'
        # Fallback to default (primary) if no replica
        return 'default'
    
    def db_for_write(self, model, **hints):
        """Route write operations to primary database."""
        return 'default'
    
    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations between objects from different databases."""
        # Allow relations between primary and replica
        db_set = {'default', 'replica'}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Only allow migrations on the primary database."""
        if db == 'replica':
            # Never run migrations on replica
            return False
        return None
