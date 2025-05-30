"""
Test script for crawler functionality
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academic_chatbot.settings')
django.setup()

from crawler.utils import crawl_and_store
from crawler.models import KnowledgeBase

def main():
    # JABU's admissions page URL
    url = "https://jabu.edu.ng/academics/programmes/undergraduate-programmes/"
    
    print(f"Crawling {url}...")
    result = crawl_and_store(url, KnowledgeBase)
    
    if result:
        print(f"Successfully crawled and stored data for {url}")
        print(f"Title: {result.title}")
        print(f"Tags: {result.tags}")
        print(f"Content length: {len(result.content)} characters")
    else:
        print(f"Failed to crawl {url}")

if __name__ == "__main__":
    main()
