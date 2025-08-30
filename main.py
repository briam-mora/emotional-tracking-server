from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os
from datetime import datetime
from typing import List, Optional
import uvicorn

app = FastAPI(title="VR Session Data Server", version="1.0.0")

# Database configuration
def get_db_connection():
    """Get database connection based on environment"""
    if os.getenv('VERCEL'):
        # Vercel Postgres
        POSTGRES_URL = os.getenv('POSTGRES_URL')
        if not POSTGRES_URL:
            raise Exception("POSTGRES_URL environment variable not set")
        try:
            conn = psycopg2.connect(POSTGRES_URL)
            # Test the connection
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            cursor.fetchone()
            cursor.close()
            return conn
        except Exception as e:
            raise Exception(f"Failed to connect to Vercel Postgres: {type(e).__name__}: {str(e)}")
    elif os.getenv('USE_SQLITE'):
        # Local SQLite for quick testing
        import sqlite3
        return sqlite3.connect("session_data.db")
    else:
        # Local PostgreSQL (default for development)
        try:
            return psycopg2.connect(
                host="localhost",
                database="emotional_tracking",
                user="postgres",
                password="password"
            )
        except psycopg2.OperationalError:
            # Fallback to SQLite if PostgreSQL is not available
            print("PostgreSQL not available, falling back to SQLite")
            import sqlite3
            return sqlite3.connect("session_data.db")

def init_db():
    """Initialize the database with required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if we're using SQLite or PostgreSQL
    is_sqlite = hasattr(conn, 'execute') and 'sqlite' in str(type(conn)).lower()
    
    if is_sqlite:
        # SQLite syntax
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                phase TEXT,
                area TEXT,
                timestamp TEXT,
                speaker TEXT,
                text TEXT,
                hmd_position_x REAL,
                hmd_position_y REAL,
                hmd_position_z REAL,
                hmd_gaze_x REAL,
                hmd_gaze_y REAL,
                hmd_gaze_z REAL,
                hmd_gaze_actor TEXT,
                hmd_movement_speed REAL,
                controller_r_x REAL,
                controller_r_y REAL,
                controller_r_z REAL,
                controller_l_x REAL,
                controller_l_y REAL,
                controller_l_z REAL,
                controller_r_actor TEXT,
                controller_l_actor TEXT,
                controller_r_speed REAL,
                controller_l_speed REAL,
                user_emotion TEXT,
                emotion_window_flag BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    else:
        # PostgreSQL syntax
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_records (
                id SERIAL PRIMARY KEY,
                session_id TEXT NOT NULL,
                phase TEXT,
                area TEXT,
                timestamp TEXT,
                speaker TEXT,
                text TEXT,
                hmd_position_x REAL,
                hmd_position_y REAL,
                hmd_position_z REAL,
                hmd_gaze_x REAL,
                hmd_gaze_y REAL,
                hmd_gaze_z REAL,
                hmd_gaze_actor TEXT,
                hmd_movement_speed REAL,
                controller_r_x REAL,
                controller_r_y REAL,
                controller_r_z REAL,
                controller_l_x REAL,
                controller_l_y REAL,
                controller_l_z REAL,
                controller_r_actor TEXT,
                controller_l_actor TEXT,
                controller_r_speed REAL,
                controller_l_speed REAL,
                user_emotion TEXT,
                emotion_window_flag BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.post("/upload")
async def upload_session_data(file: UploadFile = File(...)):
    """Upload session data JSON file"""
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files are allowed")
    
    try:
        content = await file.read()
        data = json.loads(content.decode('utf-8'))
        
        if not isinstance(data, list):
            raise HTTPException(status_code=400, detail="JSON must be an array of session records")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if we're using SQLite or PostgreSQL
        is_sqlite = hasattr(conn, 'execute') and 'sqlite' in str(type(conn)).lower()
        
        records_added = 0
        for record in data:
            if is_sqlite:
                # SQLite uses ? placeholders
                cursor.execute('''
                    INSERT INTO session_records (
                        session_id, phase, area, timestamp, speaker, text,
                        hmd_position_x, hmd_position_y, hmd_position_z,
                        hmd_gaze_x, hmd_gaze_y, hmd_gaze_z, hmd_gaze_actor, hmd_movement_speed,
                        controller_r_x, controller_r_y, controller_r_z,
                        controller_l_x, controller_l_y, controller_l_z,
                        controller_r_actor, controller_l_actor,
                        controller_r_speed, controller_l_speed,
                        user_emotion, emotion_window_flag
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    record.get('session_id'),
                    record.get('phase'),
                    record.get('area'),
                    record.get('timestamp'),
                    record.get('conversation_data', {}).get('speaker'),
                    record.get('conversation_data', {}).get('text'),
                    record.get('hmd_data', {}).get('position', {}).get('x'),
                    record.get('hmd_data', {}).get('position', {}).get('y'),
                    record.get('hmd_data', {}).get('position', {}).get('z'),
                    record.get('hmd_data', {}).get('gaze_vector', {}).get('x'),
                    record.get('hmd_data', {}).get('gaze_vector', {}).get('y'),
                    record.get('hmd_data', {}).get('gaze_vector', {}).get('z'),
                    record.get('hmd_data', {}).get('gaze_actor'),
                    record.get('hmd_data', {}).get('movement_speed'),
                    record.get('controller_data', {}).get('r_position', {}).get('x'),
                    record.get('controller_data', {}).get('r_position', {}).get('y'),
                    record.get('controller_data', {}).get('r_position', {}).get('z'),
                    record.get('controller_data', {}).get('l_position', {}).get('x'),
                    record.get('controller_data', {}).get('l_position', {}).get('y'),
                    record.get('controller_data', {}).get('l_position', {}).get('z'),
                    record.get('controller_data', {}).get('r_interacted_actor'),
                    record.get('controller_data', {}).get('l_interacted_actor'),
                    record.get('controller_data', {}).get('r_movement_speed'),
                    record.get('controller_data', {}).get('l_movement_speed'),
                    record.get('user_emotion'),
                    record.get('emotion_window_flag')
                ))
            else:
                # PostgreSQL uses %s placeholders
                cursor.execute('''
                    INSERT INTO session_records (
                        session_id, phase, area, timestamp, speaker, text,
                        hmd_position_x, hmd_position_y, hmd_position_z,
                        hmd_gaze_x, hmd_gaze_y, hmd_gaze_z, hmd_gaze_actor, hmd_movement_speed,
                        controller_r_x, controller_r_y, controller_r_z,
                        controller_l_x, controller_l_y, controller_l_z,
                        controller_r_actor, controller_l_actor,
                        controller_r_speed, controller_l_speed,
                        user_emotion, emotion_window_flag
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    record.get('session_id'),
                    record.get('phase'),
                    record.get('area'),
                    record.get('timestamp'),
                    record.get('conversation_data', {}).get('speaker'),
                    record.get('conversation_data', {}).get('text'),
                    record.get('hmd_data', {}).get('position', {}).get('x'),
                    record.get('hmd_data', {}).get('position', {}).get('y'),
                    record.get('hmd_data', {}).get('position', {}).get('z'),
                    record.get('hmd_data', {}).get('gaze_vector', {}).get('x'),
                    record.get('hmd_data', {}).get('gaze_vector', {}).get('y'),
                    record.get('hmd_data', {}).get('gaze_vector', {}).get('z'),
                    record.get('hmd_data', {}).get('gaze_actor'),
                    record.get('hmd_data', {}).get('movement_speed'),
                    record.get('controller_data', {}).get('r_position', {}).get('x'),
                    record.get('controller_data', {}).get('r_position', {}).get('y'),
                    record.get('controller_data', {}).get('r_position', {}).get('z'),
                    record.get('controller_data', {}).get('l_position', {}).get('x'),
                    record.get('controller_data', {}).get('l_position', {}).get('y'),
                    record.get('controller_data', {}).get('l_position', {}).get('z'),
                    record.get('controller_data', {}).get('r_interacted_actor'),
                    record.get('controller_data', {}).get('l_interacted_actor'),
                    record.get('controller_data', {}).get('r_movement_speed'),
                    record.get('controller_data', {}).get('l_movement_speed'),
                    record.get('user_emotion'),
                    record.get('emotion_window_flag')
                ))
            records_added += 1
        
        conn.commit()
        conn.close()
        
        # Get updated session count
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(DISTINCT session_id) FROM session_records')
        total_sessions = cursor.fetchone()[0]
        conn.close()
        
        return {
            "message": f"Successfully uploaded {records_added} records", 
            "records_added": records_added,
            "total_sessions": total_sessions
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/api/sessions")
async def get_sessions(limit: int = 100, offset: int = 0):
    """Get list of all sessions with summary information"""
    try:
        conn = get_db_connection()
        
        # Check if we're using SQLite or PostgreSQL
        is_sqlite = hasattr(conn, 'execute') and 'sqlite' in str(type(conn)).lower()
        
        if is_sqlite:
            cursor = conn.cursor()
            # Get session summaries with count, timestamps, and emotion variety
            cursor.execute('''
                SELECT 
                    session_id,
                    COUNT(*) as records,
                    MIN(created_at) as created
                FROM session_records 
                GROUP BY session_id
                ORDER BY created DESC 
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            sessions = []
            for row in rows:
                session_dict = dict(zip(columns, row))
                # Format timestamp to ISO format
                if session_dict.get('created'):
                    try:
                        if isinstance(session_dict['created'], str):
                            session_dict['created'] = session_dict['created'].replace(' ', 'T') + 'Z'
                        else:
                            session_dict['created'] = str(session_dict['created']).replace(' ', 'T') + 'Z'
                    except Exception as e:
                        print(f"Error formatting created: {e}")
                        session_dict['created'] = str(session_dict['created'])
                sessions.append(session_dict)
                
            # Get total count of unique sessions
            cursor.execute('SELECT COUNT(DISTINCT session_id) FROM session_records')
            total_sessions = cursor.fetchone()[0]
            
        else:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            # Get session summaries with count, timestamps, and emotion variety
            cursor.execute('''
                SELECT 
                    session_id,
                    COUNT(*) as records,
                    MIN(created_at) as created
                FROM session_records 
                GROUP BY session_id
                ORDER BY created DESC 
                LIMIT %s OFFSET %s
            ''', (limit, offset))
            
            rows = cursor.fetchall()
            sessions = [dict(row) for row in rows]
            
            # Get total count of unique sessions
            cursor.execute('SELECT COUNT(DISTINCT session_id) FROM session_records')
            total_sessions = cursor.fetchone()['count']
        
        conn.close()
        
        # Debug logging
        print(f"Sessions endpoint: Found {len(sessions)} sessions, total: {total_sessions}")
        
        # Check if we have any data
        if total_sessions == 0:
            return {
                "items": [],
                "total": 0,
                "has_more": False,
                "message": "No sessions found in database"
            }
        
        return {
            "items": sessions,
            "total": total_sessions,
            "has_more": len(sessions) == limit
        }
    except Exception as e:
        # Log the error for debugging
        print(f"Error in sessions endpoint: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        # Return a fallback response
        return {
            "items": [], 
            "total": 0,
            "has_more": False,
            "error": f"Database connection issue: {type(e).__name__}: {str(e)}"
        }

@app.get("/api/sessions/{session_id}")
async def get_session_by_id(session_id: str):
    """Get all records for a specific session"""
    conn = get_db_connection()
    
    # Check if we're using SQLite or PostgreSQL
    is_sqlite = hasattr(conn, 'execute') and 'sqlite' in str(type(conn)).lower()
    
    if is_sqlite:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM session_records 
            WHERE session_id = ? 
            ORDER BY timestamp
        ''', (session_id,))
        
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        sessions = []
        for row in rows:
            session_dict = dict(zip(columns, row))
            sessions.append(session_dict)
    else:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('''
            SELECT * FROM session_records 
            WHERE session_id = %s 
            ORDER BY timestamp
        ''', (session_id,))
        
        rows = cursor.fetchall()
        sessions = [dict(row) for row in rows]
    
    conn.close()
    return {"session_id": session_id, "records": sessions}

@app.get("/api/sessions/{session_id}/download")
async def download_session_with_nested_structure(session_id: str):
    """Download session data with original nested structure preserved"""
    conn = get_db_connection()
    
    # Check if we're using SQLite or PostgreSQL
    is_sqlite = hasattr(conn, 'execute') and 'sqlite' in str(type(conn)).lower()
    
    if is_sqlite:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM session_records 
            WHERE session_id = ? 
            ORDER BY timestamp
        ''', (session_id,))
        
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        flat_records = []
        for row in rows:
            record_dict = dict(zip(columns, row))
            flat_records.append(record_dict)
    else:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('''
            SELECT * FROM session_records 
            WHERE session_id = %s 
            ORDER BY timestamp
        ''', (session_id,))
        
        rows = cursor.fetchall()
        flat_records = [dict(row) for row in rows]
    
    conn.close()
    
    # Reconstruct nested structure
    nested_records = []
    for record in flat_records:
        nested_record = {
            "session_id": record.get("session_id"),
            "phase": record.get("phase"),
            "area": record.get("area"),
            "timestamp": record.get("timestamp"),
            "conversation_data": {
                "speaker": record.get("speaker"),
                "text": record.get("text")
            },
            "hmd_data": {
                "position": {
                    "x": record.get("hmd_position_x"),
                    "y": record.get("hmd_position_y"),
                    "z": record.get("hmd_position_z")
                },
                "gaze_vector": {
                    "x": record.get("hmd_gaze_x"),
                    "y": record.get("hmd_gaze_y"),
                    "z": record.get("hmd_gaze_z")
                },
                "gaze_actor": record.get("hmd_gaze_actor"),
                "movement_speed": record.get("hmd_movement_speed")
            },
            "controller_data": {
                "r_position": {
                    "x": record.get("controller_r_x"),
                    "y": record.get("controller_r_y"),
                    "z": record.get("controller_r_z")
                },
                "l_position": {
                    "x": record.get("controller_l_x"),
                    "y": record.get("controller_l_y"),
                    "z": record.get("controller_l_z")
                },
                "r_interacted_actor": record.get("controller_r_actor"),
                "l_interacted_actor": record.get("controller_l_actor"),
                "r_movement_speed": record.get("controller_r_speed"),
                "l_movement_speed": record.get("controller_l_speed")
            },
            "user_emotion": record.get("user_emotion"),
            "emotion_window_flag": record.get("emotion_window_flag")
        }
        nested_records.append(nested_record)
    
    return JSONResponse(
        content=nested_records,
        headers={"Content-Disposition": f"attachment; filename=session_{session_id}.json"}
    )

@app.get("/api/health")
async def health_check():
    """Health check endpoint to test database connection"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute('SELECT 1')
        cursor.fetchone()
        
        # Check if table exists and has data
        cursor.execute('SELECT COUNT(*) FROM session_records')
        total_records = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT session_id) FROM session_records')
        total_sessions = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "total_records": total_records,
            "total_sessions": total_sessions
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": f"{type(e).__name__}: {str(e)}"
        }

@app.get("/api/stats")
async def get_stats():
    """Get basic statistics about the data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if we're using SQLite or PostgreSQL
    is_sqlite = hasattr(conn, 'execute') and 'sqlite' in str(type(conn)).lower()
    
    # Total records
    cursor.execute('SELECT COUNT(*) FROM session_records')
    total_records = cursor.fetchone()[0]
    
    # Unique sessions
    cursor.execute('SELECT COUNT(DISTINCT session_id) FROM session_records')
    unique_sessions = cursor.fetchone()[0]
    
    # Recent activity (last 24 hours)
    if is_sqlite:
        cursor.execute('''
            SELECT COUNT(*) FROM session_records 
            WHERE created_at >= datetime('now', '-1 day')
        ''')
    else:
        cursor.execute('''
            SELECT COUNT(*) FROM session_records 
            WHERE created_at >= NOW() - INTERVAL '1 day'
        ''')
    recent_records = cursor.fetchone()[0]
    
    # Most common emotions
    cursor.execute('''
        SELECT user_emotion, COUNT(*) as count 
        FROM session_records 
        WHERE user_emotion IS NOT NULL AND user_emotion != ''
        GROUP BY user_emotion 
        ORDER BY count DESC 
        LIMIT 5
    ''')
    top_emotions = cursor.fetchall()
    
    conn.close()
    
    return {
        "total_records": total_records,
        "unique_sessions": unique_sessions,
        "recent_records_24h": recent_records,
        "top_emotions": [{"emotion": emotion, "count": count} for emotion, count in top_emotions]
    }

@app.delete("/api/clear")
async def clear_data():
    """Clear all data from the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM session_records')
    conn.commit()
    conn.close()
    return {"message": "All data cleared"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
