"""
Batch crawler that can process multiple URLs
"""
import os
import django
import time
from crawler.config import URLS_TO_SCRAPE, CRAWL_DELAY

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academic_chatbot.settings')
django.setup()

from crawler.utils import crawl_and_store
from crawler.models import KnowledgeBase

def crawl_all_urls():
    """
    Crawl all URLs defined in the config
    
    Returns:
        dict: Stats about the crawl operation
    """
    success_count = 0
    failed_urls = []
    
    print(f"Starting batch crawl of {len(URLS_TO_SCRAPE)} URLs...")
    
    for i, url in enumerate(URLS_TO_SCRAPE, 1):
        print(f"[{i}/{len(URLS_TO_SCRAPE)}] Crawling {url}...")
        
        try:
            result = crawl_and_store(url, KnowledgeBase)
            
            if result:
                print(f"✅ Success: {url}")
                print(f"  - Title: {result.title}")
                print(f"  - Tags: {result.tags}")
                print(f"  - Content length: {len(result.content)} characters")
                success_count += 1
            else:
                print(f"❌ Failed: {url}")
                failed_urls.append(url)
                
        except Exception as e:
            print(f"❌ Error crawling {url}: {str(e)}")
            failed_urls.append(url)
        
        # Add delay between requests
        if i < len(URLS_TO_SCRAPE):
            time.sleep(CRAWL_DELAY)
    
    stats = {
        "total": len(URLS_TO_SCRAPE),
        "success": success_count,
        "failed": len(failed_urls),
        "failed_urls": failed_urls
    }
    
    print("\nCrawl Summary:")
    print(f"- Total URLs: {stats['total']}")
    print(f"- Successfully crawled: {stats['success']}")
    print(f"- Failed: {stats['failed']}")
    
    if failed_urls:
        print("\nFailed URLs:")
        for url in failed_urls:
            print(f"- {url}")
    
    return stats

if __name__ == "__main__":
    crawl_all_urls()
