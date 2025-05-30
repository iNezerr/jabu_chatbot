# JABU Academic Chatbot

An AI-powered academic assistant developed for Joseph Ayo Babalola University (JABU) to provide students with information about programs, admissions, and other academic matters.

## Project Overview

The JABU Chatbot helps students access university information through a conversational interface powered by AI. The system utilizes web crawlers to build and maintain a knowledge base, enabling accurate and contextually relevant responses to student inquiries.

## Table of Contents

- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Variables](#environment-variables)
- [API Documentation](#api-documentation)
  - [Authentication](#authentication)
  - [Users](#users)
  - [Chat](#chat)
  - [Knowledge Base Management](#knowledge-base-management)
- [Backend Architecture](#backend-architecture)
- [Frontend Integration Guide](#frontend-integration-guide)
- [Development Guide](#development-guide)
- [Testing](#testing)
- [Deployment](#deployment)
- [License](#license)

## Technology Stack

- **Backend**: Django 5.2 + Django REST Framework
- **Database**: PostgreSQL
- **AI/ML**: Groq API (LLM integration)
- **Web Scraping**: httpx and BeautifulSoup4
- **Authentication**: JWT (JSON Web Tokens) via SimpleJWT
- **API Documentation**: drf-spectacular for OpenAPI/Swagger

## Project Structure

The project is organized into several Django apps:

```
jabu_chatbot/
├── academic_chatbot/   # Main project settings and configuration
├── chat/               # Chat interaction and AI integration
├── crawler/            # Web scraping and knowledge base management
├── users/              # User authentication and profile management
├── core/               # Shared utilities and base models
└── frontend/           # (Optional) Basic frontend templates for testing
```

### Key Components

- **academic_chatbot**: Core project configuration, settings, main URL routing
- **users**: Student profile management, authentication and authorization
- **chat**: Chat interaction handling, AI integration with Groq API, message processing
- **crawler**: Web scraping, knowledge base population, search functionality
- **core**: Base models and utilities shared across the application

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Git

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/jabu_chatbot.git
   cd jabu_chatbot
   ```
2. Create and activate a virtual environment:

   ```bash
   python -m venv .jac
   # On Windows
   .jac\Scripts\activate 
   # On macOS/Linux
   source .jac/bin/activate
   ```
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```
4. Set up the database:

   ```bash
   python manage.py migrate
   ```
5. Create a superuser:

   ```bash
   python manage.py createsuperuser
   ```
6. Run the development server:

   ```bash
   python manage.py runserver
   ```

### Environment Variables

Create a `.env` file in the project root with the following variables:

```
DATABASE_URL=postgres://username:password@localhost:5432/jabu_chatbot
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama3-70b-8192
SECRET_KEY=your_django_secret_key
DEBUG=True
```

## API Documentation

Once the server is running, you can access the interactive API documentation at:

- http://localhost:8000/api/docs/
- http://localhost:8000/api/schema/ (raw OpenAPI schema)

### Authentication

JWT authentication is implemented. All API endpoints (except authentication endpoints) require a valid token.

- **Obtain Token**: `POST /api/token/`

  ```json
  {
    "username": "your_username",
    "password": "your_password"
  }
  ```

  Response:

  ```json
  {
    "access": "access_token_here",
    "refresh": "refresh_token_here"
  }
  ```
- **Refresh Token**: `POST /api/token/refresh/`

  ```json
  {
    "refresh": "your_refresh_token"
  }
  ```

For API requests, include the token in the Authorization header:

```
Authorization: Bearer your_access_token
```

### Users

- **Get Current User Profile**: `GET /api/my-profile/`

  - Returns the profile of the authenticated user
- **Update User Profile**: `PUT /api/my-profile/update/`

  ```json
  {
    "name": "Student Name",
    "email": "student@example.com",
    "program": "Computer Science",
    "year_of_study": 2,
    "gpa": 3.5,
    "student_id": "CS12345",
    "bio": "A brief bio"
  }
  ```
- **Create User Profile**: `POST /api/profiles/` (Admin only)
- **List All Profiles**: `GET /api/profiles/` (Admin only)

### Chat

- **Send Message**: `POST /api/chat/`

  ```json
  {
    "message": "What programs does JABU offer?",
    "student_id": "CS12345",  // Optional
    "conversation_id": "uuid"  // Optional, for continuing conversations
  }
  ```

  Response:

  ```json
  {
    "status": "success",
    "data": {
      "response": "JABU offers various undergraduate and postgraduate programs...",
      "conversation_id": "conversation_uuid",
      "sources": [
        {
          "title": "Undergraduate Programs",
          "url": "https://jabu.edu.ng/academics/programmes/undergraduate-programmes/",
          "relevance": 0.85
        }
      ]
    }
  }
  ```
- **Submit Feedback**: `POST /api/feedback/`

  ```json
  {
    "chat_log": 123,  // Chat log ID
    "rating": 4,      // 1-5 rating
    "comment": "Very helpful response!"
  }
  ```

### Knowledge Base Management

- **Refresh Knowledge Base**: `POST /api/refresh-knowledgebase/` (Admin only)

  ```json
  {
    "url": "https://jabu.edu.ng/academics/",  // Single URL (optional)
    "urls": ["https://jabu.edu.ng/admissions/"],  // Multiple URLs (optional)
    "use_config": true,  // Use URLs from config.py (optional)
    "delay": 1  // Delay between requests in seconds (optional)
  }
  ```
- **Search Knowledge Base**: `GET /api/search/?q=admission+requirements&limit=5`

  - Query parameter `q`: Search query
  - Query parameter `limit`: Maximum number of results (optional)

## Backend Architecture

### Data Models

- **StudentProfile**:

  - User (OneToOne to Django User)
  - Name, Email, Program, Year of study, GPA
  - Student ID, Bio, Date joined, Last updated
- **ChatLog**:

  - Student (ForeignKey to StudentProfile)
  - User message, AI response
  - Timestamp, Conversation ID
- **Feedback**:

  - Chat log (ForeignKey to ChatLog)
  - Rating (1-5), Comment
  - Submission timestamp
- **KnowledgeBase**:

  - Title, Content, Tags (array)
  - Source URL
  - Created/Updated timestamps
  - Verification flag

### Key Services

- **ChatService**: Handles message processing, AI integration, and response generation
- **Crawler**: Web scraping and content extraction
- **Search**: Knowledge base search with relevance scoring

## Frontend Integration Guide

### Authentication Flow

1. **Login**: Send credentials to `/api/token/` to obtain JWT tokens
2. **Store Tokens**: Save the returned tokens securely (e.g., HTTP-only cookies or localStorage)
3. **Use Tokens**: Include the access token in the Authorization header for all API requests
4. **Token Refresh**: When the access token expires, use the refresh token to get a new one from `/api/token/refresh/`

### API Integration

#### Chat Implementation

1. Implement a chat interface that sends user messages to `/api/chat/`
2. Store and pass the conversation_id with each message to maintain conversation context
3. Display the AI's response from the response data
4. Optionally show sources and allow feedback collection

#### User Profile Management

1. Fetch the user's profile from `/api/my-profile/` upon authentication
2. Allow users to update their profile information via `/api/my-profile/update/`
3. Display relevant student information to personalize the experience

#### Knowledge Base Search

1. Implement a search interface that queries `/api/search/?q=search_term`
2. Display search results with titles, content previews, and relevance scores
3. Allow users to follow source URLs for more information

### Required API Headers

For all authenticated requests:

```
Content-Type: application/json
Authorization: Bearer your_access_token
```

For CSRF-protected requests (when using session authentication):

```
X-CSRFToken: your_csrf_token
```

## Development Guide

### Adding New Knowledge Sources

1. Add new URLs to `crawler/config.py` in the `URLS_TO_SCRAPE` list
2. Run the crawler via management command:
   ```bash
   python manage.py crawl_urls --use-config
   ```
3. Alternatively, use the admin API endpoint to trigger crawling

### Extending the AI Model

1. Update the system prompt in `chat/services.py` to adjust AI behavior
2. Modify the `generate_response` method to add new context or features
3. Update the response processing logic as needed

### Custom Search Implementation

1. Modify `crawler/search.py` to adjust search algorithms and ranking
2. Update the search query building in `search_knowledge_base` function
3. Adjust the content extraction in `get_relevant_content` function

## Testing

Run the test scripts to verify functionality:

```bash
# Test chat functionality
python test_chat.py

# Test crawler functionality
python test_crawler.py

# Test API endpoints
python test_api.py

# Run all Django tests
python manage.py test
```

## Deployment

### Production Settings

1. Update `.env` with production settings:

   ```
   DEBUG=False
   SECRET_KEY=secure_production_key
   ALLOWED_HOSTS=your-domain.com
   ```
2. Set up a production database
3. Configure static file serving
4. Use a WSGI server (e.g., Gunicorn, uWSGI)
5. Set up a reverse proxy (e.g., Nginx)

### Scaling Considerations

- Implement Redis for caching and job queuing (with Celery)
- Add database connection pooling
- Consider horizontal scaling for crawler tasks
- Set up scheduled tasks for knowledge base updates

## License

[MIT License](LICENSE)

---
