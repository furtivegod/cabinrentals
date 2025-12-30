"""
Supabase client management
"""
from supabase import create_client, Client
from app.config import settings

_supabase_client: Client | None = None


def get_supabase_client() -> Client:
    """Get or create Supabase client"""
    global _supabase_client
    if _supabase_client is None:
        if not settings.SUPABASE_URL:
            raise ValueError("SUPABASE_URL is required. Please set it in your .env file.")
        if not settings.SUPABASE_KEY:
            raise ValueError("SUPABASE_KEY is required. Please set it in your .env file.")
        
        _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    return _supabase_client

