"""
Chat service module to handle interactions with the AI model
"""
import os
import json
import httpx
import uuid
import logging
from typing import Dict, List, Optional, Tuple, Any
from crawler.search import search_knowledge_base, get_relevant_content
from crawler.utils import crawl_and_store
from crawler.models import KnowledgeBase
from chat.models import ChatLog
from users.models import StudentProfile
from groq import Groq

# Configure logging
logger = logging.getLogger(__name__)

class ChatService:
    """
    Service for handling chat interactions with the AI model
    """
    # Default system prompt template
    DEFAULT_SYSTEM_PROMPT = """
    You are an AI academic counselor for Joseph Ayo Babalola University (JABU).
    Your role is to provide accurate information about academic programs, courses, 
    admission requirements, and student services.
    
    Base your responses on the knowledge sources provided below.
    If you don't know the answer, inform the student that you don't have that information,
    but you'll help them find it or direct them to contact the appropriate department.
    
    Always be professional, supportive, and focus on providing accurate information.
    
    KNOWLEDGE SOURCES:
    {knowledge_sources}
    """
    
    def __init__(self):
        """Initialize the chat service"""
        self.api_key = os.getenv("GROQ_API_KEY")
        self.api_base = os.getenv("GROQ_API_BASE", "https://api.groq.com/v1")
        self.model = os.getenv("GROQ_MODEL", "llama3-70b-8192")
        
        # Initialize Groq client if available
        try:
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
            self.groq_available = True
        except (ImportError, Exception) as e:
            logger.warning(f"Groq client initialization failed: {str(e)}")
            self.groq_available = False
    
    def _get_conversation_id(self, conversation_id: Optional[str] = None) -> str:
        """
        Get or generate a conversation ID
        
        Args:
            conversation_id: Existing conversation ID or None
            
        Returns:
            str: Conversation ID
        """
        return conversation_id or str(uuid.uuid4())
    
    def _search_knowledge_base(self, query: str) -> Tuple[List[Dict], str]:
        """
        Search the knowledge base for relevant information
        
        Args:
            query: User query string
            
        Returns:
            Tuple containing:
            - List of sources (dict)
            - Formatted context string for AI prompt
        """
        # Search knowledge base for relevant content
        results = search_knowledge_base(query, limit=3)
        
        if not results:
            return [], ""
        
        # Format sources for response
        sources = []
        context_parts = []
        
        for entry, score in results:
            source = {
                "title": entry.title,
                "url": entry.source_url,
                "relevance": score
            }
            sources.append(source)
            
            # Format context for AI input
            context = f"Source: {entry.title}\n"
            if entry.source_url:
                context += f"URL: {entry.source_url}\n"
            context += f"Content: {entry.content[:1000]}...\n" if len(entry.content) > 1000 else f"Content: {entry.content}\n"
            context_parts.append(context)
        
        # Format all context parts into one string
        formatted_context = "\n---\n".join(context_parts)
        
        return sources, formatted_context
    
    def _fallback_crawl(self, query: str) -> Tuple[List[Dict], str]:
        """
        Fallback method to crawl relevant information if knowledge base search fails
        
        Args:
            query: User query string
            
        Returns:
            Tuple containing:
            - List of sources (dict)
            - Formatted context string for AI prompt
        """
        # Extract keywords to determine what page might have relevant info
        keywords = query.lower().split()
        
        base_url = "https://www.jabu.edu.ng"
        
        # Map of keywords to likely JABU URLs
        url_mapping = {
            "":f"{base_url}/academics/",
            "admissions": f"{base_url}/admissions/",
            "library": f"{base_url}/library/",
            "jabu staff": f"{base_url}/jabu-staff/",
            "about": f"{base_url}/about/",
            "offices": f"{base_url}/offices/",
            "undergraduate programmes": f"{base_url}/academics/programmes/undergraduate-programmes/",
            "academic calendar": f"{base_url}/academics/academic-calendar/",
            "college of agriculture and natural sciences": f"{base_url}/academics/colleges/college-of-agriculture-and-natural-sciences/",
            "college of environmental sciences": f"{base_url}/academics/colleges/college-of-environmental-sciences/",
            "college of health sciences": f"{base_url}/academics/colleges/college-of-health-sciences/",
            "college of humanities and social sciences": f"{base_url}/academics/colleges/college-of-humanities-and-social-sciences/",
            "college of law": f"{base_url}/academics/colleges/college-of-law/",
            "college of management sciences": f"{base_url}/academics/colleges/college-of-management-sciences/",
            "college of postgraduate studies": f"{base_url}/academics/colleges/college-of-postgraduate-studies/"
        }
        
        # Find potential URLs to crawl based on query keywords
        urls_to_crawl = []
        for keyword, url in url_mapping.items():
            if any(kw in keyword for kw in keywords):
                if url not in urls_to_crawl:
                    urls_to_crawl.append(url)
        
        # Fallback to main URLs if no match
        if not urls_to_crawl:
            urls_to_crawl = ["https://www.jabu.edu.ng/academics"]
        
        # Crawl URLs and store in knowledge base
        sources = []
        context_parts = []
        
        for url in urls_to_crawl[:1]:  # Limit to just one URL for now
            kb_entry = crawl_and_store(url, KnowledgeBase)
            
            if kb_entry:
                source = {
                    "title": kb_entry.title,
                    "url": kb_entry.source_url,
                    "relevance": 50  # Default relevance score
                }
                sources.append(source)
                
                # Format context for AI input
                context = f"Source: {kb_entry.title}\n"
                if kb_entry.source_url:
                    context += f"URL: {kb_entry.source_url}\n"
                context += f"Content: {kb_entry.content[:1000]}...\n" if len(kb_entry.content) > 1000 else f"Content: {kb_entry.content}\n"
                context_parts.append(context)
        
        # Format all context parts into one string
        formatted_context = "\n---\n".join(context_parts)
        
        return sources, formatted_context
    
    async def generate_response(self, user_message: str, student_id: Optional[str] = None, 
                               conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a response to the user message
        
        Args:
            user_message: User's question or message
            student_id: Optional student ID to track conversations
            conversation_id: Optional conversation ID for continued conversations
            
        Returns:
            Dict containing response, conversation ID, and sources
        """
        # Get or generate conversation ID
        conversation_id = self._get_conversation_id(conversation_id)
        
        # First try to find relevant information in the knowledge base
        sources, context = self._search_knowledge_base(user_message)
        
        # If no relevant information found, try crawling
        if not context:
            sources, context = self._fallback_crawl(user_message)
        
        # If still no context, use generic response
        if not context:
            context = "No specific information available on this topic."
        
        # Format system prompt with available context
        system_prompt = self.DEFAULT_SYSTEM_PROMPT.format(knowledge_sources=context)
        
        # Get student info if student_id is provided
        student_info = ""
        student = None
        if student_id:
            try:
                student = StudentProfile.objects.get(student_id=student_id)
                student_info = f"Student information: {student.name}, {student.program}, Year {student.year_of_study}"
            except StudentProfile.DoesNotExist:
                logger.warning(f"Student with ID {student_id} not found")
                student_info = ""
        
        # Call AI model to generate response
        try:
            # Prepare messages for the AI
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{student_info}\n\nStudent question: {user_message}"}
            ]
            
            # Generate AI response
            ai_response = ""
            
            # Use Groq client if available, otherwise fall back to httpx
            if self.groq_available and self.api_key:
                try:
                    # Use the Groq Python SDK
                    completion = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=0.7,
                        max_tokens=1024
                    )
                    ai_response = completion.choices[0].message.content
                    logger.info("Successfully generated response using Groq SDK")
                except Exception as e:
                    logger.error(f"Error using Groq SDK: {str(e)}")
                    # Fall back to httpx
                    ai_response = await self._fallback_generate_with_httpx(messages)
            else:
                # Use httpx for API calls
                ai_response = await self._fallback_generate_with_httpx(messages)
            
            # Save chat log if we have a valid student
            if student:
                ChatLog.objects.create(
                    student=student,
                    user_message=user_message,
                    ai_response=ai_response,
                    conversation_id=conversation_id
                )
                logger.info(f"Saved chat log for student {student_id}, conversation {conversation_id}")
            
            return {
                "response": ai_response,
                "conversation_id": conversation_id,
                "sources": sources
            }
            
        except Exception as e:
            # Log the error
            logger.error(f"Error generating response: {str(e)}")
            return {
                "response": "I'm sorry, I encountered an error while processing your request. Please try again later.",
                "conversation_id": conversation_id,
                "sources": []
            }
    
    async def _fallback_generate_with_httpx(self, messages):
        """
        Fallback method to generate AI responses using httpx
        
        Args:
            messages: List of message objects for the API
            
        Returns:
            str: Generated response text
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1024
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                response_data = response.json()
                return response_data['choices'][0]['message']['content']
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during API call: {str(e)}")
            # If API call fails, return a generic response
            return "I apologize, but I'm having trouble accessing the information right now. Please try again later."
        except Exception as e:
            logger.error(f"Unexpected error during API call: {str(e)}")
            # If something unexpected happens, return an error message
            return "I'm sorry, I encountered an error while processing your request. Please try again later."
