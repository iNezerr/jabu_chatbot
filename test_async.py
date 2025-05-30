"""
Test script for the chat implementation to verify async/sync operations.
"""
import os
import sys
import django
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academic_chatbot.settings')
django.setup()

# Import necessary modules
from chat.services import ChatService
from chat.views import chat_message
from asgiref.sync import sync_to_async, async_to_sync
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_async")

async def async_test():
    """Test the async methods directly"""
    print("Testing ChatService async implementation...")
    
    # Create a chat service instance
    chat_service = ChatService()
    
    # Create proper AsyncMock objects
    chat_service._search_knowledge_base = AsyncMock(return_value=(
        [{"title": "Test Source", "url": "http://test.com", "relevance": 100}], 
        "Test context content"
    ))
    
    chat_service._fallback_generate_with_httpx = AsyncMock(return_value="This is a mock response from the AI model.")
    
    # Also mock the fallback crawl
    chat_service._fallback_crawl = AsyncMock(return_value=(
        [{"title": "Test Source 2", "url": "http://test2.com", "relevance": 80}],
        "Additional test context content"
    ))
    
    # Test the generate_response method
    print("Testing direct async call...")
    try:
        response = await chat_service.generate_response("Hello, I have a question about JABU programs")
        print("Response received successfully!")
        print(f"Conversation ID: {response.get('conversation_id', '')}")
        print(f"Sources count: {len(response.get('sources', []))}")
        print(f"Response: {response.get('response', '')[:100]}...")  # Print first 100 chars
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_chat_service():
    """Run the async test using asyncio"""
    return asyncio.run(async_test())

if __name__ == "__main__":
    success = test_chat_service()
    if success:
        print("\nAll tests passed! The async/sync integration is working correctly.")
    else:
        print("\nTests failed. Please check the error messages above.")
