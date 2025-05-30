"""
Script to test the chat functionality directly
"""
import os
import django
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academic_chatbot.settings')
django.setup()

from chat.services import ChatService

async def test_chat():
    """Test chat functionality"""
    # Create chat service
    chat_service = ChatService()
    
    # Test questions
    questions = [
        "What programs does JABU offer?",
        "What are the admission requirements for Computer Science?",
        "How can I apply for a scholarship?",
    ]
    
    for question in questions:
        print(f"\n\033[1mQuestion:\033[0m {question}")
        print("-" * 50)
        
        # Generate response
        response_data = await chat_service.generate_response(question)
        
        # Print response
        print(f"\033[1mResponse:\033[0m {response_data['response']}")
        
        # Print sources
        if response_data['sources']:
            print("\n\033[1mSources:\033[0m")
            for source in response_data['sources']:
                print(f"- {source.get('title', 'Untitled')} ({source.get('relevance', 'N/A')})")
        else:
            print("\n\033[1mSources:\033[0m None")
        
        print("=" * 50)

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_chat())
