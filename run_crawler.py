"""
Script to run the batch crawler from the command line
"""
import os
import django
import sys

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academic_chatbot.settings')
django.setup()

# Import after Django is set up
from crawler.batch_crawler import crawl_all_urls

if __name__ == "__main__":
    print("Starting JABU Academic Chatbot Crawler")
    print("======================================")
    
    try:
        stats = crawl_all_urls()
        
        if stats["failed"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
