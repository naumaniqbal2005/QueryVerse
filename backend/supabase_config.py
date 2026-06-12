"""
Supabase Configuration Module
Handles Supabase client initialization and configuration
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SupabaseConfig:
    """Singleton class for Supabase configuration"""
    
    _instance = None
    _client: Client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def client(self) -> Client:
        """Get or create Supabase client instance"""
        if self._client is None:
            self._client = self._create_client()
        return self._client
    
    def _create_client(self) -> Client:
        """Create and configure Supabase client"""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY must be set in environment variables. "
                "Please add them to your .env file."
            )
        
        return create_client(supabase_url, supabase_key)
    
    @property
    def service_role_client(self) -> Client:
        """Get Supabase client with service role key (admin privileges)"""
        supabase_url = os.getenv("SUPABASE_URL")
        service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not service_role_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment variables."
            )
        
        return create_client(supabase_url, service_role_key)

# Global instance
supabase = SupabaseConfig()

def get_supabase_client() -> Client:
    """Convenience function to get the Supabase client"""
    return supabase.client

def get_supabase_admin_client() -> Client:
    """Convenience function to get the Supabase admin client"""
    return supabase.service_role_client
