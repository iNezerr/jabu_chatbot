"""
Script to test Profile and Feedback APIs using username/password authentication
"""
import os
import django
import requests
from getpass import getpass
import json

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academic_chatbot.settings')
django.setup()

# Base URL for APIs
BASE_URL = "http://localhost:8000/api"

def get_auth_token(username, password):
    """Get JWT authentication token using username and password"""
    auth_url = f"{BASE_URL}/token/"
    
    response = requests.post(auth_url, json={
        "username": username,
        "password": password
    })
    
    if response.status_code == 200:
        token_data = response.json()
        # Return the access token
        return token_data.get("access")
    else:
        print(f"Authentication failed: {response.status_code}")
        print(response.text)
        return None

def test_profile_api(headers):
    """Test the profile API endpoints"""
    
    print("\n==== Testing Profile API ====")
    
    # Get all profiles (admin only)
    print("\n1. Getting all profiles...")
    response = requests.get(f"{BASE_URL}/profiles/", headers=headers)
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data)} profiles")
    
    # Get my profile
    print("\n2. Getting my profile...")
    response = requests.get(f"{BASE_URL}/my-profile/", headers=headers)
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))

def test_feedback_api(headers):
    """Test the feedback API endpoints"""
    # Add content-type header
    headers = headers.copy()
    headers['Content-Type'] = 'application/json'
    
    print("\n==== Testing Feedback API ====")
    
    # First, get a chat ID to rate
    print("\n1. Sending a chat message first to get a chat ID...")
    chat_data = {
        'message': 'What programs are offered at JABU?'
    }
    response = requests.post(f"{BASE_URL}/chat/", json=chat_data, headers=headers)
    print(f"Chat status code: {response.status_code}")
    
    if response.status_code != 200:
        print("Failed to get chat ID. Skipping feedback test.")
        return
    
    # Submit feedback
    print("\n2. Submitting feedback...")
    chat_id = 1  # Fallback chat ID if we can't get a real one
    try:
        chat_log_id = response.json().get('data', {}).get('chat_log_id', chat_id)
    except:
        chat_log_id = chat_id
        
    feedback_data = {
        'chat_log': chat_log_id,
        'rating': 5,
        'comment': 'This was a very helpful answer!'
    }
    
    response = requests.post(f"{BASE_URL}/feedback/", json=feedback_data, headers=headers)
    print(f"Feedback status code: {response.status_code}")
    if response.status_code == 201:
        print(json.dumps(response.json(), indent=2))

def main():
    """Main function to run tests"""
    # Get username and password for authentication
    username = input("Enter username: ").strip()
    password = getpass("Enter password: ").strip()
    
    # Get authentication token
    auth_token = get_auth_token(username, password)
    
    # Set up headers for API requests
    headers = {}
    if auth_token:
        headers['Authorization'] = f'Bearer {auth_token}'
        print("Successfully authenticated!")
    else:
        print("Proceeding without authentication (some tests may fail)")
    
    # Test APIs
    test_profile_api(headers)
    test_feedback_api(headers)

if __name__ == "__main__":
    main()
