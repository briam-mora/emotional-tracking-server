#!/usr/bin/env python3
"""
Test script for the VR Session Data Server
"""

import requests
import json
import time
from datetime import datetime

# Server URL (change this to your deployed URL)
SERVER_URL = "http://localhost:8000"

def create_test_data():
    """Create sample session data matching Unity format"""
    return [
        {
            "session_id": "test-session-123",
            "phase": "test_phase",
            "area": "test_area",
            "timestamp": datetime.utcnow().isoformat(),
            "conversation_data": {
                "speaker": "user",
                "text": "Hello, this is a test message"
            },
            "hmd_data": {
                "position": {"x": 1.5, "y": 2.0, "z": 0.5},
                "gaze_vector": {"x": 0.0, "y": 0.0, "z": 1.0},
                "gaze_actor": "test_object",
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
            "emotion_window_flag": True
        },
        {
            "session_id": "test-session-123",
            "phase": "test_phase",
            "area": "test_area",
            "timestamp": datetime.utcnow().isoformat(),
            "conversation_data": {
                "speaker": "ai",
                "text": "Hello! How are you feeling today?"
            },
            "hmd_data": {
                "position": {"x": 1.6, "y": 2.1, "z": 0.6},
                "gaze_vector": {"x": 0.1, "y": 0.1, "z": 0.9},
                "gaze_actor": "ai_avatar",
                "movement_speed": 0.2
            },
            "controller_data": {
                "r_position": {"x": 1.1, "y": 1.6, "z": 0.1},
                "l_position": {"x": -0.9, "y": 1.4, "z": -0.1},
                "r_interacted_actor": "none",
                "l_interacted_actor": "none",
                "r_movement_speed": 0.1,
                "l_movement_speed": 0.1
            },
            "user_emotion": "excited",
            "emotion_window_flag": False
        }
    ]

def test_upload():
    """Test file upload functionality"""
    print("Testing file upload...")
    
    # Create test data
    test_data = create_test_data()
    
    # Save to temporary file
    with open("test_session_data.json", "w") as f:
        json.dump(test_data, f, indent=2)
    
    # Upload file
    with open("test_session_data.json", "rb") as f:
        files = {"file": ("test_session_data.json", f, "application/json")}
        response = requests.post(f"{SERVER_URL}/upload", files=files)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Upload successful: {result['records_added']} records added")
        return True
    else:
        print(f"❌ Upload failed: {response.status_code} - {response.text}")
        return False

def test_stats():
    """Test statistics endpoint"""
    print("\nTesting statistics endpoint...")
    
    response = requests.get(f"{SERVER_URL}/api/stats")
    
    if response.status_code == 200:
        stats = response.json()
        print("✅ Statistics retrieved:")
        print(f"   Total records: {stats['total_records']}")
        print(f"   Unique sessions: {stats['unique_sessions']}")
        print(f"   Recent records (24h): {stats['recent_records_24h']}")
        print(f"   Top emotions: {stats['top_emotions']}")
        return True
    else:
        print(f"❌ Statistics failed: {response.status_code} - {response.text}")
        return False

def test_sessions():
    """Test sessions endpoint"""
    print("\nTesting sessions endpoint...")
    
    response = requests.get(f"{SERVER_URL}/api/sessions?limit=10")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Sessions retrieved: {len(data['sessions'])} records")
        if data['sessions']:
            session = data['sessions'][0]
            print(f"   Sample session ID: {session['session_id']}")
            print(f"   Sample emotion: {session['user_emotion']}")
        return True
    else:
        print(f"❌ Sessions failed: {response.status_code} - {response.text}")
        return False

def test_dashboard():
    """Test dashboard accessibility"""
    print("\nTesting dashboard...")
    
    response = requests.get(f"{SERVER_URL}/")
    
    if response.status_code == 200:
        print("✅ Dashboard accessible")
        return True
    else:
        print(f"❌ Dashboard failed: {response.status_code}")
        return False

def main():
    """Run all tests"""
    print("🧪 VR Session Data Server Test Suite")
    print("=" * 40)
    
    tests = [
        test_upload,
        test_stats,
        test_sessions,
        test_dashboard
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Server is working correctly.")
    else:
        print("⚠️  Some tests failed. Check server logs for details.")
    
    # Cleanup
    try:
        import os
        if os.path.exists("test_session_data.json"):
            os.remove("test_session_data.json")
    except:
        pass

if __name__ == "__main__":
    main()
