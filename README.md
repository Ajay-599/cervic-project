# Chatbot Backend (Flask)

A simple Flask-based chatbot API server.

## Setup

```bash
# 1. Create a virtual environment (recommended)
python -m venv venv

# 2. Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

## Run the Server

```bash
python app.py
```

The server starts at **http://localhost:5000**.

## API Usage

### `POST /chat`

Send a message and get a bot response.

```bash
curl -X POST http://localhost:5000/chat -H "Content-Type: application/json" -d "{\"message\": \"hello\"}"
```

**Response:**
```json
{
  "response": "Hey there! 👋 How can I help you today?"
}
```

### `GET /`

Health check — confirms the API is running.
