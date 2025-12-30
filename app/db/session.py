"""
Database session management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Lazy engine creation - only create when needed
_engine = None
_SessionLocal = None


def get_engine():
    """Get or create database engine"""
    global _engine
    if _engine is None:
        database_url = settings.DATABASE_URL
        
        # If DATABASE_URL is not set, raise an error with helpful message
        if not database_url:
            raise ValueError(
                "DATABASE_URL is required. Please set it in your .env file.\n"
                "For Supabase, use: postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres"
            )
        
        _engine = create_engine(
            database_url,
            echo=settings.DATABASE_ECHO,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
    return _engine


def get_session_local():
    """Get or create session factory"""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine()
        )
    return _SessionLocal


# For backward compatibility - lazy property-like access
class _LazySessionLocal:
    """Lazy sessionmaker wrapper"""
    def __call__(self):
        return get_session_local()
    
    def __getattr__(self, name):
        return getattr(get_session_local(), name)

SessionLocal = _LazySessionLocal()
