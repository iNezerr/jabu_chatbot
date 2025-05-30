"""
Super simple chat service for JABU chatbot
"""
import os
import httpx
import uuid
import logging
from chat.models import ChatLog
from users.models import StudentProfile
from crawler.models import KnowledgeBase
from django.db.models import Q

# Configure logging
logger = logging.getLogger(__name__)

class ChatService:
    """
    Simple service for chat interactions with the AI model
    """
    # System prompt for the AI
    SYSTEM_PROMPT = """
    You are an AI academic counselor for Joseph Ayo Babalola University (JABU).
    Provide accurate information about academic programs, courses, admissions, and student services.
    Base your responses on the knowledge sources provided.
    Be professional and helpful.
    
    KNOWLEDGE SOURCES:
    {knowledge_sources}
    """
    
    def __init__(self):
        """Initialize with API key"""
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = os.getenv("GROQ_MODEL", "llama3-70b-8192")
    
    def generate_response(self, message, student_id=None, conversation_id=None):
        """
        Generate a response to the student message
        """
        # Create conversation ID if needed
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        # Find relevant information
        sources = []
        knowledge = self._search_knowledge_base(message)
        
        # Format knowledge for AI
        if knowledge:
            knowledge_text = "\n\n".join([f"SOURCE: {k.title}\nCONTENT: {k.content[:1000]}" for k in knowledge])
            sources = [{"title": k.title, "url": k.source_url} for k in knowledge]
        else:
            knowledge_text = "No specific information available on this topic."
            
        # Get student info
        student = None
        if student_id:
            try:
                student = StudentProfile.objects.get(student_id=student_id)
            except StudentProfile.DoesNotExist:
                pass
        
        # Generate AI response
        prompt = self.SYSTEM_PROMPT.format(knowledge_sources=knowledge_text)
        ai_response = self._get_ai_response(prompt, message)
        
        # Save to database if student exists
        if student:
            try:
                chat_log = ChatLog.objects.create(
                    student=student,
                    user_message=message,
                    ai_response=ai_response,
                    conversation_id=conversation_id
                )
                logger.info(f"Successfully saved chat log for student {student.student_id}, conversation {conversation_id}")
            except Exception as e:
                logger.error(f"Failed to save chat log: {str(e)}")
        else:
            logger.warning(f"Chat log not saved: No student found for ID {student_id}")
        
        # Return response
        return {
            "response": ai_response,
            "conversation_id": conversation_id,
            "sources": sources
        }
    
    def _search_knowledge_base(self, query):
        """Find relevant information in knowledge base"""
        try:
            # Simple keyword search - just get the most relevant matches
            keywords = query.lower().split()
            q_objects = Q()
            
            # Add each keyword to the query
            for word in keywords:
                if len(word) > 2:  # Skip very short words
                    q_objects |= Q(content__icontains=word) | Q(title__icontains=word)
            
            # Get top 3 most relevant entries
            results = KnowledgeBase.objects.filter(q_objects)[:3]
            return list(results)
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return []
    
    def _get_ai_response(self, system_prompt, user_message):
        """Get response from AI model"""
        try:
            # Try using Groq SDK first
            try:
                from groq import Groq
                client = Groq(api_key=self.api_key)
                
                # Create messages for the AI
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
                
                # Call the API
                completion = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=800
                )
                
                return completion.choices[0].message.content
            except Exception as e:
                # Fall back to using httpx
                return self._call_api_with_httpx(system_prompt, user_message)
        
        except Exception as e:
            logger.error(f"AI response error: {e}")
            return "I'm sorry, I'm having trouble accessing information right now. Please try again later."
    
    def _call_api_with_httpx(self, system_prompt, user_message):
        """Make API call using httpx as fallback"""
        if not self.api_key:
            return f"[DEMO MODE] This is a sample response about: {user_message}"
            
        try:
            url = "https://api.groq.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.7,
                "max_tokens": 800
            }
            
            with httpx.Client(timeout=15.0) as client:
                response = client.post(url, headers=headers, json=data)
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"API call error: {e}")
            return "I'm sorry, I couldn't process your request at this time."
