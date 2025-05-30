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
    Simple service for handling chat interactions with the AI model
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
        """Initialize the chat service with API credentials"""
        self.api_key = os.getenv("GROQ_API_KEY")
        self.api_base = os.getenv("GROQ_API_BASE", "https://api.groq.com/v1")
        self.model = os.getenv("GROQ_MODEL", "llama3-70b-8192")
    
    def generate_response(self, message: str, student_id: str = None, 
                         conversation_id: str = None) -> Dict[str, Any]:
        """
        Generate a response to the student's message
        
        Args:
            message: Student's question or message
            student_id: Student's ID for conversation tracking
            conversation_id: Optional conversation ID for continued conversations
            
        Returns:
            Dict containing response, conversation ID, and sources
        """
        # Create a conversation ID if one doesn't exist
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        # Search the knowledge base for relevant information
        search_results = self._search_knowledge_base(message)
        
        # Format the sources and context for the AI
        sources, formatted_context = self._format_search_results(search_results)
        
        # Get student information if available
        student = self._get_student(student_id)
        student_info = ""
        if student:
            student_info = f"Student information: {student.name}, {student.program}, Year {student.year_of_study}"

        # Prepare the system prompt with context
        system_prompt = self.DEFAULT_SYSTEM_PROMPT.format(knowledge_sources=formatted_context)
        
        # Generate AI response
        ai_response = self._call_ai_model(system_prompt, message, student_info)
        
        # Save the conversation to the database
        if student:
            self._save_chat_log(student, message, ai_response, conversation_id)
            
        # Return the response data
        return {
            "response": ai_response,
            "conversation_id": conversation_id,
            "sources": sources
        }
    
    def _search_knowledge_base(self, query):
        """Search for relevant information in the knowledge base"""
        try:
            # Simple keyword search in the knowledge base
            keywords = query.lower().split()
            q_objects = [Q(content__icontains=word) | Q(title__icontains=word) for word in keywords]
            
            # Combine the Q objects
            combined_q = Q()
            for q in q_objects:
                combined_q |= q
                
            # Query the knowledge base
            results = KnowledgeBase.objects.filter(combined_q)[:3]
            return list(results)
        except Exception as e:
            logger.error(f"Error searching knowledge base: {str(e)}")
            return []
    
    def _format_search_results(self, results):
        """Format search results for the AI prompt and response"""
        sources = []
        context_parts = []
        
        for entry in results:
            source = {
                "title": entry.title,
                "url": entry.source_url,
                "relevance": 100  # Simple relevance score
            }
            sources.append(source)
            
            # Format context for the AI
            context = f"Source: {entry.title}\n"
            if entry.source_url:
                context += f"URL: {entry.source_url}\n"
            
            # Truncate long content
            content = entry.content
            if len(content) > 1000:
                content = content[:1000] + "..."
                
            context += f"Content: {content}\n"
            context_parts.append(context)
        
        if not context_parts:
            return [], "No specific information available on this topic."
        
        # Join all context parts
        formatted_context = "\n---\n".join(context_parts)
        return sources, formatted_context
    
    def _get_student(self, student_id):
        """Get student profile from the database"""
        if not student_id:
            return None
            
        try:
            student = StudentProfile.objects.get(student_id=student_id)
            return student
        except StudentProfile.DoesNotExist:
            logger.warning(f"Student with ID {student_id} not found")
            return None
    
    def _call_ai_model(self, system_prompt, user_message, student_info=""):
        """Call the AI model to generate a response"""
        try:
            # Use Groq API if available
            if self.api_key:
                try:
                    from groq import Groq
                    client = Groq(api_key=self.api_key)
                    
                    # Prepare the messages for the model
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"{student_info}\n\nStudent question: {user_message}"}
                    ]
                    
                    # Call the API
                    completion = client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=0.7,
                        max_tokens=1024
                    )
                    
                    return completion.choices[0].message.content
                except Exception as e:
                    logger.error(f"Error using Groq API: {str(e)}")
                    return self._call_api_with_httpx(system_prompt, user_message, student_info)
            else:
                return self._call_api_with_httpx(system_prompt, user_message, student_info)
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I'm sorry, I encountered an error while processing your request. Please try again later."
    
    def _call_api_with_httpx(self, system_prompt, user_message, student_info=""):
        """Call the AI model using httpx as a fallback"""
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # Prepare the messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{student_info}\n\nStudent question: {user_message}"}
            ]
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1024
            }
            
            # Send synchronous request
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                response_data = response.json()
                return response_data['choices'][0]['message']['content']
                
        except Exception as e:
            logger.error(f"Error in API call: {str(e)}")
            if not self.api_key:
                # Return a mock response for testing without API key
                return f"This is a mock response. I would answer about: {user_message}"
            return "I apologize, but I'm having trouble accessing information right now. Please try again later."
    
    def _save_chat_log(self, student, user_message, ai_response, conversation_id):
        """Save the chat interaction to the database"""
        try:
            ChatLog.objects.create(
                student=student,
                user_message=user_message,
                ai_response=ai_response,
                conversation_id=conversation_id
            )
            logger.info(f"Saved chat log for {student.name}, conversation {conversation_id}")
        except Exception as e:
            logger.error(f"Error saving chat log: {str(e)}")
import logging
from typing import Dict, Any, Optional, List, Tuple
from crawler.search import search_knowledge_base
from chat.models import ChatLog
from users.models import StudentProfile
from asgiref.sync import sync_to_async
from groq import Groq

# Configure logging
logger = logging.getLogger(__name__)

class ChatService:
    """
    Simple service for handling chat interactions with the AI model
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
            logger.info("Groq client initialized successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Groq client initialization failed: {str(e)}")
            self.groq_available = False
            logger.info("Will fall back to httpx for API calls")
    
    def _get_conversation_id(self, conversation_id: Optional[str] = None) -> str:
        """
        Get or generate a conversation ID
        
        Args:
            conversation_id: Existing conversation ID or None
            
        Returns:
            str: Conversation ID
        """
        return conversation_id or str(uuid.uuid4())
    
    async def _search_knowledge_base(self, query: str) -> Tuple[List[Dict], str]:
        """
        Search the knowledge base for relevant information
        
        Args:
            query: User query string
            
        Returns:
            Tuple containing:
            - List of sources (dict)
            - Formatted context string for AI prompt
        """
        # Search knowledge base for relevant content using sync_to_async
        @sync_to_async
        def async_search_knowledge_base(q):
            return search_knowledge_base(q, limit=3)
        
        results = await async_search_knowledge_base(query)
        
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
    
    async def _fallback_crawl(self, query: str) -> Tuple[List[Dict], str]:
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
            # Use sync_to_async if crawl_and_store is synchronous
            @sync_to_async
            def async_crawl_and_store(url, model):
                return crawl_and_store(url, model)
            
            kb_entry = await async_crawl_and_store(url, KnowledgeBase)
            
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
        sources, context = await self._search_knowledge_base(user_message)
        
        # If no relevant information found, try crawling
        if not context:
            # Convert to async if needed
            if asyncio.iscoroutinefunction(self._fallback_crawl):
                sources, context = await self._fallback_crawl(user_message)
            else:
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
            student = await self._get_student(student_id)
            if student:
                student_info = f"Student information: {student.name}, {student.program}, Year {student.year_of_study}"
        
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
                
                # If API calls still failed (no api key), provide a mock response for testing
                if "error" in ai_response.lower() and not self.api_key:
                    logger.warning("No API key available, using mock response")
                    ai_response = self._get_mock_response(user_message, context)
            
            # Save chat log if we have a valid student
            if student:
                await self._save_chat_log(student, user_message, ai_response, conversation_id)
            
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
    
    async def _fallback_generate_with_httpx(self, messages, max_retries=2):
        """
        Fallback method to generate AI responses using httpx
        
        Args:
            messages: List of message objects for the API
            max_retries: Maximum number of retries on failure
            
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
        
        retries = 0
        while retries <= max_retries:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    logger.info(f"Sending API request to {self.api_base}/chat/completions (attempt {retries + 1})")
                    response = await client.post(
                        f"{self.api_base}/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=30.0
                    )
                    response.raise_for_status()
                    response_data = response.json()
                    logger.info("API request successful")
                    return response_data['choices'][0]['message']['content']
            except httpx.HTTPError as e:
                logger.error(f"HTTP error during API call (attempt {retries + 1}): {str(e)}")
                if response.status_code == 429:  # Rate limit error
                    logger.warning("Rate limit hit, waiting before retry")
                    await asyncio.sleep(2 ** retries)  # Exponential backoff
                elif response.status_code >= 500:  # Server error
                    logger.warning(f"Server error {response.status_code}, will retry")
                    await asyncio.sleep(1)
                else:
                    # For other HTTP errors, don't retry
                    return "I apologize, but I'm having trouble accessing the information right now. Please try again later."
            except Exception as e:
                logger.error(f"Unexpected error during API call (attempt {retries + 1}): {str(e)}")
                # If something unexpected happens, wait a moment before retrying
                await asyncio.sleep(1)
            
            retries += 1
        
        # If we've exhausted all retries
        logger.error(f"All {max_retries} retries failed for API call")
        return "I'm sorry, I encountered an error while processing your request. Please try again later."
    
    def _get_mock_response(self, user_message, context):
        """
        Generate a mock response for testing when API key is not available
        
        Args:
            user_message (str): User's question
            context (str): Knowledge base context
            
        Returns:
            str: Mock response
        """
        # Extract the first few sentences from context if available
        first_paragraph = ""
        if "Content:" in context:
            try:
                content_part = context.split("Content:")[1].split("\n")[0]
                sentences = content_part.split(".")
                first_paragraph = ". ".join(sentences[:3]) + "."
            except:
                pass
                
        # Basic responses based on message keywords
        message_lower = user_message.lower()
        
        if "program" in message_lower or "course" in message_lower:
            return "JABU offers various undergraduate and postgraduate programs across several colleges. " + first_paragraph
            
        elif "admission" in message_lower or "apply" in message_lower or "application" in message_lower:
            return "To apply for admission to JABU, you need to complete the online application form and submit required documents. " + first_paragraph
            
        elif "fee" in message_lower or "tuition" in message_lower or "cost" in message_lower:
            return "Tuition fees at JABU vary depending on your program of study. Please contact the bursar's office for detailed information. " + first_paragraph
            
        elif "scholarship" in message_lower:
            return "JABU offers merit-based scholarships to outstanding students. Applications are typically open at the beginning of each academic year. " + first_paragraph
            
        elif "accommodation" in message_lower or "hostel" in message_lower or "housing" in message_lower:
            return "JABU provides on-campus accommodation for students. Hostel allocation is done on a first-come, first-served basis. " + first_paragraph
            
        elif "academic calendar" in message_lower or "semester" in message_lower or "session" in message_lower:
            return "The academic year at JABU typically runs from September to July, with two semesters. Please check the university website for the latest calendar. " + first_paragraph
            
        elif "contact" in message_lower:
            return "You can contact JABU through email at info@jabu.edu.ng or call the university at the numbers listed on the official website."
            
        else:
            # Generic response
            return "Thank you for your question. " + first_paragraph + " For more detailed information, please visit the official JABU website or contact the appropriate department directly."
    
    async def _get_student(self, student_id):
        """
        Helper method to get student information by ID
        
        Args:
            student_id: The student ID to look up
            
        Returns:
            StudentProfile: The student profile or None if not found
        """
        if not student_id:
            return None
            
        try:
            # Use sync_to_async to safely query Django ORM from async context
            @sync_to_async
            def fetch_student():
                return StudentProfile.objects.get(student_id=student_id)
            
            return await fetch_student()
        except Exception as e:
            logger.warning(f"Student with ID {student_id} not found: {str(e)}")
            return None
    
    async def _save_chat_log(self, student, user_message, ai_response, conversation_id):
        """
        Helper method to save chat log to database
        
        Args:
            student: The student profile
            user_message: The original user message
            ai_response: The generated AI response
            conversation_id: The conversation ID
            
        Returns:
            ChatLog: The created chat log or None if there was an error
        """
        if not student:
            return None
            
        try:
            # Use sync_to_async to safely call Django ORM from async context
            @sync_to_async
            def create_chat_log():
                return ChatLog.objects.create(
                    student=student,
                    user_message=user_message,
                    ai_response=ai_response,
                    conversation_id=conversation_id
                )
            
            chat_log = await create_chat_log()
            logger.info(f"Saved chat log for student {student.student_id}, conversation {conversation_id}")
            return chat_log
        except Exception as e:
            logger.error(f"Failed to save chat log: {str(e)}")
            return None
