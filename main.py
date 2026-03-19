import gradio as gr
import os
import requests

# Load GROQ API key from environment variable
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Supported model
MODEL_NAME = "llama-3.1-8b-instant"

SYSTEM_PROMPT = """
You are CodeMentor, a friendly programming tutor.
Explain programming concepts clearly with simple examples.
Help beginners understand Python, C++, and algorithms.
"""

def query_groq(messages, temperature):
    """Query the GROQ API with proper error handling."""
    if not GROQ_API_KEY:
        return "⚠️ API key not configured. Please set the GROQ_API_KEY environment variable."
    
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
            return response.json()["choices"][0]["message"]["content"]
        elif response.status_code == 401:
            return "🔑 Authentication failed. Please check your GROQ_API_KEY."
        elif response.status_code == 429:
            return "⏳ Rate limit exceeded. Please wait a moment and try again."
        elif response.status_code >= 500:
            return "🔧 Server error. The GROQ service might be temporarily unavailable."
        else:
            return f"❌ API Error ({response.status_code}): {response.text[:200]}"
    
    except requests.exceptions.Timeout:
        return "⏱️ Request timed out. Please try again."
    except requests.exceptions.ConnectionError:
        return "🌐 Connection error. Please check your internet connection."
    except Exception as e:
        return f"❌ Unexpected error: {str(e)[:200]}"

def respond(user_message, chat_history, temperature):
    """Handle user messages and update chat history."""
    if not user_message or not user_message.strip():
        return "", chat_history
    
    chat_history.append({"role": "user", "content": user_message})

    # Clean chat history to remove unsupported fields
    clean_history = [{"role": msg["role"], "content": msg["content"]} for msg in chat_history]
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + clean_history

    bot_reply = query_groq(messages, temperature)
    chat_history.append({"role": "assistant", "content": bot_reply})

    return "", chat_history

# Build the Gradio interface
with gr.Blocks() as demo:
    gr.Markdown("## 🤖 CodeMentor – Programming Tutor")
    
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
        placeholder="Ask a programming question...",
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