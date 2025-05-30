"""
Utility to search the knowledge base
"""
import os
import django
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academic_chatbot.settings')
django.setup()

from crawler.models import KnowledgeBase
from django.db.models import Q

def main():
    if len(sys.argv) < 2:
        print("Usage: python search_kb.py <search_query>")
        return
    
    query = ' '.join(sys.argv[1:])
    print(f"Searching for: {query}")
    
    # Search in title, content, or tags
    results = KnowledgeBase.objects.filter(
        Q(title__icontains=query) | 
        Q(content__icontains=query) |
        Q(tags__contains=[query])
    )
    
    if results:
        print(f"Found {results.count()} results:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.title}")
            print(f"   URL: {result.source_url}")
            print(f"   Tags: {', '.join(result.tags)}")
            # Print a preview of the content
            content_preview = result.content[:150] + '...' if len(result.content) > 150 else result.content
            print(f"   Content preview: {content_preview}")
    else:
        print("No results found.")

if __name__ == "__main__":
    main()
