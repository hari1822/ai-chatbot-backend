#!/usr/bin/env python3
"""
Test script to verify OpenRouter integration is working correctly.
Run this script to test the AI chat functionality.
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base URL for your API
BASE_URL = "http://localhost:8000"

def test_openrouter_config():
    """Test if OpenRouter is configured correctly"""
    print("Testing OpenRouter configuration...")
    
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    openrouter_model = os.getenv("OPENROUTER_MODEL")
    
    if not openrouter_api_key or openrouter_api_key == "your_openrouter_api_key_here":
        print("❌ OpenRouter API key is not configured!")
        print("   Please set OPENROUTER_API_KEY in your .env file")
        print("   Get your API key from: https://openrouter.ai/keys")
        return False
    
    print(f"✅ OpenRouter API key configured: {openrouter_api_key[:10]}...")
    print(f"✅ OpenRouter model: {openrouter_model}")
    return True

def get_auth_token():
    """Login and get auth token"""
    print("\nLogging in to get auth token...")
    
    # First try to register a test user
    register_data = {
        "email": "test-ai@example.com",
        "name": "AI Test User", 
        "password": "testpassword123"
    }
    
    try:
        requests.post(f"{BASE_URL}/auth/register", json=register_data)
    except:
        pass  # User might already exist
    
    # Now login
    login_data = {
        "email": "test-ai@example.com",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            token = data.get("token", {}).get("access_token")
            if token:
                print("✅ Successfully logged in")
                return token
        
        print(f"❌ Login failed: {response.status_code}")
        return None
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_ai_chat(token):
    """Test the AI chat functionality"""
    print("\nTesting AI chat functionality...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Create a new chat session
        print("Creating new chat session...")
        response = requests.post(f"{BASE_URL}/chat/sessions?title=AI Test Chat", headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Failed to create chat session: {response.status_code}")
            return False
        
        session_data = response.json()
        session_id = session_data["id"]
        print(f"✅ Created chat session {session_id}")
        
        # Send a test message
        print("Sending test message to AI...")
        test_message = {
            "content": "Hello! Can you tell me a short joke about programming?",
            "sender_type": "user"
        }
        
        response = requests.post(
            f"{BASE_URL}/chat/sessions/{session_id}/messages",
            headers=headers,
            json=test_message
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to send message: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        ai_response = response.json()
        print(f"✅ AI Response received!")
        print(f"AI said: {ai_response['content'][:100]}...")
        
        # Test another message for conversation context
        print("\nTesting conversation context...")
        followup_message = {
            "content": "That's funny! Can you explain why it's funny?",
            "sender_type": "user"
        }
        
        response = requests.post(
            f"{BASE_URL}/chat/sessions/{session_id}/messages",
            headers=headers,
            json=followup_message
        )
        
        if response.status_code == 200:
            ai_response2 = response.json()
            print(f"✅ Follow-up response received!")
            print(f"AI explained: {ai_response2['content'][:100]}...")
            
            # Check if session title was updated
            response = requests.get(f"{BASE_URL}/chat/sessions", headers=headers)
            if response.status_code == 200:
                sessions = response.json()
                updated_session = next((s for s in sessions if s['id'] == session_id), None)
                if updated_session and updated_session['title'] != 'AI Test Chat':
                    print(f"✅ Session title auto-updated to: {updated_session['title']}")
                else:
                    print("ℹ️ Session title not auto-updated (this is optional)")
            
            return True
        else:
            print(f"❌ Follow-up message failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ AI chat test error: {e}")
        return False

def test_openrouter_direct():
    """Test OpenRouter API directly"""
    print("\nTesting OpenRouter API directly...")
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    
    if not api_key or api_key == "your_openrouter_api_key_here":
        print("❌ Cannot test OpenRouter directly - API key not configured")
        return False
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "AI Chatbot Test"
    }
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful AI assistant. Respond with 'OpenRouter connection successful!' if you can see this message."
            },
            {
                "role": "user",
                "content": "Hello, can you confirm the connection is working?"
            }
        ],
        "max_tokens": 100,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                ai_message = data["choices"][0]["message"]["content"]
                print(f"✅ OpenRouter direct connection successful!")
                print(f"Response: {ai_message}")
                return True
            else:
                print(f"❌ Unexpected OpenRouter response format: {data}")
                return False
        else:
            print(f"❌ OpenRouter API failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ OpenRouter direct test error: {e}")
        return False

def main():
    """Run all OpenRouter integration tests"""
    print("🤖 Starting OpenRouter Integration Tests...\n")
    
    # Test 1: Configuration
    if not test_openrouter_config():
        print("\n❌ Configuration test failed. Please fix configuration before proceeding.")
        print("\nTo fix:")
        print("1. Get an API key from https://openrouter.ai/keys")
        print("2. Add it to your .env file: OPENROUTER_API_KEY=your_actual_key_here")
        print("3. Restart the backend server")
        return
    
    # Test 2: Direct OpenRouter API
    if not test_openrouter_direct():
        print("\n❌ Direct OpenRouter API test failed.")
        print("This might indicate an issue with your API key or network connection.")
        return
    
    # Test 3: Backend integration
    token = get_auth_token()
    if not token:
        print("\n❌ Cannot proceed - authentication failed")
        return
    
    # Test 4: AI chat functionality
    if test_ai_chat(token):
        print("\n🎉 All OpenRouter integration tests passed!")
        print("\n✅ Your AI chatbot is ready to use with real AI responses!")
        print("\nNext steps:")
        print("1. Start your backend: cd ai-chatbot-backend && python run.py")
        print("2. Start your frontend: cd ai-chatbot-app && npm start")
        print("3. Go to http://localhost:3000 and start chatting!")
    else:
        print("\n❌ AI chat functionality test failed.")
        print("Check the backend logs for more detailed error information.")

if __name__ == "__main__":
    main()
