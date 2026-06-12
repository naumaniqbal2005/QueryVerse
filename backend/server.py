from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import os
import requests
import sqlite3
import json
import uvicorn
from dotenv import load_dotenv
from supabase_routes import (
    create_user, get_user,
    create_chat, get_chat, list_user_chats, update_chat, delete_chat,
    upload_database_file, get_database, list_user_databases, download_database_file, delete_database,
    create_message, get_chat_messages, delete_message,
    link_database_to_chat, unlink_database_from_chat, get_chat_databases,
    load_session
)
from auth_routes import router as auth_router, get_current_user_dependency

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Database Chat API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth router
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

# Security scheme for JWT
security = HTTPBearer()

# Load GROQ API key from environment variable
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL_NAME = "llama-3.1-8b-instant"

# Import simple name matcher
from simple_matcher import SimpleNameMatcher

# Initialize simple matcher
print("Initializing simple name matcher...")
name_matcher = SimpleNameMatcher()
print("Simple name matcher ready!")


# DATABASE_SCHEMA = """Game Rental DB:Admins(AdminID PK:int,FullName:str,Email:str,AccessLevel:str);Categories(CategoryID PK:int,CategoryName:str);Games(GameID PK:int,GameTitle:str,Platform:str,Genre:str,TotalStock:int,CategoryID FK->Categories.CategoryID:int);GameCopies(CopyID PK:int,GameID FK->Games.GameID:int,CopyCondition:str,Availability:str);Users(UserID PK:int,FullName:str,Email:str,AccountStatus:str);Rentals(RentalID PK:int,UserID FK->Users.UserID:int,CopyID FK->GameCopies.CopyID:int,DateIssued:str,DateDue:str);Penalties(PenaltyID PK:int,UserID FK->Users.UserID:int,RentalID FK->Rentals.RentalID:int,PenaltyAmount:decimal,PenaltyReason:str);Reviews(ReviewID PK:int,UserID FK->Users.UserID:int,GameID FK->Games.GameID:int,Rating:int,ReviewText:str);Transactions(TransactionID PK:int,UserID FK->Users.UserID:int,RentalID FK->Rentals.RentalID:int,AdminID FK->Admins.AdminID:int,Amount:decimal,TransactionDate:str);UnreleasedCatalog(UnreleasedID PK:int,GameTitle:str,ExpectedRelease:str);UserInterests(InterestID PK:int,UserID FK->Users.UserID:int,UnreleasedID FK->UnreleasedCatalog.UnreleasedID:int,RequestTime:str);Waitlist(WaitlistID PK:int,UserID FK->Users.UserID:int,GameID FK->Games.GameID:int,RequestTime:str)"""

# SQL_GENERATOR_PROMPT = f"""Convert question to SQLite using schema:{DATABASE_SCHEMA}Return ONLY SQL. Use JOINs for related tables. Dates as TEXT 'YYYY-MM-DD'."""

RESPONSE_GENERATOR_PROMPT = """Convert SQL results to natural language. Be Friendly but to the point and definitive. For multiple results, list them clearly. Format responses to be user-friendly and easy to read. Ignore repeated values. Don't mention that you got the answer from an SQL query. Dont make a heading. A single sentence answer."""

DATABASE_SCHEMA = ""
DB_NAME = "mydb.db"

# Pydantic models
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    chat_history: List[ChatMessage] = []
    temperature: float = 0.7

class ChatResponse(BaseModel):
    response: str
    chat_history: List[ChatMessage]
    tokens_used: Optional[dict] = None

class HealthResponse(BaseModel):
    status: str
    message: str

class SchemaUploadResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status: str
    message: str
    db_schema: str = Field(serialization_alias="schema")
    tables: List[str]

def execute_sql_query(sql_query):
    """Execute SQL query on the database and return results."""
    try:
        # Look for mydb.db in the current directory (backend folder)
        db_path = DB_NAME
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(sql_query)
        results = cursor.fetchall()
        
        column_names = [description[0] for description in cursor.description] if cursor.description else []
        
        conn.close()
        return results, column_names, None
    except sqlite3.Error as e:
        return None, None, str(e)

def parse_sql_schema(sql_content):
    """Parse SQL schema to extract table names and columns."""
    import re
    
    tables = {}
    # Pattern to match CREATE TABLE statements
    create_table_pattern = r'CREATE\s+TABLE\s+(\w+)\s*\((.*?)\);'
    
    matches = re.findall(create_table_pattern, sql_content, re.IGNORECASE | re.DOTALL)
    
    for table_name, columns_block in matches:
        columns = []
        # Split by comma, but ignore commas inside parentheses
        column_defs = re.split(r',(?![^(]*\))', columns_block)
        
        for col_def in column_defs:
            col_def = col_def.strip()
            if col_def:
                # Extract column name (first word before space or parenthesis)
                col_match = re.match(r'(\w+)', col_def)
                if col_match:
                    col_name = col_match.group(1)
                    # Skip constraints like PRIMARY KEY, FOREIGN KEY, etc.
                    if col_name.upper() not in ['PRIMARY', 'FOREIGN', 'UNIQUE', 'CHECK', 'CONSTRAINT']:
                        columns.append(col_name)
        
        tables[table_name] = columns
    
    return tables

def convert_to_groq_schema(tables):
    """Convert parsed tables to Groq schema format."""
    schema_parts = []
    for table_name, columns in tables.items():
        col_str = ','.join(columns)
        schema_parts.append(f"{table_name}({col_str})")
    
    return ';'.join(schema_parts)

def remove_database_file(db_path):
    """Remove an existing SQLite database and its sidecar files."""
    for suffix in ("", "-wal", "-shm", "-journal"):
        path = f"{db_path}{suffix}" if suffix else db_path
        if os.path.exists(path):
            os.remove(path)


def create_database_from_schema(sql_content, db_path):
    """Create SQLite database from SQL schema content."""
    try:
        remove_database_file(db_path)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.executescript(sql_content)
        conn.commit()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)

def query_groq(messages, temperature):
    """Query the GROQ API with proper error handling."""
    if not GROQ_API_KEY:
        return "⚠️ API key not configured. Please set the GROQ_API_KEY environment variable.", 0, 0
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": temperature
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            response_data = response.json()
            content = response_data["choices"][0]["message"]["content"]
            usage = response_data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            return content, input_tokens, output_tokens
        elif response.status_code == 401:
            return "🔑 Authentication failed. Please check your GROQ_API_KEY.", 0, 0
        elif response.status_code == 429:
            return "⏳ Rate limit exceeded. Please wait a moment and try again.", 0, 0
        elif response.status_code >= 500:
            return "🔧 Server error. The GROQ service might be temporarily unavailable.", 0, 0
        else:
            return f"❌ API Error ({response.status_code}): {response.text[:200]}", 0, 0
    
    except requests.exceptions.Timeout:
        return "⏱️ Request timed out. Please try again.", 0, 0
    except requests.exceptions.ConnectionError:
        return "🌐 Connection error. Please check your internet connection.", 0, 0
    except Exception as e:
        return f"❌ Unexpected error: {str(e)[:200]}", 0, 0

@app.get("/")
async def root():
    return {"message": "Database Chat API is running"}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy", message="API is ready to handle requests")

@app.post("/upload-schema", response_model=SchemaUploadResponse)
async def upload_schema(file: UploadFile = File(...)):
    """Upload SQL schema file to create database and extract schema for Groq."""
    global DATABASE_SCHEMA
    
    try:
        # Read the uploaded file
        content = await file.read()
        sql_content = content.decode('utf-8')
        
        # Parse the SQL schema to extract tables and columns
        tables = parse_sql_schema(sql_content)
        
        if not tables:
            raise HTTPException(status_code=400, detail="No tables found in the SQL schema")
        
        # Convert to Groq schema format
        groq_schema = convert_to_groq_schema(tables)
        
        # Update the global DATABASE_SCHEMA
        DATABASE_SCHEMA = groq_schema
        
        # Create the database from the schema
        success, error = create_database_from_schema(sql_content, DB_NAME)
        
        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to create database: {error}")
        
        return SchemaUploadResponse(
            status="success",
            message=f"Database created successfully with {len(tables)} tables",
            db_schema=groq_schema,
            tables=list(tables.keys())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing schema: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Handle chat requests with database queries - requires authentication"""
    # Verify JWT token
    token = credentials.credentials
    try:
        from auth_utils import decode_access_token
        payload = decode_access_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Authentication failed")
    
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Check if schema has been uploaded
    if not DATABASE_SCHEMA:
        raise HTTPException(status_code=400, detail="No database schema loaded. Please upload a SQL schema file first using /upload-schema endpoint.")
    
    # Enhance query with simple name matching
    original_message = request.message
    enhanced_message = name_matcher.enhance_query(original_message)
    
    chat_history = request.chat_history.copy()
    chat_history.append({"role": "user", "content": enhanced_message})

    try:
        # Step 1: Generate SQL query
        sql_generator_prompt = f"""Convert question to SQLite using schema:{DATABASE_SCHEMA}Return ONLY SQL. Use JOINs for related tables. Dates as TEXT 'YYYY-MM-DD'."""
        sql_messages = [
            {"role": "system", "content": sql_generator_prompt},
            {"role": "user", "content": enhanced_message}
        ]
        
        sql_query, sql_input_tokens, sql_output_tokens = query_groq(sql_messages, 0.1)  # Low temperature for consistent SQL
        
        # Clean SQL query (remove markdown formatting and explanatory text)
        sql_query = sql_query.strip()
        if sql_query.startswith("```sql"):
            sql_query = sql_query[6:]
        if sql_query.startswith("```"):
            sql_query = sql_query[3:]
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]
        
        # Remove any explanatory text after SQL statement
        if ';' in sql_query:
            sql_query = sql_query.split(';')[0] + ';'
        else:
            # If no semicolon, take only the first line that looks like SQL
            lines = sql_query.split('\n')
            for line in lines:
                line = line.strip()
                if line and (line.upper().startswith(('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WITH'))):
                    sql_query = line
                    break
        
        sql_query = sql_query.strip()
        
        # Print SQL query for debugging
        print(f"Generated SQL Query: {sql_query}")
        print(f"Query length: {len(sql_query)}")
        print(f"Contains semicolon: {';' in sql_query}")
        
        # Step 2: Execute SQL query
        results, column_names, error = execute_sql_query(sql_query)
        
        if error:
            response = f"Database error: {error}"
            tokens_used = None
        elif results is None:
            response = "❌ No results returned from database."
            tokens_used = None
        else:
            # Step 3: Generate natural language response
            results_str = json.dumps({"columns": column_names, "data": results}, indent=2)
            
            response_messages = [
                {"role": "system", "content": RESPONSE_GENERATOR_PROMPT},
                {"role": "user", "content": f"Question: {enhanced_message}\nSQL Query: {sql_query}\nResults: {results_str}"}
            ]
            
            response, resp_input_tokens, resp_output_tokens = query_groq(response_messages, request.temperature)
            
            # Calculate total tokens used
            total_input = sql_input_tokens + resp_input_tokens
            total_output = sql_output_tokens + resp_output_tokens
            total_tokens = total_input + total_output
            
            tokens_used = {
                "total": total_tokens,
                "input": total_input,
                "output": total_output,
                "sql_generation": {"input": sql_input_tokens, "output": sql_output_tokens},
                "response_generation": {"input": resp_input_tokens, "output": resp_output_tokens}
            }
            
            # # Add technical details for transparency
            # if len(response) < 500:  # Only add details for shorter responses
            #     response += f"\n\n**Technical Details:**\n- SQL Query: `{sql_query}`\n- Results: {len(results)} row(s) found\n- Tokens Used: {total_tokens} (Input: {total_input}, Output: {total_output})"
    
    except Exception as e:
        response = f"❌ Error processing your request: {str(e)}"
        tokens_used = None
    
    chat_history.append({"role": "assistant", "content": response})
    
    return ChatResponse(
        response=response,
        chat_history=chat_history,
        tokens_used=tokens_used
    )

# ============ Supabase CRUD Endpoints ============

# User endpoints
@app.post("/supabase/users")
async def api_create_user(user: dict):
    """Create a new user"""
    return await create_user(user)

@app.get("/supabase/users/{user_id}")
async def api_get_user(user_id: str):
    """Get user by ID"""
    return await get_user(user_id)

# Chat endpoints
@app.post("/supabase/chats")
async def api_create_chat(chat: dict, user_id: str):
    """Create a new chat for a user"""
    return await create_chat(chat, user_id)

@app.get("/supabase/chats/{chat_id}")
async def api_get_chat(chat_id: str):
    """Get chat by ID"""
    return await get_chat(chat_id)

@app.get("/supabase/users/{user_id}/chats")
async def api_list_user_chats(user_id: str):
    """List all chats for a user"""
    return await list_user_chats(user_id)

@app.put("/supabase/chats/{chat_id}")
async def api_update_chat(chat_id: str, title: str):
    """Update chat title"""
    return await update_chat(chat_id, title)

@app.delete("/supabase/chats/{chat_id}")
async def api_delete_chat(chat_id: str):
    """Delete a chat"""
    return await delete_chat(chat_id)

# Database endpoints
@app.post("/supabase/databases/upload")
async def api_upload_database(
    file: UploadFile = File(...),
    user_id: str = None,
    name: str = None
):
    """Upload database file to Supabase Storage"""
    return await upload_database_file(file, user_id, name)

@app.get("/supabase/databases/{database_id}")
async def api_get_database(database_id: str):
    """Get database by ID"""
    return await get_database(database_id)

@app.get("/supabase/users/{user_id}/databases")
async def api_list_user_databases(user_id: str):
    """List all databases for a user"""
    return await list_user_databases(user_id)

@app.get("/supabase/databases/{database_id}/download")
async def api_download_database(database_id: str):
    """Download database file from Supabase Storage"""
    return await download_database_file(database_id)

@app.delete("/supabase/databases/{database_id}")
async def api_delete_database(database_id: str):
    """Delete a database"""
    return await delete_database(database_id)

# Message endpoints
@app.post("/supabase/messages")
async def api_create_message(message: dict, chat_id: str):
    """Create a new message in a chat"""
    return await create_message(message, chat_id)

@app.get("/supabase/chats/{chat_id}/messages")
async def api_get_chat_messages(chat_id: str):
    """Get all messages for a chat"""
    return await get_chat_messages(chat_id)

@app.delete("/supabase/messages/{message_id}")
async def api_delete_message(message_id: str):
    """Delete a message"""
    return await delete_message(message_id)

# Chat-Database relationship endpoints
@app.post("/supabase/chats/{chat_id}/databases/{database_id}")
async def api_link_database_to_chat(chat_id: str, database_id: str):
    """Link a database to a chat"""
    return await link_database_to_chat(chat_id, database_id)

@app.delete("/supabase/chats/{chat_id}/databases/{database_id}")
async def api_unlink_database_from_chat(chat_id: str, database_id: str):
    """Unlink a database from a chat"""
    return await unlink_database_from_chat(chat_id, database_id)

@app.get("/supabase/chats/{chat_id}/databases")
async def api_get_chat_databases(chat_id: str):
    """Get all databases linked to a chat"""
    return await get_chat_databases(chat_id)

# Session loading endpoint
@app.get("/supabase/sessions/{chat_id}")
async def api_load_session(chat_id: str):
    """Load a complete session (chat, messages, and databases)"""
    return await load_session(chat_id)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
