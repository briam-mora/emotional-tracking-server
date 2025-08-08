# VR Session Data Server

A FastAPI server for uploading and managing VR session data from Unity applications.

## Features

- Upload JSON session data files
- Store data in PostgreSQL (Vercel) or SQLite (local development)
- Simple dashboard for viewing and downloading session records
- RESTful API endpoints for data access

## Local Development

### Option 1: SQLite (Quick Start)
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variable to use SQLite
export USE_SQLITE=1

# Run the server
python main.py
```

### Option 2: PostgreSQL (Recommended)
```bash
# Install PostgreSQL locally or use Docker
# Create database: emotional_tracking

# Install dependencies
pip install -r requirements.txt

# Run the server (will auto-detect PostgreSQL)
python main.py
```

## Vercel Deployment

### 1. Set up Vercel Postgres
1. Go to your Vercel dashboard
2. Create a new Postgres database
3. Copy the connection string

### 2. Deploy to Vercel
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Set environment variables
vercel env add POSTGRES_URL
# Paste your Postgres connection string
```

### 3. Environment Variables
- `POSTGRES_URL`: Your Vercel Postgres connection string
- `VERCEL`: Automatically set by Vercel

## API Endpoints

- `GET /` - Dashboard
- `POST /upload` - Upload JSON session data
- `GET /api/sessions` - Get all sessions (with pagination)
- `GET /api/sessions/{session_id}` - Get specific session
- `GET /api/stats` - Get statistics
- `DELETE /api/clear` - Clear all data

## Data Format

The server expects JSON files with an array of session records:

```json
[
  {
    "session_id": "uuid-string",
    "phase": "intro",
    "area": "intro",
    "timestamp": "2025-07-30T17:01:50.5818500Z",
    "conversation_data": {
      "speaker": "user",
      "text": "Hello"
    },
    "hmd_data": {
      "position": {"x": 1.5, "y": 2.0, "z": 0.5},
      "gaze_vector": {"x": 0.0, "y": 0.0, "z": 1.0},
      "gaze_actor": "object_name",
      "movement_speed": 0.5
    },
    "controller_data": {
      "r_position": {"x": 1.0, "y": 1.5, "z": 0.0},
      "l_position": {"x": -1.0, "y": 1.5, "z": 0.0},
      "r_interacted_actor": "button_1",
      "l_interacted_actor": "button_2",
      "r_movement_speed": 0.3,
      "l_movement_speed": 0.2
    },
    "user_emotion": "happy",
    "emotion_window_flag": true
  }
]
```

## Testing

Run the test script to verify functionality:
```bash
python test_upload.py
```

## Database Migration

The server automatically handles both SQLite and PostgreSQL:
- **Local development**: Falls back to SQLite if PostgreSQL is unavailable
- **Vercel deployment**: Uses PostgreSQL via `POSTGRES_URL` environment variable
- **Manual override**: Set `USE_SQLITE=1` to force SQLite usage
