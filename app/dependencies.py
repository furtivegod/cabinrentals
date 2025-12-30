"""
Dependency injection for FastAPI
"""
from app.db.supabase import get_supabase_client
from supabase import Client


def get_supabase() -> Client:
    """
    Supabase client dependency
    """
    return get_supabase_client()

