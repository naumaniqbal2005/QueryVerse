import gradio as gr
import os
import requests
import sqlite3
import json

# Load GROQ API key from environment variable
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Supported model
MODEL_NAME = "llama-3.1-8b-instant"

DATABASE_SCHEMA = """Game Rental DB:Admins(AdminID PK:int,FullName:str,Email:str,AccessLevel:str);Categories(CategoryID PK:int,CategoryName:str);Games(GameID PK:int,GameTitle:str,Platform:str,Genre:str,TotalStock:int,CategoryID FK->Categories.CategoryID:int);GameCopies(CopyID PK:int,GameID FK->Games.GameID:int,CopyCondition:str,Availability:str);Users(UserID PK:int,FullName:str,Email:str,AccountStatus:str);Rentals(RentalID PK:int,UserID FK->Users.UserID:int,CopyID FK->GameCopies.CopyID:int,DateIssued:str,DateDue:str);Penalties(PenaltyID PK:int,UserID FK->Users.UserID:int,RentalID FK->Rentals.RentalID:int,PenaltyAmount:decimal,PenaltyReason:str);Reviews(ReviewID PK:int,UserID FK->Users.UserID:int,GameID FK->Games.GameID:int,Rating:int,ReviewText:str);Transactions(TransactionID PK:int,UserID FK->Users.UserID:int,RentalID FK->Rentals.RentalID:int,AdminID FK->Admins.AdminID:int,Amount:decimal,TransactionDate:str);UnreleasedCatalog(UnreleasedID PK:int,GameTitle:str,ExpectedRelease:str);UserInterests(InterestID PK:int,UserID FK->Users.UserID:int,UnreleasedID FK->UnreleasedCatalog.UnreleasedID:int,RequestTime:str);Waitlist(WaitlistID PK:int,UserID FK->Users.UserID:int,GameID FK->Games.GameID:int,RequestTime:str)"""

SQL_GENERATOR_PROMPT = f"""Convert question to SQLite using schema:{DATABASE_SCHEMA}Return ONLY SQL. Use JOINs for related tables. Dates as TEXT 'YYYY-MM-DD'.Q:"""

RESPONSE_GENERATOR_PROMPT = """Convert SQL results to natural language. Be Friendly but to the point and definitive. For multiple results, list them clearly. Format responses to be user-friendly and easy to read. Ignore repeated values. Don't mention that you got the answer from an SQL query."""

def execute_sql_query(sql_query):
    """Execute SQL query on the database and return results."""
    try:
        conn = sqlite3.connect("mydb.db")
        cursor = conn.cursor()
        cursor.execute(sql_query)
        results = cursor.fetchall()
        
        # Get column names for better formatting
        column_names = [description[0] for description in cursor.description] if cursor.description else []
        
        conn.close()
        return results, column_names, None
    except sqlite3.Error as e:
        return None, None, str(e)

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

def respond(user_message, chat_history, temperature):
    """Handle user questions about the database."""
    if not user_message or not user_message.strip():
        return "", chat_history
    
    chat_history.append({"role": "user", "content": user_message})

    try:
        # Step 1: Generate SQL query
        sql_messages = [
            {"role": "system", "content": SQL_GENERATOR_PROMPT},
            {"role": "user", "content": user_message}
        ]
        
        sql_query, sql_input_tokens, sql_output_tokens = query_groq(sql_messages, 0.1)  # Low temperature for consistent SQL
        
        # Clean SQL query (remove markdown formatting if present)
        sql_query = sql_query.strip()
        if sql_query.startswith("```sql"):
            sql_query = sql_query[6:]
        if sql_query.startswith("```"):
            sql_query = sql_query[3:]
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]
        sql_query = sql_query.strip()
        
        # Step 2: Execute SQL query
        results, column_names, error = execute_sql_query(sql_query)
        
        if error:
            response = f"❌ Database error: {error} SQL Query: {sql_query}"
        elif results is None:
            response = "❌ No results returned from database."
        else:
            # Step 3: Generate natural language response
            results_str = json.dumps({"columns": column_names, "data": results}, indent=2)
            
            response_messages = [
                {"role": "system", "content": RESPONSE_GENERATOR_PROMPT},
                {"role": "user", "content": f"Question: {user_message}\nSQL Query: {sql_query}\nResults: {results_str}"}
            ]
            
            response, resp_input_tokens, resp_output_tokens = query_groq(response_messages, temperature)
            
            # Calculate total tokens used
            total_input = sql_input_tokens + resp_input_tokens
            total_output = sql_output_tokens + resp_output_tokens
            total_tokens = total_input + total_output
            
            # Add technical details for transparency
            if len(response) < 500:  # Only add details for shorter responses
                response += f"\nSQL Query: {sql_query}\nResults: {len(results)} row(s) found\nTokens Used: {total_tokens} (Input: {total_input}, Output: {total_output})"
    
    except Exception as e:
        response = f"❌ Error processing your request: {str(e)}"
    
    chat_history.append({"role": "assistant", "content": response})
    return "", chat_history

# Build the Gradio interface
with gr.Blocks() as demo:
    gr.Markdown("## 🎮 Database Chat Assistant")
    gr.Markdown("Ask questions about the video game rental database in natural language:")
    gr.Markdown("*Examples: 'How many users are active?', 'What games are available for PC?', 'Show me all rentals due this week'*")
    
    if not GROQ_API_KEY:
        gr.Markdown(
            """
            > ⚠️ **Warning**: GROQ_API_KEY environment variable is not set.
            > 
            > To use this chatbot, you need to set your GROQ API key:
            > - **Windows**: `set GROQ_API_KEY=your_api_key_here`
            > - **Linux/Mac**: `export GROQ_API_KEY=your_api_key_here`
            > 
            > Get your API key from [https://console.groq.com](https://console.groq.com)
            """
        )

    # Initialize chatbot (fixed: no 'type' argument)
    chatbot = gr.Chatbot(height=400)

    msg = gr.Textbox(
        placeholder="Ask a question about the database...",
        label="Your Question"
    )

    temperature = gr.Slider(
        0.2, 1.0, 0.7, step=0.1,
        label="Response Creativity"
    )

    clear = gr.Button("Clear Chat")

    msg.submit(respond, [msg, chatbot, temperature], [msg, chatbot])
    clear.click(lambda: [], None, chatbot)

demo.launch()