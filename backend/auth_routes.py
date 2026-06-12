"""
Authentication routes for user registration and login
Uses direct HTTP requests to avoid Supabase client dependency issues
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
from auth_utils import verify_password, get_password_hash, create_access_token, decode_access_token
import requests
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Use service role key for admin operations

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")

# Pydantic models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str]


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


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserRegister):
    """Register a new user"""
    # Check if user already exists
    try:
        response = supabase_request("GET", "users", filters={"email": user_data.email})
        if response.status_code == 200 and response.json():
            raise HTTPException(status_code=400, detail="User with this email already exists")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking existing user: {str(e)}")
    
    # Hash the password
    password_hash = get_password_hash(user_data.password)
    
    # Create user in Supabase
    try:
        user_data_dict = {
            'email': user_data.email,
            'password_hash': password_hash
        }
        if user_data.full_name:
            user_data_dict['full_name'] = user_data.full_name
        
        response = supabase_request("POST", "users", data=user_data_dict)
        
        if response.status_code not in [200, 201]:
            raise HTTPException(status_code=500, detail=f"Error creating user: {response.text}")
        
        new_user = response.json()[0]
        
        return UserResponse(
            id=new_user['id'],
            email=new_user['email'],
            full_name=new_user.get('full_name')
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    """Login user and return JWT token"""
    # Find user by email
    try:
        response = supabase_request("GET", "users", filters={"email": user_data.email})
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Error fetching user")
        
        users = response.json()
        if not users:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        user = users[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user: {str(e)}")
    
    # Verify password
    if not verify_password(user_data.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create access token
    access_token = create_access_token(data={"sub": user['id'], "email": user['email']})
    
    return TokenResponse(
        access_token=access_token,
        user={
            "id": user['id'],
            "email": user['email'],
            "full_name": user.get('full_name')
        }
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(token: str):
    """Get current user from JWT token"""
    # Decode token
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    # Fetch user from Supabase
    try:
        response = supabase_request("GET", "users", filters={"id": user_id})
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Error fetching user")
        
        users = response.json()
        if not users:
            raise HTTPException(status_code=404, detail="User not found")
        
        user = users[0]
        return UserResponse(
            id=user['id'],
            email=user['email'],
            full_name=user.get('full_name')
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user: {str(e)}")


# Dependency for protected routes
async def get_current_user_dependency(token: str) -> dict:
    """Dependency to get current user for protected routes"""
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    try:
        response = supabase_request("GET", "users", filters={"id": user_id})
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Error fetching user")
        
        users = response.json()
        if not users:
            raise HTTPException(status_code=404, detail="User not found")
        
        return users[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user: {str(e)}")
