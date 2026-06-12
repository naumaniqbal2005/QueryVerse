"""
Supabase CRUD Routes for QueryVerse
Handles user, chat, database, and message persistence
"""

from fastapi import HTTPException, UploadFile, File, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import json
import os
from supabase import Client
from supabase_config import get_supabase_client, get_supabase_admin_client

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
def get_current_user(supabase: Client = Depends(get_supabase_client)):
    """Get current user from Supabase auth (simplified version)"""
    # In production, you'd validate the JWT token from the request
    # For now, this is a placeholder
    return None

# User endpoints
async def create_user(user: UserCreate, supabase: Client = Depends(get_supabase_admin_client)):
    """Create a new user"""
    try:
        # Check if user already exists
        existing = supabase.table('users').select('*').eq('email', user.email).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        # Create user
        result = supabase.table('users').insert({
            'email': user.email,
            'full_name': user.full_name
        }).execute()
        
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

async def get_user(user_id: str, supabase: Client = Depends(get_supabase_client)):
    """Get user by ID"""
    try:
        result = supabase.table('users').select('*').eq('id', user_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user: {str(e)}")

# Chat endpoints
async def create_chat(chat: ChatCreate, user_id: str, supabase: Client = Depends(get_supabase_client)):
    """Create a new chat for a user"""
    try:
        result = supabase.table('chats').insert({
            'user_id': user_id,
            'title': chat.title
        }).execute()
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating chat: {str(e)}")

async def get_chat(chat_id: str, supabase: Client = Depends(get_supabase_client)):
    """Get chat by ID"""
    try:
        result = supabase.table('chats').select('*').eq('id', chat_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Chat not found")
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting chat: {str(e)}")

async def list_user_chats(user_id: str, supabase: Client = Depends(get_supabase_client)):
    """List all chats for a user"""
    try:
        result = supabase.table('chats').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing chats: {str(e)}")

async def update_chat(chat_id: str, title: str, supabase: Client = Depends(get_supabase_client)):
    """Update chat title"""
    try:
        result = supabase.table('chats').update({'title': title}).eq('id', chat_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Chat not found")
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating chat: {str(e)}")

async def delete_chat(chat_id: str, supabase: Client = Depends(get_supabase_client)):
    """Delete a chat (cascade deletes messages and chat_databases)"""
    try:
        result = supabase.table('chats').delete().eq('id', chat_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Chat not found")
        return {"message": "Chat deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting chat: {str(e)}")

# Database endpoints
async def upload_database_file(
    file: UploadFile = File(...),
    user_id: str = None,
    name: str = None,
    supabase_admin: Client = Depends(get_supabase_admin_client)
):
    """Upload database file to Supabase Storage and create database record"""
    try:
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        storage_path = f"{user_id}/{timestamp}_{file.filename}"
        
        # Upload to Supabase Storage
        supabase_admin.storage.from_('database-files').upload(
            path=storage_path,
            file=content,
            file_options={'content-type': 'application/octet-stream'}
        )
        
        # Create database record
        result = supabase_admin.table('databases').insert({
            'user_id': user_id,
            'name': name or file.filename,
            'storage_path': storage_path,
            'file_name': file.filename,
            'file_size': file_size
        }).execute()
        
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading database: {str(e)}")

async def get_database(database_id: str, supabase: Client = Depends(get_supabase_client)):
    """Get database by ID"""
    try:
        result = supabase.table('databases').select('*').eq('id', database_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Database not found")
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting database: {str(e)}")

async def list_user_databases(user_id: str, supabase: Client = Depends(get_supabase_client)):
    """List all databases for a user"""
    try:
        result = supabase.table('databases').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing databases: {str(e)}")

async def download_database_file(database_id: str, supabase_admin: Client = Depends(get_supabase_admin_client)):
    """Download database file from Supabase Storage"""
    try:
        # Get database record
        db_record = await get_database(database_id, supabase_admin)
        
        # Download file from storage
        file_data = supabase_admin.storage.from_('database-files').download(db_record['storage_path'])
        
        return {
            'file_data': file_data,
            'file_name': db_record['file_name'],
            'file_size': db_record['file_size']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading database: {str(e)}")

async def delete_database(database_id: str, supabase_admin: Client = Depends(get_supabase_admin_client)):
    """Delete database record and file from storage"""
    try:
        # Get database record
        db_record = await get_database(database_id, supabase_admin)
        
        # Delete from storage
        supabase_admin.storage.from_('database-files').remove([db_record['storage_path']])
        
        # Delete record
        result = supabase_admin.table('databases').delete().eq('id', database_id).execute()
        
        return {"message": "Database deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting database: {str(e)}")

# Message endpoints
async def create_message(message: MessageCreate, chat_id: str, supabase: Client = Depends(get_supabase_client)):
    """Create a new message in a chat"""
    try:
        result = supabase.table('messages').insert({
            'chat_id': chat_id,
            'role': message.role,
            'content': message.content,
            'tokens_used': json.dumps(message.tokens_used) if message.tokens_used else None
        }).execute()
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating message: {str(e)}")

async def get_chat_messages(chat_id: str, supabase: Client = Depends(get_supabase_client)):
    """Get all messages for a chat"""
    try:
        result = supabase.table('messages').select('*').eq('chat_id', chat_id).order('created_at', asc=True).execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting messages: {str(e)}")

async def delete_message(message_id: str, supabase: Client = Depends(get_supabase_client)):
    """Delete a message"""
    try:
        result = supabase.table('messages').delete().eq('id', message_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Message not found")
        return {"message": "Message deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting message: {str(e)}")

# Chat-Database relationship endpoints
async def link_database_to_chat(chat_id: str, database_id: str, supabase: Client = Depends(get_supabase_client)):
    """Link a database to a chat"""
    try:
        result = supabase.table('chat_databases').insert({
            'chat_id': chat_id,
            'database_id': database_id
        }).execute()
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error linking database to chat: {str(e)}")

async def unlink_database_from_chat(chat_id: str, database_id: str, supabase: Client = Depends(get_supabase_client)):
    """Unlink a database from a chat"""
    try:
        result = supabase.table('chat_databases').delete().eq('chat_id', chat_id).eq('database_id', database_id).execute()
        return {"message": "Database unlinked from chat successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error unlinking database from chat: {str(e)}")

async def get_chat_databases(chat_id: str, supabase: Client = Depends(get_supabase_client)):
    """Get all databases linked to a chat"""
    try:
        result = supabase.table('chat_databases').select('*, databases(*)').eq('chat_id', chat_id).execute()
        # Extract database information
        databases = [item['databases'] for item in result.data if item.get('databases')]
        return databases
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting chat databases: {str(e)}")

# Session loading endpoint
async def load_session(chat_id: str, supabase: Client = Depends(get_supabase_client), supabase_admin: Client = Depends(get_supabase_admin_client)):
    """Load a complete session (chat, messages, and databases)"""
    try:
        # Get chat
        chat = await get_chat(chat_id, supabase)
        
        # Get messages
        messages = await get_chat_messages(chat_id, supabase)
        
        # Get linked databases
        databases = await get_chat_databases(chat_id, supabase)
        
        # Download database files
        database_files = []
        for db in databases:
            file_info = await download_database_file(db['id'], supabase_admin)
            database_files.append({
                'database': db,
                'file_data': file_info['file_data'],
                'file_name': file_info['file_name']
            })
        
        return {
            'chat': chat,
            'messages': messages,
            'databases': database_files
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading session: {str(e)}")
