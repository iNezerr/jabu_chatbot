from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from .models import KnowledgeBase
from .utils import crawl_and_store
from .config import URLS_TO_SCRAPE
from .search import search_knowledge_base, get_relevant_content
import time

# Create your views here.

@api_view(['POST'])
@permission_classes([IsAdminUser])
def refresh_knowledgebase(request):
    """
    Admin-only endpoint to trigger crawling and update the knowledge base
    
    POST Data:
        - url: Single URL to crawl (optional)
        - urls: List of URLs to crawl (optional)
        - use_config: Boolean, if true, uses URLs from config (optional)
        - delay: Delay between requests in seconds (optional, defaults to 1)
    """
    # Get parameters from request
    url = request.data.get('url')
    urls = request.data.get('urls', [])
    use_config = request.data.get('use_config', False)
    delay = int(request.data.get('delay', 1))
    
    # Process the URLs to crawl
    urls_to_crawl = []
    
    if url:
        urls_to_crawl.append(url)
    
    if urls and isinstance(urls, list):
        urls_to_crawl.extend(urls)
    
    if use_config:
        urls_to_crawl.extend(URLS_TO_SCRAPE)
    
    # Remove duplicates while preserving order
    urls_to_crawl = list(dict.fromkeys(urls_to_crawl))
    
    if not urls_to_crawl:
        return Response({
            'status': 'error',
            'message': 'No URLs to crawl. Provide "url", "urls" or set "use_config" to true.'
        }, status=400)
    
    # Results tracking
    results = []
    success_count = 0
    failed_urls = []
    
    # Crawl each URL
    for i, current_url in enumerate(urls_to_crawl):
        # Crawl and store in KnowledgeBase
        result = crawl_and_store(current_url, KnowledgeBase)
        
        if result:
            success_count += 1
            results.append({
                'id': result.id,
                'url': current_url,
                'title': result.title,
                'tags': result.tags,
                'status': 'success'
            })
        else:
            failed_urls.append(current_url)
            results.append({
                'url': current_url,
                'status': 'failed'
            })
        
        # Add delay between requests if not the last URL
        if i < len(urls_to_crawl) - 1 and delay > 0:
            time.sleep(delay)
    
    # Return results
    return Response({
        'status': 'completed',
        'message': f'Crawled {len(urls_to_crawl)} URLs. Success: {success_count}, Failed: {len(failed_urls)}',
        'data': {
            'total': len(urls_to_crawl),
            'success_count': success_count,
            'failed_count': len(failed_urls),
            'failed_urls': failed_urls,
            'results': results
        }
    }, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_kb(request):
    """
    Search the knowledge base for relevant information
    
    GET Parameters:
        - q: Search query (required)
        - limit: Maximum number of results (optional, default: 10)
    """
    query = request.query_params.get('q')
    limit = int(request.query_params.get('limit', 10))
    
    if not query:
        return Response({
            'status': 'error',
            'message': 'Search query (q) is required'
        }, status=400)
    
    # Search the knowledge base
    results = search_knowledge_base(query, limit=limit)
    
    # Format the response
    formatted_results = []
    for entry, score in results:
        # Format the content preview
        content_preview = entry.content[:300] + '...' if len(entry.content) > 300 else entry.content
        
        formatted_results.append({
            'id': entry.id,
            'title': entry.title,
            'content_preview': content_preview,
            'tags': entry.tags,
            'source_url': entry.source_url,
            'relevance_score': score,
            'last_updated': entry.last_updated
        })
    
    return Response({
        'status': 'success',
        'query': query,
        'count': len(formatted_results),
        'results': formatted_results
    }, status=200)
