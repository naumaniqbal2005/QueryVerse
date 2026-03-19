# Database Chat Assistant - Full Stack Application

A modern web application that allows users to ask natural language questions about a video game rental database, with AI-powered SQL generation and response formatting.

## Architecture

- **Backend**: FastAPI (Python)
- **Frontend**: React + Vite (JavaScript)
- **Database**: SQLite
- **AI**: GROQ API for natural language processing

## Features

- 🎮 Natural language to SQL conversion
- 💬 Real-time chat interface
- 📊 Token usage tracking
- 🎨 Modern, responsive UI
- ⚡ Fast API responses
- 🔧 Temperature control for response creativity

## Setup Instructions

### Prerequisites

- Python 3.8+
- Node.js 16+
- GROQ API key

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variable:
```bash
# Windows
set GROQ_API_KEY=your_api_key_here

# Linux/Mac
export GROQ_API_KEY=your_api_key_here
```

4. Start the backend server:
```bash
python main.py
```

Backend will run on `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install Node.js dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

Frontend will run on `http://localhost:3000`

## API Endpoints

### GET `/`
Health check endpoint

### GET `/health`
API health status

### POST `/chat`
Chat with the database assistant

**Request Body:**
```json
{
  "message": "How many users are active?",
  "chat_history": [],
  "temperature": 0.7
}
```

**Response:**
```json
{
  "response": "There are 7 active users in the database...",
  "chat_history": [...],
  "tokens_used": {
    "total": 245,
    "input": 180,
    "output": 65,
    "sql_generation": {"input": 120, "output": 15},
    "response_generation": {"input": 60, "output": 50}
  }
}
```

## Environment Variables

- `GROQ_API_KEY`: Your GROQ API key (required)

## Database

The application uses a SQLite database (`mydb.db`) with the following schema:
- Admins, Categories, Games, GameCopies
- Users, Rentals, Penalties, Reviews
- Transactions, UnreleasedCatalog, UserInterests, Waitlist

## Development

### Backend Development
```bash
cd backend
python main.py
```

### Frontend Development
```bash
cd frontend
npm run dev
```

### Production Build

Frontend:
```bash
npm run build
```

## Features Breakdown

### Token Usage Tracking
- Total tokens per request
- Input/output breakdown
- SQL generation vs response generation
- Real-time display

### Chat Features
- Message history
- Typing indicators
- Clear chat functionality
- Temperature slider for creativity control

### UI/UX
- Responsive design
- Modern styling
- Smooth animations
- Professional color scheme

## Troubleshooting

1. **Backend not starting**: Check GROQ_API_KEY environment variable
2. **Frontend can't connect**: Ensure backend is running on port 8000
3. **Database errors**: Verify `mydb.db` exists in backend directory
4. **API errors**: Check GROQ API key and internet connection

## Technology Stack

- **Backend**: FastAPI, Uvicorn, Pydantic
- **Frontend**: React 18, Vite, Axios
- **Database**: SQLite
- **AI**: GROQ API (Llama 3.1 8B Instant)
- **Styling**: CSS3 with custom properties
- **Build Tools**: Vite, npm
