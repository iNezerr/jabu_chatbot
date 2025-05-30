"""
Knowledge Base search utilities
"""
import os
import django
from django.db.models import Q
import re
from collections import Counter

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academic_chatbot.settings')
django.setup()

from crawler.models import KnowledgeBase

def preprocess_query(query):
    """
    Clean and extract meaningful keywords from the query
    
    Args:
        query (str): User's search query
    
    Returns:
        list: List of keywords
    """
    # Convert to lowercase and remove punctuation
    query = re.sub(r'[^\w\s]', ' ', query.lower())
    
    # Split into words
    words = query.split()
    
    # Remove very short words and common stop words
    stop_words = {'and', 'the', 'is', 'in', 'at', 'of', 'for', 'a', 'an', 'to', 'with', 'on', 'by'}
    words = [word for word in words if word not in stop_words and len(word) > 2]
    
    return words

def search_knowledge_base(query, limit=10):
    """
    Search the knowledge base for relevant information
    
    Args:
        query (str): User's search query
        limit (int): Max number of results to return
    
    Returns:
        list: List of relevant knowledge base entries
    """
    # Process the query into keywords
    keywords = preprocess_query(query)
    
    if not keywords:
        return []
    
    # Build the query filters
    filter_conditions = Q()
    
    # Search in title, content and tags
    for keyword in keywords:
        filter_conditions |= Q(title__icontains=keyword) 
        filter_conditions |= Q(content__icontains=keyword)
        filter_conditions |= Q(tags__contains=[keyword])
    
    # Get matching entries
    results = KnowledgeBase.objects.filter(filter_conditions).distinct()
    
    # Score and rank results
    scored_results = []
    for entry in results:
        score = 0
        
        # Count keyword occurrences
        for keyword in keywords:
            # Title match (higher weight)
            if keyword in entry.title.lower():
                score += 10
                
            # Tag match (high weight)
            if any(keyword in tag.lower() for tag in entry.tags):
                score += 5
                
            # Content match
            content_matches = len(re.findall(r'\b' + keyword + r'\b', entry.content.lower()))
            score += content_matches
        
        scored_results.append((entry, score))
    
    # Sort by score (descending) and take top results
    scored_results.sort(key=lambda x: x[1], reverse=True)
    
    # Return the top N results
    return [(entry, score) for entry, score in scored_results[:limit]]

def get_relevant_content(query):
    """
    Get relevant content for an AI response
    
    Args:
        query (str): User's query
    
    Returns:
        str: Formatted content for context injection into AI
    """
    results = search_knowledge_base(query, limit=3)
    
    if not results:
        return None
    
    context_parts = []
    
    for entry, score in results:
        # Extract a relevant snippet from content
        content_preview = entry.content[:300] + '...' if len(entry.content) > 300 else entry.content
        
        context_parts.append(
            f"Source: {entry.title}\n"
            f"URL: {entry.source_url}\n"
            f"Content: {content_preview}\n"
        )
    
    return "\n---\n".join(context_parts)

if __name__ == "__main__":
    # Example usage
    query = "admission requirements for computer science"
    results = search_knowledge_base(query)
    
    print(f"Search results for: '{query}'")
    print("=" * 50)
    
    if results:
        for idx, (entry, score) in enumerate(results, 1):
            print(f"{idx}. {entry.title} (Relevance: {score})")
            print(f"   URL: {entry.source_url}")
            print(f"   Tags: {', '.join(entry.tags)}")
            content_preview = entry.content[:150] + '...' if len(entry.content) > 150 else entry.content
            print(f"   Preview: {content_preview}")
            print()
    else:
        print("No results found.")
