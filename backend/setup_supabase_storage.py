# """
# Setup script for Supabase Storage bucket
# Creates the 'database-files' bucket for storing database files
# Uses direct HTTP requests to avoid dependency issues
# """

# import os
# import requests
# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()

# def setup_storage_bucket():
#     """Create the database-files storage bucket in Supabase using REST API"""
    
#     supabase_url = os.getenv("SUPABASE_URL")
#     service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
#     if not supabase_url or not service_role_key:
#         print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
#         return False
    
#     # Remove trailing slash from URL if present
#     supabase_url = supabase_url.rstrip('/')
    
#     bucket_name = "database-files"
    
#     try:
#         # Check if bucket already exists
#         headers = {
#             "apikey": service_role_key,
#             "Authorization": f"Bearer {service_role_key}",
#             "Content-Type": "application/json"
#         }
        
#         list_url = f"{supabase_url}/storage/v1/bucket"
#         response = requests.get(list_url, headers=headers)
        
#         if response.status_code == 200:
#             existing_buckets = response.json()
#             bucket_exists = any(bucket.get('name') == bucket_name for bucket in existing_buckets)
            
#             if bucket_exists:
#                 print(f"Bucket '{bucket_name}' already exists. Skipping creation.")
#                 return True
#         else:
#             print(f"Warning: Could not check existing buckets (status {response.status_code})")
        
#         # Create the bucket using REST API
#         create_url = f"{supabase_url}/storage/v1/bucket"
#         bucket_data = {
#             "id": bucket_name,
#             "name": bucket_name,
#             "public": False,
#             "file_size_limit": 52428800,  # 50MB limit (free tier)
#             "allowed_mime_types": "application/x-sqlite3,application/vnd.sqlite3,application/sql,text/x-sql,application/octet-stream"
#         }
        
#         response = requests.post(create_url, json=bucket_data, headers=headers)
        
#         if response.status_code in [200, 201]:
#             print(f"✓ Successfully created storage bucket: {bucket_name}")
#             print(f"  - Public: No")
#             print(f"  - File size limit: 50MB")
#             print(f"  - Allowed types: SQLite, SQL files")
#             return True
#         else:
#             print(f"Error creating bucket: {response.status_code}")
#             print(f"Response: {response.text}")
#             return False
            
#     except Exception as e:
#         print(f"Error creating storage bucket: {e}")
#         return False

# if __name__ == "__main__":
#     print("Setting up Supabase Storage bucket...")
#     success = setup_storage_bucket()
    
#     if success:
#         print("\n✓ Storage setup completed successfully!")
#         print("\nNext steps:")
#         print("1. Run the SQL migration in Supabase SQL Editor:")
#         print("   - Open your Supabase project")
#         print("   - Go to SQL Editor")
#         print("   - Copy and run the contents of supabase_migration.sql")
#     else:
#         print("\n✗ Storage setup failed. Please check your credentials.")
