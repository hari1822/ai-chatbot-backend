#!/usr/bin/env python3
"""
Test script to verify authentication endpoints are working correctly.
Run this script to test login and user fetching functionality.
"""

import requests
import json

# Base URL for your API
BASE_URL = "http://localhost:8000"

def test_registration():
    """Test user registration"""
    print("Testing registration...")
    
    user_data = {
        "email": "test@example.com",
        "name": "Test User",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        print(f"Registration Response: {response.status_code}")
        print(f"Response Data: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Registration successful!")
            return True
        else:
            print("❌ Registration failed!")
            return False
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return False

def test_login():
    """Test user login"""
    print("\nTesting login...")
    
    login_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"Login Response: {response.status_code}")
        response_data = response.json()
        print(f"Response Data: {json.dumps(response_data, indent=2)}")
        
        if response.status_code == 200 and response_data.get("success"):
            print("✅ Login successful!")
            return response_data.get("token", {}).get("access_token")
        else:
            print("❌ Login failed!")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_get_current_user(token):
    """Test getting current user with token"""
    print("\nTesting get current user...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        print(f"Get User Response: {response.status_code}")
        response_data = response.json()
        print(f"Response Data: {json.dumps(response_data, indent=2)}")
        
        if response.status_code == 200:
            print("✅ Get current user successful!")
            return True
        else:
            print("❌ Get current user failed!")
            return False
    except Exception as e:
        print(f"❌ Get current user error: {e}")
        return False

def test_chat_sessions(token):
    """Test chat sessions endpoint"""
    print("\nTesting chat sessions...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Test getting sessions
        response = requests.get(f"{BASE_URL}/chat/sessions", headers=headers)
        print(f"Get Sessions Response: {response.status_code}")
        print(f"Sessions: {response.json()}")
        
        # Test creating a session
        response = requests.post(f"{BASE_URL}/chat/sessions?title=Test Session", headers=headers)
        print(f"Create Session Response: {response.status_code}")
        session_data = response.json()
        print(f"New Session: {json.dumps(session_data, indent=2)}")
        
        if response.status_code == 200:
            print("✅ Chat sessions working!")
            return session_data.get("id")
        else:
            print("❌ Chat sessions failed!")
            return None
    except Exception as e:
        print(f"❌ Chat sessions error: {e}")
        return None

def main():
    """Run all tests"""
    print("🚀 Starting API Tests...\n")
    
    # Test registration (might fail if user already exists)
    test_registration()
    
    # Test login
    token = test_login()
    
    if not token:
        print("\n❌ Cannot proceed without valid token")
        return
    
    # Test getting current user
    if not test_get_current_user(token):
        print("\n❌ User authentication is not working properly")
        return
    
    # Test chat functionality
    session_id = test_chat_sessions(token)
    
    if session_id:
        print(f"\n✅ All tests passed! Chat functionality is working.")
    else:
        print(f"\n⚠️ Authentication works but chat functionality has issues.")
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    main()
