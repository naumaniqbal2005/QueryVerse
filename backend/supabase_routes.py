"""
Supabase CRUD Routes for QueryVerse
Handles user, chat, database, and message persistence
Uses direct HTTP requests to avoid Supabase client dependency issues
"""

from fastapi import HTTPException, UploadFile, File, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Use service role key for admin operations

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")

# Pydantic models
class UserCreate(BaseModel):
    email: str
    full_name: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    created_at: str
    updated_at: str

class ChatCreate(BaseModel):
    title: str = "New Chat"

class ChatResponse(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: str
    updated_at: str

class DatabaseCreate(BaseModel):
    name: str
    storage_path: str
    file_name: str
    file_size: Optional[int] = None
    schema_info: Optional[str] = None

class DatabaseResponse(BaseModel):
    id: str
    user_id: str
    name: str
    storage_path: str
    file_name: str
    file_size: Optional[int]
    schema_info: Optional[str]
    created_at: str
    updated_at: str


def supabase_request(method: str, table: str, data: dict = None, filters: dict = None):
    """Helper function to make Supabase REST API requests"""
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    if method == "GET":
        params = {}
        if filters:
            for key, value in filters.items():
                params[key] = f"eq.{value}"
        response = requests.get(url, headers=headers, params=params)
    elif method == "POST":
        response = requests.post(url, json=data, headers=headers)
    elif method == "PUT":
        response = requests.put(url, json=data, headers=headers)
    elif method == "DELETE":
        response = requests.delete(url, headers=headers)
    else:
        raise ValueError(f"Unsupported method: {method}")
    
    return response


class MessageCreate(BaseModel):
    role: str = Field(..., pattern="^[ua]$")  # 'u' for user, 'a' for agent
    content: str
    tokens_used: Optional[dict] = None

class MessageResponse(BaseModel):
    id: str
    chat_id: str
    role: str
    content: str
    tokens_used: Optional[dict]
    created_at: str

class ChatWithMessages(BaseModel):
    chat: ChatResponse
    messages: List[MessageResponse]
    databases: List[DatabaseResponse]

# Helper function to get user from auth token (simplified)
def get_current_user():
    """Get current user from Supabase auth (simplified version)"""
    # In production, you'd validate the JWT token from the request
    # For now, this is a placeholder
    return None

# User endpoints
async def create_user(user: UserCreate):
    """Create a new user"""
    try:
        # Check if user already exists
        response = supabase_request("GET", "users", filters={"email": user.email})
        if response.status_code == 200 and response.json():
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        # Create user
        response = supabase_request("POST", "users", data={
            'email': user.email,
            'full_name': user.full_name
        })
        
        if response.status_code not in [200, 201]:
            raise HTTPException(status_code=500, detail=f"Error creating user: {response.text}")
        
        return response.json()[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

async def get_user(user_id: str):
    """Get user by ID"""
    try:
        response = supabase_request("GET", "users", filters={"id": user_id})
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Error getting user")
        
        users = response.json()
        if not users:
            raise HTTPException(status_code=404, detail="User not found")
        return users[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user: {str(e)}")

# Chat endpoints
async def create_chat(chat: ChatCreate, user_id: str):
    """Create a new chat for a user"""
    try:
        response = supabase_request("POST", "chats", data={
            'user_id': user_id,
            'title': chat.title
        })
        
        if response.status_code not in [200, 201]:
            raise HTTPException(status_code=500, detail=f"Error creating chat: {response.text}")
        
        return response.json()[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating chat: {str(e)}")

async def get_chat(chat_id: str):
    """Get chat by ID"""
    try:
        response = supabase_request("GET", "chats", filters={"id": chat_id})
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Error getting chat")
        
        chats = response.json()
        if not chats:
            raise HTTPException(status_code=404, detail="Chat not found")
        return chats[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting chat: {str(e)}")

async def list_user_chats(user_id: str):
    """List all chats for a user"""
    try:
        response = supabase_request("GET", "chats", filters={"user_id": user_id})
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Error listing chats")
        
        chats = response.json()
        # Sort by created_at descending
        chats.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return chats
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing chats: {str(e)}")

async def update_chat(chat_id: str, title: str):
    """Update chat title"""
    try:
        response = supabase_request("PUT", "chats", data={'title': title}, filters={"id": chat_id})
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Error updating chat")
        
        chats = response.json()
        if not chats:
            raise HTTPException(status_code=404, detail="Chat not found")
        return chats[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating chat: {str(e)}")

async def delete_chat(chat_id: str):
    """Delete a chat (cascade deletes messages and chat_databases)"""
    try:
        response = supabase_request("DELETE", "chats", filters={"id": chat_id})
        if response.status_code != 200 and response.status_code != 204:
            raise HTTPException(status_code=500, detail="Error deleting chat")
        return {"message": "Chat deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting chat: {str(e)}")

# Database endpoints
async def upload_database_file(
    file: UploadFile = File(...),
    user_id: str = None,
    name: str = None
):
    """Upload database file to Supabase Storage and create database record"""
    try:
        # Read file content
        if hasattr(file, 'read'):
            content = file.read()
        else:
            content = await file.read()
        file_size = len(content)
        
        # Get filename from file object or use default
        filename = getattr(file, 'filename', name or 'schema.sql')
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        storage_path = f"{user_id}/{timestamp}_{filename}"
        
        # Upload to Supabase Storage using direct HTTP request
        storage_url = f"{SUPABASE_URL}/storage/v1/object/database-files/{storage_path}"
        storage_headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/octet-stream"
        }
        
        storage_response = requests.put(storage_url, data=content, headers=storage_headers)
        if storage_response.status_code not in [200, 201]:
            raise HTTPException(status_code=500, detail=f"Failed to upload to storage: {storage_response.text}")
        
        # Create database record
        response = supabase_request("POST", "databases", data={
            'user_id': user_id,
            'name': name or filename,
            'storage_path': storage_path,
            'file_name': filename,
            'file_size': file_size
        })
        
        if response.status_code not in [200, 201]:
            raise HTTPException(status_code=500, detail=f"Error creating database record: {response.text}")
        
        return response.json()[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading database: {str(e)}")

async def get_database(database_id: str):
    """Get database by ID"""
    try:
        response = supabase_request("GET", "databases", filters={"id": database_id})
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Error getting database")
        
        databases = response.json()
        if not databases:
            raise HTTPException(status_code=404, detail="Database not found")
        return databases[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting database: {str(e)}")

async def list_user_databases(user_id: str):
    """List all databases for a user"""
    try:
        response = supabase_request("GET", "databases", filters={"user_id": user_id})
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Error listing databases")
        
        databases = response.json()
        # Sort by created_at descending
        databases.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return databases
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing databases: {str(e)}")

async def download_database_file(database_id: str):
    """Download database file from Supabase Storage"""
    try:
        # Get database record
        db_record = await get_database(database_id)
        
        # Download from storage using direct HTTP request
        storage_path = db_record['storage_path']
        storage_url = f"{SUPABASE_URL}/storage/v1/object/database-files/{storage_path}"
        storage_headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }
        
        storage_response = requests.get(storage_url, headers=storage_headers)
        if storage_response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Failed to download from storage: {storage_response.text}")
        
        return {
            'fileData': storage_response.content,
            'fileName': db_record['file_name'],
            'name': db_record['name']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading database: {str(e)}")

async def delete_database(database_id: str):
    """Delete database record and file from storage"""
    try:
        # Get database record
        db_record = await get_database(database_id)
        
        # Delete from storage using direct HTTP request
        storage_path = db_record['storage_path']
        storage_url = f"{SUPABASE_URL}/storage/v1/object/database-files/{storage_path}"
        storage_headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }
        
        storage_response = requests.delete(storage_url, headers=storage_headers)
        if storage_response.status_code not in [200, 204]:
            raise HTTPException(status_code=500, detail=f"Failed to delete from storage: {storage_response.text}")
        
        # Delete record
        response = supabase_request("DELETE", "databases", filters={"id": database_id})
        if response.status_code not in [200, 204]:
            raise HTTPException(status_code=500, detail="Error deleting database record")
        
        return {"message": "Database deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting database: {str(e)}")

# Message endpoints
async def create_message(message: MessageCreate, chat_id: str):
    """Create a new message in a chat"""
    try:
        response = supabase_request("POST", "messages", data={
            'chat_id': chat_id,
            'role': message.role,
            'content': message.content,
            'tokens_used': json.dumps(message.tokens_used) if message.tokens_used else None
        })
        
        if response.status_code not in [200, 201]:
            raise HTTPException(status_code=500, detail=f"Error creating message: {response.text}")
        
        return response.json()[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating message: {str(e)}")

async def get_chat_messages(chat_id: str):
    """Get all messages for a chat"""
    try:
        response = supabase_request("GET", "messages", filters={"chat_id": chat_id})
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Error getting messages")
        
        messages = response.json()
        # Sort by created_at ascending
        messages.sort(key=lambda x: x.get('created_at', ''))
        return messages
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting messages: {str(e)}")

async def delete_message(message_id: str):
    """Delete a message"""
    try:
        response = supabase_request("DELETE", "messages", filters={"id": message_id})
        if response.status_code not in [200, 204]:
            raise HTTPException(status_code=500, detail="Error deleting message")
        return {"message": "Message deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting message: {str(e)}")

# Chat-Database relationship endpoints
async def link_database_to_chat(chat_id: str, database_id: str):
    """Link a database to a chat"""
    try:
        response = supabase_request("POST", "chat_databases", data={
            'chat_id': chat_id,
            'database_id': database_id
        })
        
        if response.status_code not in [200, 201]:
            raise HTTPException(status_code=500, detail=f"Error linking database to chat: {response.text}")
        
        return response.json()[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error linking database to chat: {str(e)}")

async def unlink_database_from_chat(chat_id: str, database_id: str):
    """Unlink a database from a chat"""
    try:
        # Need to delete by both chat_id and database_id
        response = requests.delete(
            f"{SUPABASE_URL}/rest/v1/chat_databases",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json"
            },
            params={
                "chat_id": f"eq.{chat_id}",
                "database_id": f"eq.{database_id}"
            }
        )
        
        if response.status_code not in [200, 204]:
            raise HTTPException(status_code=500, detail=f"Error unlinking database from chat: {response.text}")
        
        return {"message": "Database unlinked from chat successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error unlinking database from chat: {str(e)}")

async def get_chat_databases(chat_id: str):
    """Get all databases linked to a chat"""
    try:
        # First get the chat-database relationships
        response = supabase_request("GET", "chat_databases", filters={"chat_id": chat_id})
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Error getting chat databases")
        
        chat_dbs = response.json()
        
        # Then get the full database info for each
        databases = []
        for chat_db in chat_dbs:
            db = await get_database(chat_db['database_id'])
            databases.append(db)
        
        return databases
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting chat databases: {str(e)}")

# Session loading endpoint
async def load_session(chat_id: str):
    """Load a complete session (chat, messages, and databases)"""
    try:
        # Get chat
        chat = await get_chat(chat_id)
        
        # Get messages
        messages = await get_chat_messages(chat_id)
        
        # Get linked databases
        databases = await get_chat_databases(chat_id)
        
        # Download database files
        database_files = []
        for db in databases:
            file_info = await download_database_file(db['id'])
            database_files.append({
                'database': db,
                'fileData': file_info['fileData'],
                'fileName': file_info['fileName']
            })
        
        return {
            'chat': chat,
            'messages': messages,
            'databases': database_files
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading session: {str(e)}")
