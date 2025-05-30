#!/usr/bin/env python
"""
Test script for the simplified JABU chatbot
"""
import os
import django
import sys
import logging

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academic_chatbot.settings')
django.setup()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import required models and services
from chat.services import ChatService
from users.models import StudentProfile, User
from crawler.models import KnowledgeBase
from django.db import transaction
from django.contrib.auth.hashers import make_password

def setup_test_data():
    """Create test data for the demo"""
    logger.info("Setting up test data...")
    
    # Create test knowledge base entries
    try:
        with transaction.atomic():
            # Only create if they don't exist
            if KnowledgeBase.objects.count() == 0:
                KnowledgeBase.objects.create(
                    title="Admission Requirements",
                    content="To apply for admission to JABU, candidates must have completed secondary education "
                            "with credits in at least five subjects including English and Mathematics. "
                            "International students must provide proof of English proficiency.",
                    source_url="https://www.jabu.edu.ng/admissions",
                    is_verified=True
                )
                
                KnowledgeBase.objects.create(
                    title="Undergraduate Programs",
                    content="JABU offers undergraduate programs in various disciplines including "
                            "Business Administration, Computer Science, Agriculture, Law, and Health Sciences. "
                            "Most programs require four years of study.",
                    source_url="https://www.jabu.edu.ng/academics/programmes",
                    is_verified=True
                )
                
                KnowledgeBase.objects.create(
                    title="Student Accommodation",
                    content="JABU provides on-campus accommodation for students in various hostels. "
                            "Accommodation is allocated on a first-come, first-served basis. "
                            "Students must apply for housing at the beginning of each academic year.",
                    source_url="https://www.jabu.edu.ng/student-life/accommodation",
                    is_verified=True
                )
                
                logger.info("Created test knowledge base entries")
    except Exception as e:
        logger.error(f"Error creating knowledge base entries: {e}")
    
    # Create test student
    try:
        with transaction.atomic():
            # Create user if it doesn't exist
            if not User.objects.filter(username="teststudent").exists():
                user = User.objects.create(
                    username="teststudent",
                    email="test@example.com",
                    password=make_password("password123")
                )
                
                # Create student profile
                StudentProfile.objects.create(
                    user=user,
                    name="Test Student",
                    email="test@example.com",
                    program="Computer Science",
                    year_of_study=2,
                    student_id="JAB123456",
                    bio="Test student account for demo purposes"
                )
                
                logger.info("Created test student account")
    except Exception as e:
        logger.error(f"Error creating test student: {e}")


def test_chat_service():
    """Test the simplified chat service"""
    logger.info("Testing chat service...")
    
    # Create service
    chat_service = ChatService()
    
    # Test queries
    test_queries = [
        "What are the admission requirements for JABU?",
        "Tell me about undergraduate programs",
        "Is on-campus accommodation available?",
        "What programs are available in computer science?"
    ]
    
    # Student ID for testing
    student_id = "JAB123456"
    
    # Test each query
    for query in test_queries:
        logger.info(f"Testing query: {query}")
        
        # Generate response
        try:
            response = chat_service.generate_response(query, student_id)
            
            logger.info(f"Response: {response['response'][:100]}...")
            logger.info(f"Sources: {len(response['sources'])} found")
            logger.info(f"Conversation ID: {response['conversation_id']}")
            logger.info("-" * 50)
        except Exception as e:
            logger.error(f"Error generating response: {e}")


if __name__ == "__main__":
    try:
        # Set up test data
        setup_test_data()
        
        # Test the chat service
        test_chat_service()
        
        logger.info("Test completed successfully!")
    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)
